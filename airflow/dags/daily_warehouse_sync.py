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
    'host': 'postgres',
    'database': 'warehouse',
    'user': 'postgres',
    'password': 'postgres',
    'port': 5432,
}

# Table mappings: source_table -> (target_schema, target_table)
# All tables mapped to 'public' schema (single schema architecture)
TABLE_MAPPINGS = {
    'alert_geofence': ('public', 'alert_geofence'),
    'armada_perangkat': ('public', 'armada_perangkat'),
    'armada_tms': ('public', 'armada_tms'),
    'atribut': ('public', 'atribut'),
    'atribut_produk': ('public', 'atribut_produk'),
    'attachment': ('public', 'attachment'),
    'attachment_armada': ('public', 'attachment_armada'),
    'attachment_chat': ('public', 'attachment_chat'),
    'attachment_driver': ('public', 'attachment_driver'),
    'attachment_gudang': ('public', 'attachment_gudang'),
    'attachment_pengembalian': ('public', 'attachment_pengembalian'),
    'attachment_perangkat': ('public', 'attachment_perangkat'),
    'attachment_qc': ('public', 'attachment_qc'),
    'bank': ('public', 'bank'),
    'chat_room': ('public', 'chat_room'),
    'customers': ('public', 'customers'),
    'daftar_user': ('public', 'daftar_user'),
    'delivery_order': ('public', 'delivery_order'),
    'detail_do': ('public', 'detail_do'),
    'detail_po': ('public', 'detail_po'),
    'detail_qc': ('public', 'detail_qc'),
    'detail_sm': ('public', 'detail_sm'),
    'detail_so': ('public', 'detail_so'),
    'driver_armada': ('public', 'driver_armada'),
    'geofence': ('public', 'geofence'),
    'gudang': ('public', 'gudang'),
    'jenis_armada': ('public', 'jenis_armada'),
    'jenis_file': ('public', 'jenis_file'),
    'jenis_insiden': ('public', 'jenis_insiden'),
    'jenis_notifikasi': ('public', 'jenis_notifikasi'),
    'jenis_order': ('public', 'jenis_order'),
    'jenis_satuan': ('public', 'jenis_satuan'),
    'jenis_transaksi': ('public', 'jenis_transaksi'),
    'kategori_produk': ('public', 'kategori_produk'),
    'kontak_darurat': ('public', 'kontak_darurat'),
    'konversi': ('public', 'konversi'),
    'kriteria_produk': ('public', 'kriteria_produk'),
    'language': ('public', 'language'),
    'language_text': ('public', 'language_text'),
    'laporan_darurat': ('public', 'laporan_darurat'),
    'laporan_pengemudi': ('public', 'laporan_pengemudi'),
    'locations': ('public', 'locations'),
    'log_aktifitas_driver': ('public', 'log_aktifitas_driver'),
    'log_chat': ('public', 'log_chat'),
    'log_panggilan': ('public', 'log_panggilan'),
    'log_perangkat': ('public', 'log_perangkat'),
    'log_perjalanan_armada': ('public', 'log_perjalanan_armada'),
    'log_sensor': ('public', 'log_sensor'),
    'log_service': ('public', 'log_service'),
    'lokasi_rak': ('public', 'lokasi_rak'),
    'mata_uang': ('public', 'mata_uang'),
    'metode_pembayaran': ('public', 'metode_pembayaran'),
    'notifikasi': ('public', 'notifikasi'),
    'order_tms': ('public', 'order_tms'),
    'orders': ('public', 'orders'),
    'parent_armada': ('public', 'parent_armada'),
    'pembayaran_fee': ('public', 'pembayaran_fee'),
    'pengembalian': ('public', 'pengembalian'),
    'pengingat_pemeliharaan_armada': ('public', 'pengingat_pemeliharaan_armada'),
    'perangkat': ('public', 'perangkat'),
    'perangkat_gps_driver': ('public', 'perangkat_gps_driver'),
    'produk': ('public', 'produk'),
    'produk_gudang': ('public', 'produk_gudang'),
    'purchase_order': ('public', 'purchase_order'),
    'quality_control': ('public', 'quality_control'),
    'rating': ('public', 'rating'),
    'rekening_driver': ('public', 'rekening_driver'),
    'role': ('public', 'role'),
    'room_last_read': ('public', 'room_last_read'),
    'room_members': ('public', 'room_members'),
    'rute': ('public', 'rute'),
    'rute_perangkat': ('public', 'rute_perangkat'),
    'sales_order': ('public', 'sales_order'),
    'satuan': ('public', 'satuan'),
    'status_armada': ('public', 'status_armada'),
    'status_gudang': ('public', 'status_gudang'),
    'status_order': ('public', 'status_order'),
    'status_qc': ('public', 'status_qc'),
    'status_user': ('public', 'status_user'),
    'stok': ('public', 'stok'),
    'stok_movement': ('public', 'stok_movement'),
    'suppliers': ('public', 'suppliers'),
    'tempat_istirahat_driver': ('public', 'tempat_istirahat_driver'),
    'tenant': ('public', 'tenant'),
    'units': ('public', 'units'),
    'user_role': ('public', 'user_role'),
    'user_tenant': ('public', 'user_tenant'),
    'weather': ('public', 'weather'),
    'z_test': ('public', 'z_test'),
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
        
        # Fetch all data from source with batch processing
        source_cursor.execute(f"SELECT * FROM {source_table}")
        rows = source_cursor.fetchall()
        
        # Insert into target with batch size for faster insertion
        if rows:
            col_names = ', '.join(columns)
            placeholders = ', '.join(['%s'] * len(columns))
            insert_query = f"INSERT INTO {target_schema}.{target_table} ({col_names}) VALUES ({placeholders})"
            
            # Process in batches of 5000 for faster insertion
            batch_size = 5000
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                target_cursor.executemany(insert_query, batch)
            
            target_conn.commit()
            print(f"✓ {target_schema}.{target_table}: {len(rows)} rows synced")
        else:
            target_conn.commit()
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
    print("Starting daily warehouse sync from DEVOM...")
    print(f"Total tables to sync: {len(TABLE_MAPPINGS)}")
    print("=" * 60)
    
    results = {
        'success': [],
        'failed': [],
    }
    
    # Sync all tables from TABLE_MAPPINGS
    print("\n📦 Syncing all company data from DEVOM...")
    for source_table, (target_schema, target_table) in TABLE_MAPPINGS.items():
        print(f"\n⏳ Syncing {source_table} -> {target_schema}.{target_table}...")
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
    
    print("\nSuccessful syncs (sample):")
    for msg in results['success'][:10]:  # Show first 10
        print(f"  ✓ {msg}")
    if len(results['success']) > 10:
        print(f"  ... and {len(results['success']) - 10} more tables")
    
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
    PGPASSWORD='postgres' psql -h postgres -p 5432 -U postgres -d warehouse -c "
    SELECT 
        tablename as table_name,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
    FROM pg_tables 
    WHERE schemaname = 'public' 
    AND tablename != 'fact_weather_hourly'
    ORDER BY tablename 
    LIMIT 10;
    " && echo "✓ Warehouse verification complete (showing 10 sample tables)"
    ''',
    dag=dag,
)

# Task 3: Log company data count
company_count_task = BashOperator(
    task_id='check_company_data',
    bash_command='''
    PGPASSWORD='postgres' psql -h postgres -p 5432 -U postgres -d warehouse -c "
    SELECT 
        COUNT(*) as total_tables,
        'public' as schema_name
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE';
    " && echo "✓ Company data check complete"
    ''',
    dag=dag,
)

# Set task dependencies
sync_task >> verify_task >> company_count_task
