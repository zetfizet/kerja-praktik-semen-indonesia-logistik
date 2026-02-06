"""
ETL DAG untuk sync data dari OLTP (devom.silog.co.id) ke Warehouse Database
Mengambil tables yang diperlukan untuk KPI Driver Analytics

Tables yang di-sync:
1. Master Data: driver, armada, driver_armada, perangkat_gps_driver, rekening_driver
2. Operational: delivery_order, rating
3. Logs: log_aktifitas_driver, log_perjalanan_armada
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import logging
import pandas as pd

default_args = {
    'owner': 'airflow',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': days_ago(1),
}

dag = DAG(
    'etl_warehouse_sync',
    default_args=default_args,
    description='Sync data dari OLTP (devom.silog.co.id) ke Warehouse Database',
    schedule_interval='0 2 * * *',  # Jalan setiap hari jam 2 pagi
    catchup=False,
    tags=['warehouse', 'etl', 'kpi-driver'],
)

logger = logging.getLogger(__name__)


def create_warehouse_schema():
    """Create schema dan tables di warehouse database"""
    hook = PostgresHook(postgres_conn_id='warehouse_db')
    
    # Baca SQL file
    with open('/home/rafiez/airflow-stack/sql/03_create_warehouse_schema.sql', 'r') as f:
        sql = f.read()
    
    # Execute
    hook.run(sql)
    logger.info("Warehouse schema created successfully")


def sync_table_from_source(source_conn_id, warehouse_conn_id, schema_name, table_name, 
                           sync_mode='full', incremental_column=None):
    """
    Sync table dari source ke warehouse
    
    Args:
        source_conn_id: Source database connection ID
        warehouse_conn_id: Warehouse database connection ID
        schema_name: Schema name di warehouse (e.g., 'warehouse')
        table_name: Table name yang akan di-sync
        sync_mode: 'full' (full sync) atau 'incremental' (berdasarkan timestamp)
        incremental_column: Column yang digunakan untuk incremental sync (e.g., 'updated_at')
    """
    try:
        source_hook = PostgresHook(postgres_conn_id=source_conn_id)
        warehouse_hook = PostgresHook(postgres_conn_id=warehouse_conn_id)
        
        # Build query
        if sync_mode == 'full':
            query = f"SELECT * FROM public.{table_name}"
        elif sync_mode == 'incremental' and incremental_column:
            # Ambil last sync time dari metadata
            metadata_query = f"""
            SELECT last_sync_time FROM warehouse.sync_metadata 
            WHERE table_name = '{table_name}'
            """
            result = warehouse_hook.get_records(metadata_query)
            last_sync_time = result[0][0] if result else None
            
            if last_sync_time:
                query = f"""
                SELECT * FROM public.{table_name} 
                WHERE {incremental_column} > '{last_sync_time}'
                """
            else:
                query = f"SELECT * FROM public.{table_name}"
        
        # Fetch data dari source
        logger.info(f"Fetching data from source: {table_name}")
        df = pd.read_sql(query, source_hook.get_conn())
        
        if df.empty:
            logger.info(f"No new data for {table_name}")
            return
        
        logger.info(f"Fetched {len(df)} rows from {table_name}")
        
        # Truncate target table (untuk full sync)
        if sync_mode == 'full':
            truncate_sql = f"TRUNCATE TABLE {schema_name}.{table_name} CASCADE"
            warehouse_hook.run(truncate_sql)
            logger.info(f"Truncated {schema_name}.{table_name}")
        
        # Insert ke warehouse
        from sqlalchemy import create_engine, text
        
        warehouse_conn = warehouse_hook.get_conn()
        engine = create_engine(f'postgresql://{warehouse_hook.login}:{warehouse_hook.password}@{warehouse_hook.host}:{warehouse_hook.port}/{warehouse_hook.schema}')
        
        df.to_sql(table_name, engine, schema=schema_name, if_exists='append', index=False)
        logger.info(f"Successfully synced {len(df)} rows to {schema_name}.{table_name}")
        
        # Update metadata
        update_metadata_sql = f"""
        INSERT INTO warehouse.sync_metadata (table_name, last_sync_time, row_count, status)
        VALUES ('{table_name}', NOW(), {len(df)}, 'SUCCESS')
        ON CONFLICT (table_name) DO UPDATE SET
            last_sync_time = NOW(),
            row_count = {len(df)},
            status = 'SUCCESS',
            updated_at = NOW()
        """
        warehouse_hook.run(update_metadata_sql)
        
    except Exception as e:
        logger.error(f"Error syncing {table_name}: {str(e)}")
        # Update metadata dengan error status
        update_metadata_sql = f"""
        INSERT INTO warehouse.sync_metadata (table_name, status, error_message)
        VALUES ('{table_name}', 'FAILED', '{str(e)}')
        ON CONFLICT (table_name) DO UPDATE SET
            status = 'FAILED',
            error_message = '{str(e)}',
            updated_at = NOW()
        """
        warehouse_hook.run(update_metadata_sql)
        raise


def validate_warehouse_data():
    """Validate data di warehouse"""
    hook = PostgresHook(postgres_conn_id='warehouse_db')
    
    validation_query = """
    SELECT 
        table_name,
        (SELECT COUNT(*) FROM warehouse.driver) as driver_count,
        (SELECT COUNT(*) FROM warehouse.armada) as armada_count,
        (SELECT COUNT(*) FROM warehouse.driver_armada) as driver_armada_count,
        (SELECT COUNT(*) FROM warehouse.perangkat_gps_driver) as gps_device_count,
        (SELECT COUNT(*) FROM warehouse.delivery_order) as delivery_order_count,
        (SELECT COUNT(*) FROM warehouse.rating) as rating_count,
        (SELECT COUNT(*) FROM warehouse.log_aktifitas_driver) as activity_log_count,
        (SELECT COUNT(*) FROM warehouse.log_perjalanan_armada) as journey_log_count,
        (SELECT COUNT(*) FROM warehouse.rekening_driver) as rekening_count
    FROM warehouse.sync_metadata
    LIMIT 1
    """
    
    result = hook.get_records(validation_query)
    logger.info(f"Warehouse validation result: {result}")
    
    # Simple validation: ensure at least some data exists
    if result:
        logger.info("Data validation passed")
    else:
        logger.warning("No validation data available")


# ============================================================================
# TASKS
# ============================================================================

# Task 1: Create warehouse schema
create_schema_task = PythonOperator(
    task_id='create_warehouse_schema',
    python_callable=create_warehouse_schema,
    dag=dag,
)

# Task 2-10: Sync master data tables (full sync)
master_tables = [
    'driver',
    'armada',
    'driver_armada',
    'perangkat_gps_driver',
    'rekening_driver',
]

master_tasks = []
for table in master_tables:
    task = PythonOperator(
        task_id=f'sync_master_{table}',
        python_callable=sync_table_from_source,
        op_kwargs={
            'source_conn_id': 'devom_silog_source',
            'warehouse_conn_id': 'warehouse_db',
            'schema_name': 'warehouse',
            'table_name': table,
            'sync_mode': 'full',
        },
        dag=dag,
    )
    master_tasks.append(task)

# Task 11-12: Sync operational tables (full sync)
operational_tables = [
    'delivery_order',
    'rating',
]

operational_tasks = []
for table in operational_tables:
    task = PythonOperator(
        task_id=f'sync_operational_{table}',
        python_callable=sync_table_from_source,
        op_kwargs={
            'source_conn_id': 'devom_silog_source',
            'warehouse_conn_id': 'warehouse_db',
            'schema_name': 'warehouse',
            'table_name': table,
            'sync_mode': 'incremental',
            'incremental_column': 'updated_at',
        },
        dag=dag,
    )
    operational_tasks.append(task)

# Task 13-14: Sync log tables (incremental sync)
log_tables = {
    'log_aktifitas_driver': 'created_at',
    'log_perjalanan_armada': 'created_at',
}

log_tasks = []
for table, incremental_col in log_tables.items():
    task = PythonOperator(
        task_id=f'sync_log_{table}',
        python_callable=sync_table_from_source,
        op_kwargs={
            'source_conn_id': 'devom_silog_source',
            'warehouse_conn_id': 'warehouse_db',
            'schema_name': 'warehouse',
            'table_name': table,
            'sync_mode': 'incremental',
            'incremental_column': incremental_col,
        },
        dag=dag,
    )
    log_tasks.append(task)

# Task 15: Validate data
validate_task = PythonOperator(
    task_id='validate_warehouse_data',
    python_callable=validate_warehouse_data,
    dag=dag,
)

# ============================================================================
# DAG DEPENDENCIES
# ============================================================================

# Schema harus dibuat terlebih dahulu
create_schema_task >> master_tasks >> operational_tasks >> log_tasks >> validate_task
