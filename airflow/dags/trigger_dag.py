from airflow import DAG

from airflow.operators.subdag import SubDagOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.operators.python import PythonOperator

from airflow.models import Variable
from airflow.sensors.filesystem import FileSensor

from sqlalchemy_utils.types.enriched_datetime.pendulum_date import pendulum

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# from SmartFileSensor import SmartFileSensor
from result_procesing_dag import define_dag_for_result_processing


def slack_notify():
    client = WebClient(token=Variable.get(key='slack_token'))
    send_message_slack(client, "Hello from your app! :tada:")


def send_message_slack(client, message):
    try:
        client.chat_postMessage(channel="general", text=message)
    except SlackApiError as e:
        print(e)


with DAG(dag_id='trigger', schedule_interval=None, start_date=pendulum.parse("2020-01-01T00:00:00")) as dag:
    wait_for_file = FileSensor(
        task_id='wait_for_file',
        filepath='{{var.value.get("filepath", "/Users/dklishch/airflow/trigger.txt")}}',
        poke_interval=5,
        mode='reschedule'
    )
    run_db_update = TriggerDagRunOperator(
        task_id='run_db_update',
        trigger_dag_id='dag_database_update_1'
    )

    process_results = SubDagOperator(
        task_id='process_results',
        subdag=define_dag_for_result_processing('trigger', 'process_results')
    )

    notify = PythonOperator(
        task_id='notify',
        python_callable=slack_notify
    )

    wait_for_file >> run_db_update >> process_results >> notify
