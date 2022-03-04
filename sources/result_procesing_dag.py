from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor
from sqlalchemy_utils.types.enriched_datetime.pendulum_date import pendulum


def define_dag_for_result_processing(parent_dag_name, child_dag_name):
    with DAG(dag_id='{0}.{1}'.format(parent_dag_name, child_dag_name), schedule_interval=None,
             start_date=pendulum.now()) as dag:
        wait_for_process_to_finish = ExternalTaskSensor(
            task_id='wait_for_process_to_finish',
            external_dag_id='dag_database_update_1',
            execution_date_fn=lambda x: pendulum.now(),
            poke_interval=5,
            mode='reschedule'
        )

        print_result = PythonOperator(
            task_id='print_result',
            python_callable=lambda ti: print(ti.xcom_pull(key='result', task_ids=['query_the_table']))
        )

        remove_file = BashOperator(
            task_id='remove_file',
            bash_command='rm {{var.value.get("file_path")}}'
        )

        create_file = BashOperator(
            task_id='create_result_file',
            bash_command='touch {{var.value.get("result_file_path", "/usr/local/airflow/external/")}}finished_{{ts}}'
        )

        wait_for_process_to_finish >> print_result >> remove_file >> create_file

        return dag
