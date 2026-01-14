from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime

def get_tables():
    hook = PostgresHook(postgres_conn_id="postgres_om")

    sql = """
    SELECT table_schema, table_name
    FROM information_schema.tables
    WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
    ORDER BY table_schema, table_name;
    """

    tables = hook.get_records(sql)
    for t in tables:
        print(t)

with DAG(
    dag_id="extract_postgres_tables",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False
) as dag:

    extract_tables = PythonOperator(
        task_id="get_tables",
        python_callable=get_tables
    )
