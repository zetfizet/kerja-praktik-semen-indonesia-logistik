from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime

with DAG(
    dag_id="etl_driver_kpi",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["driver", "kpi"]
) as dag:

    transform = PostgresOperator(
        task_id="transform_driver_kpi",
        postgres_conn_id="postgres_default",
        sql="""
        SELECT 1;
        """
    )
