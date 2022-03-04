from airflow import DAG
from airflow.models import DagRun, Variable
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor
from sqlalchemy_utils.types.enriched_datetime.pendulum_date import pendulum


def print_results(ti):
    print(ti.xcom_pull(key='result', task_ids=['query_the_table']))


def get_dag_end_time(dt):
    dags = DagRun.find("dag_database_update_1")
    for i in range(len(dags) - 1, -1, -1):
        if dags[i].external_trigger:
            return dags[i].execution_date
    return None


def define_dag_for_result_processing(parent_dag_name, child_dag_name):
    with DAG(dag_id='{0}.{1}'.format(parent_dag_name, child_dag_name), schedule_interval=None,
             start_date=pendulum.parse("2020-01-01T00:00:00")) as dag:
        waitForProcessToFinish = ExternalTaskSensor(
            task_id='wait_for_process_to_finish',
            poke_interval=5,
            external_dag_id='dag_database_update_1',
            execution_date_fn=get_dag_end_time,
            mode='reschedule'
        )

        printResult = PythonOperator(
            task_id='print_results',
            python_callable=print_results
        )
        removeFile = BashOperator(
            task_id='remove_file',
            bash_command='rm {{var.value.get("file_path")}}'
        )
        createFile = BashOperator(
            task_id='create_result_file',
            bash_command=
            "touch {{var.values.get('result_file_path', /Users/dklishch/airflow/external/) + finished_ + ts_nodash}}"
        )

        waitForProcessToFinish >> printResult >> removeFile >> createFile

        return dag
