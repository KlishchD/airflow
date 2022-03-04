import random

import pendulum
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.dummy import DummyOperator
from datetime import datetime
from datetime import timedelta
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.utils.trigger_rule import TriggerRule
from airflow.providers.postgres.hooks.postgres import PostgresHook

from hooks.PostgresSQLCountRows import PostgresSQLCountRows

default_args = {
    'owner': 'rnd',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

configs = {
    'dag_database_update_1': {
        'schedule_interval': None,
        'start_date': datetime(2022, 2, 21),
        'table_name': 'table_name_1'
    },
    'dag_database_update_2': {
        'schedule_interval': '*/2 * * * *',
        'start_date': datetime(2022, 2, 21),
        'table_name': 'table_name_2'
    },
    'dag_database_update_3': {
        'schedule_interval': '*/3 * * * *',
        'start_date': datetime(2022, 2, 21),
        'table_name': 'table_name_3'
    }
}


def print_logs(dag_id, database):
    print(f"{dag_id} start processing tables in database: {database}")


def check_table_exist(table_name):
    return 'dummy' if PostgresHook().get_records(get_sql_to_check_table_existence(table_name)) else 'create_table'


def query_table(table_name, **context):
    context['ti'].xcom_push(key='report', value=context['run_id'] + ' ended successfully')

    context['ti'].xcom_push(key='run_id', value=context['run_id'])

    hook = PostgresSQLCountRows(task_id='hook', table_name=table_name)
    context['ti'].xcom_push(key='result', value=hook.execute(context))


def get_sql_for_table_creation(table_name):
    return f"CREATE TABLE {table_name}(custom_id integer NOT NULL," \
           f"user_name VARCHAR (50) NOT NULL, timestamp TIMESTAMP NOT NULL);"


def get_sql_for_row_insertion(table_name, custom_id, user_name, time):
    return f'INSERT INTO {table_name} VALUES({custom_id}, \'{user_name}\', CAST(\'{time}\' AS TIMESTAMP))'


def get_sql_to_check_table_existence(table_name):
    return f"SELECT * FROM information_schema.tables WHERE table_name = '{table_name}'"


def build_dag(dag_id, schedule_interval, start_date, table_name):
    with DAG(dag_id=dag_id, schedule_interval=schedule_interval, start_date=start_date) as dag:
        process_start_logging = PythonOperator(
            task_id='proces_start_logging',
            queue='db_update_queue',
            python_callable=print_logs,
            op_kwargs={
                'dag_id': dag_id,
                "database": table_name
            }
        )
        get_current_user_task = BashOperator(
            task_id="get_current_user",
            bash_command='echo "$USER"',
            queue='db_update_queue'
        )

        branch = BranchPythonOperator(
            task_id="branch",
            queue='db_update_queue',
            python_callable=check_table_exist,
            op_args=[table_name]
        )

        dummy_task = DummyOperator(
            task_id="dummy",
            queue='db_update_queue'
        )

        create_table_task = PostgresOperator(
            task_id="create_table",
            sql=get_sql_for_table_creation(table_name),
            queue='db_update_queue'
        )

        insertion_task = PostgresOperator(
            task_id="insert_row",
            sql=get_sql_for_row_insertion(table_name,
                                          random.randint(0, 123456),
                                          '{{ti.xcom_pull(key="return_value", task_ids="get_current_user")}}',
                                          pendulum.now()),
            trigger_rule=TriggerRule.NONE_FAILED,
            queue='db_update_queue'
        )

        querying_task = PythonOperator(
            task_id="query_table",
            python_callable=query_table,
            op_args=[table_name],
            queue='db_update_queue'
        )

        process_start_logging >> get_current_user_task >> branch
        branch >> [dummy_task, create_table_task] >> insertion_task >> querying_task

        return dag


for dag_id, value in configs.items():
    globals()[dag_id] = build_dag(dag_id, **value)
