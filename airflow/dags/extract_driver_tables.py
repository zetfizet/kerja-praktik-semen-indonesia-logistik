from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime
import os

BASE_PATH = "/opt/airflow/data/extract"

def extract_table(table):
    hook = PostgresHook(postgres_conn_id="postgres_om")
    df = hook.get_pandas_df(f"SELECT * FROM {table}")

    os.makedirs(BASE_PATH, exist_ok=True)
    path = f"{BASE_PATH}/{table}.csv"
    df.to_csv(path, index=False)

    print(f"Extracted {table} → {path}")

with DAG(
    dag_id="etl_extract_driver_tables",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False
) as dag:

    extract_driver = PythonOperator(
        task_id="extract_driver_armada",
        python_callable=extract_table,
        op_args=["driver_armada"]
    )

    extract_rating = PythonOperator(
        task_id="extract_rating",
        python_callable=extract_table,
        op_args=["rating"]
    )

    extract_gps = PythonOperator(
        task_id="extract_gps",
        python_callable=extract_table,
        op_args=["perangkat_gps_driver"]
    )

    extract_driver >> extract_rating >> extract_gps
