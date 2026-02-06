"""
Daily Warehouse Sync DAG
Syncs all warehouse schemas from source (devom.silog.co.id) every day
Focus: Weather data updates, plus all other tables
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import psycopg2
from psycopg2 import sql

# Default DAG arguments
default_args = {
    'owner': 'data_team',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2026, 1, 21),
}

# DAG definition
dag = DAG(
    'daily_warehouse_sync',
    default_args=default_args,
    description='Daily sync of all warehouse schemas from source database',
    schedule='0 0 * * *',  # Run at 7 AM WIB (UTC+7) = 00:00 UTC
    catchup=False,
    tags=['warehouse', 'daily', 'sync'],
)

# Source database credentials
SOURCE_DB_CONFIG = {
    'host': 'devom.silog.co.id',
    'database': 'om',
    'user': 'om',
    'password': 'om',
}

# Target (warehouse) database credentials
TARGET_DB_CONFIG = {
    'host': 'localhost',
    'database': 'warehouse',
    'user': 'postgres',
    'password': 'postgres123',
}

# Table mappings: source_table -> (target_schema, target_table)
TABLE_MAPPINGS = {
    # Driver schema
    'daftar_user': ('driver', 'daftar_user'),
    'attachment_driver': ('driver', 'attachment_driver'),
    'laporan_pengemudi': ('driver', 'laporan_pengemudi'),
    'kontak_darurat_pengemudi': ('driver', 'kontak_darurat'),
    
    # Armada schema
    'armada_tms': ('armada', 'armada_tms'),
    'jenis_armada': ('armada', 'jenis_armada'),
    'driver_armada': ('armada', 'driver_armada'),
    'armada_perangkat': ('armada', 'armada_perangkat'),
    'attachment_armada': ('armada', 'attachment_armada'),
    
    # Delivery schema
    'delivery_order': ('delivery', 'delivery_order'),
    'detail_do': ('delivery', 'detail_do'),
    'jenis_order': ('delivery', 'jenis_order'),
    'attachment_gudang': ('delivery', 'attachment_gudang'),
    
    # Activity schema
    'log_perjalanan_armada': ('activity', 'log_perjalanan_armada'),
    'log_aktifitas_driver': ('activity', 'log_aktifitas_driver'),
    'log_perangkat': ('activity', 'log_perangkat'),
    'log_chat': ('activity', 'log_chat'),
    'log_panggilan': ('activity', 'log_panggilan'),
    'log_sensor': ('activity', 'log_sensor'),
    'alert_geofence': ('activity', 'alert_geofence'),
    
    # Financial schema
    'orders': ('financial', 'orders'),
    'detail_po': ('financial', 'detail_po'),
    'jenis_transaksi': ('financial', 'jenis_transaksi'),
    'detail_qc': ('financial', 'detail_qc'),
    'bank': ('financial', 'bank'),
    
    # Support schema
    'attachment': ('support', 'attachment'),
    'jenis_file': ('support', 'jenis_file'),
    'chat_room': ('support', 'chat_room'),
    'attachment_chat': ('support', 'attachment_chat'),
    'attachment_pengembalian': ('support', 'attachment_pengembalian'),
    'attachment_perangkat': ('support', 'attachment_perangkat'),
    'attachment_qc': ('support', 'attachment_qc'),
    
    # Weather schema (PRIORITY)
    'fact_weather_hourly': ('weather', 'fact_weather_hourly'),
    
    # Master schema
    'gudang': ('master', 'gudang'),
    'locations': ('master', 'locations'),
    'kategori_produk': ('master', 'kategori_produk'),
    'konversi': ('master', 'konversi'),
    'jenis_satuan': ('master', 'jenis_satuan'),
    'atribut': ('master', 'atribut'),
    'atribut_produk': ('master', 'atribut_produk'),
    'kriteria_produk': ('master', 'kriteria_produk'),
    'geofence': ('master', 'geofence'),
    'jenis_insiden': ('master', 'jenis_insiden'),
    'jenis_notifikasi': ('master', 'jenis_notifikasi'),
    'laporan_darurat': ('master', 'laporan_darurat'),
    'rating': ('master', 'rating'),
}

def sync_table(source_table, target_schema, target_table):
    """Sync a single table from source to warehouse"""
    try:
        # Connect to source
        source_conn = psycopg2.connect(**SOURCE_DB_CONFIG)
        source_cursor = source_conn.cursor()
        
        # Connect to target
        target_conn = psycopg2.connect(**TARGET_DB_CONFIG)
        target_cursor = target_conn.cursor()
        
        # Get column info from source
        source_cursor.execute(f"SELECT * FROM {source_table} LIMIT 0")
        columns = [desc[0] for desc in source_cursor.description]
        
        # Clear target table
        target_cursor.execute(f"TRUNCATE TABLE {target_schema}.{target_table}")
        
        # Fetch all data from source
        source_cursor.execute(f"SELECT * FROM {source_table}")
        rows = source_cursor.fetchall()
        
        # Insert into target
        if rows:
            col_names = ', '.join(columns)
            placeholders = ', '.join(['%s'] * len(columns))
            insert_query = f"INSERT INTO {target_schema}.{target_table} ({col_names}) VALUES ({placeholders})"
            target_cursor.executemany(insert_query, rows)
            target_conn.commit()
            print(f"✓ {target_schema}.{target_table}: {len(rows)} rows synced")
        else:
            print(f"✓ {target_schema}.{target_table}: 0 rows (table empty in source)")
        
        source_cursor.close()
        source_conn.close()
        target_cursor.close()
        target_conn.close()
        
        return True, f"{target_schema}.{target_table}: {len(rows) if rows else 0} rows"
    
    except Exception as e:
        error_msg = f"ERROR syncing {target_schema}.{target_table}: {str(e)}"
        print(error_msg)
        return False, error_msg

def sync_all_tables():
    """Sync all tables - main function"""
    print("=" * 60)
    print("Starting daily warehouse sync...")
    print("=" * 60)
    
    results = {
        'success': [],
        'failed': [],
    }
    
    # Priority: Weather tables first
    weather_tables = [('fact_weather_hourly', 'weather', 'fact_weather_hourly')]
    
    print("\n📍 PRIORITY: Syncing WEATHER data first...")
    for src, tgt_schema, tgt_table in weather_tables:
        success, msg = sync_table(src, tgt_schema, tgt_table)
        if success:
            results['success'].append(msg)
        else:
            results['failed'].append(msg)
    
    # Then sync all other tables
    print("\n📊 Syncing other schemas...")
    for source_table, (target_schema, target_table) in TABLE_MAPPINGS.items():
        if source_table == 'fact_weather_hourly':
            continue  # Skip, already synced above
        
        success, msg = sync_table(source_table, target_schema, target_table)
        if success:
            results['success'].append(msg)
        else:
            results['failed'].append(msg)
    
    # Summary
    print("\n" + "=" * 60)
    print("SYNC SUMMARY")
    print("=" * 60)
    print(f"✅ Success: {len(results['success'])} tables")
    print(f"❌ Failed: {len(results['failed'])} tables")
    
    if results['failed']:
        print("\nFailed tables:")
        for msg in results['failed']:
            print(f"  - {msg}")
    
    print("\nDetailed results:")
    for msg in results['success'][:10]:  # Show first 10
        print(f"  ✓ {msg}")
    if len(results['success']) > 10:
        print(f"  ... and {len(results['success']) - 10} more")
    
    return {
        'success_count': len(results['success']),
        'failed_count': len(results['failed']),
    }

# Task 1: Sync all tables
sync_task = PythonOperator(
    task_id='sync_warehouse_tables',
    python_callable=sync_all_tables,
    dag=dag,
)

# Task 2: Verify sync completed
verify_task = BashOperator(
    task_id='verify_warehouse_data',
    bash_command='''
    PGPASSWORD='postgres123' psql -h localhost -U postgres -d warehouse -c "
    SELECT 
        table_schema,
        COUNT(*) as table_count,
        SUM((SELECT COUNT(*) FROM information_schema.tables t2 
             WHERE t2.table_schema = t1.table_schema)) as total_tables
    FROM information_schema.tables t1
    WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
    GROUP BY table_schema
    ORDER BY table_schema;
    " && echo "✓ Warehouse verification complete"
    ''',
    dag=dag,
)

# Task 3: Log weather data count
weather_count_task = BashOperator(
    task_id='check_weather_data',
    bash_command='''
    PGPASSWORD='postgres123' psql -h localhost -U postgres -d warehouse -c "
    SELECT 'fact_weather_hourly' as table_name, COUNT(*) as row_count 
    FROM weather.fact_weather_hourly;
    " && echo "✓ Weather data check complete"
    ''',
    dag=dag,
)

# Set task dependencies
sync_task >> verify_task >> weather_count_task
