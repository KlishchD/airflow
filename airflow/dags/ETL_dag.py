from airflow.decorators import task, dag
from airflow.models import Variable
from sqlalchemy_utils.types.enriched_datetime.pendulum_date import pendulum
from urllib.request import urlopen

file_path = '/usr/local/airflow/tmp.txt'
url = Variable.get(key='data_url')


@dag(schedule_interval=None, start_date=pendulum.parse('2020:01:01'))
def etl():
    @task
    def load(link, path):
        with open(path, 'wb') as destination:
            for line in urlopen(link):
                destination.write(line)

    @task
    def count_accidents(path):
        counts = {}
        with open(path, 'rb') as file:
            file.readline()
            for line in file:
                try:
                    year = str(line).split(',')[1]
                except ValueError:
                    continue
                counts[year] = counts.get(year, 0) + 1
        return counts

    @task
    def print_result(counts: dict):
        for year, count in counts.items():
            print(year, ":", count)

    print_result(load(url, file_path) >> count_accidents(file_path))


dag = etl()
