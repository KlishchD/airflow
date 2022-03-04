from typing import Any
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.models import BaseOperator


class PostgresSQLCountRows(BaseOperator):

    def __init__(self, table_name: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.table_name = table_name

    def execute(self, context: Any):
        return PostgresHook().get_first(sql=f"SELECT COUNT(*) FROM {self.table_name}")
