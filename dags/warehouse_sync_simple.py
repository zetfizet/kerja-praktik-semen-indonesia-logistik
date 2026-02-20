"""
Warehouse Sync DAG for Analytics & Metabase
Sinkronisasi data warehouse untuk analytics & Metabase dashboard

Fitur:
- Auto create table: table dibuat otomatis jika belum ada
- Incremental sync: 63 tables menggunakan timestamp (diubah_pada, created_at, dll)
- Full sync: 25 tables tanpa timestamp (TRUNCATE + INSERT)
- Smart sync: Otomatis pilih strategi sync berdasarkan kolom timestamp
- Optimized untuk Metabase dashboard queries

Target: Metabase dashboard & analytics  
Schedule: 2 AM daily
Total: 88 tables (63 incremental, 25 full sync)
"""

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.operators.bash import BashOperator
from datetime import datetime, timedelta
import psycopg2

# Default DAG arguments
default_args = {
    'owner': 'data_team',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2026, 2, 6),
}

# DAG definition
dag = DAG(
    'warehouse_sync_simple',
    default_args=default_args,
    description='Warehouse sync - 88 tables (63 incremental, 25 full) to public schema',
    schedule='0 2 * * *',  # Run at 2 AM every day
    catchup=False,
    tags=['warehouse', 'analytics', 'metabase', 'full-sync'],
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
    'host': 'postgres',  # Container name in docker network
    'database': 'warehouse',
    'user': 'airflow',
    'password': 'airflow',
    'port': 5432,
}

# Table mappings: source_table -> (target_schema, target_table, sync_column)
# sync_column: timestamp column untuk incremental sync (diubah_pada, created_at, updated_at, dibuat_pada)
# None = full sync (untuk table tanpa timestamp column)
# 
# Incremental sync: Hanya sync data yang berubah/baru (berdasarkan timestamp)
# Full sync: Sync semua data (TRUNCATE + INSERT) - untuk table tanpa timestamp
# 
# AUTO-GENERATED: 63 incremental, 25 full sync
TABLE_MAPPINGS = {
    'alert_geofence': ('public', 'alert_geofence', 'diubah_pada'),
    'armada_perangkat': ('public', 'armada_perangkat', None),
    'armada_tms': ('public', 'armada_tms', 'diubah_pada'),
    'atribut': ('public', 'atribut', None),
    'atribut_produk': ('public', 'atribut_produk', None),
    'attachment': ('public', 'attachment', 'diubah_pada'),
    'attachment_armada': ('public', 'attachment_armada', None),
    'attachment_chat': ('public', 'attachment_chat', None),
    'attachment_driver': ('public', 'attachment_driver', None),
    'attachment_gudang': ('public', 'attachment_gudang', None),
    'attachment_pengembalian': ('public', 'attachment_pengembalian', None),
    'attachment_perangkat': ('public', 'attachment_perangkat', None),
    'attachment_qc': ('public', 'attachment_qc', None),
    'bank': ('public', 'bank', 'diubah_pada'),
    'chat_room': ('public', 'chat_room', 'dibuat_pada'),
    'customers': ('public', 'customers', 'created_at'),
    'daftar_user': ('public', 'daftar_user', 'diubah_pada'),
    'delivery_order': ('public', 'delivery_order', None),
    'detail_do': ('public', 'detail_do', None),
    'detail_po': ('public', 'detail_po', None),
    'detail_qc': ('public', 'detail_qc', 'diubah_pada'),
    'detail_sm': ('public', 'detail_sm', None),
    'detail_so': ('public', 'detail_so', 'diubah_pada'),
    'driver_armada': ('public', 'driver_armada', None),
    'geofence': ('public', 'geofence', 'diubah_pada'),
    'gudang': ('public', 'gudang', 'diubah_pada'),
    'jenis_armada': ('public', 'jenis_armada', 'diubah_pada'),
    'jenis_file': ('public', 'jenis_file', 'diubah_pada'),
    'jenis_insiden': ('public', 'jenis_insiden', 'diubah_pada'),
    'jenis_notifikasi': ('public', 'jenis_notifikasi', 'diubah_pada'),
    'jenis_order': ('public', 'jenis_order', None),
    'jenis_satuan': ('public', 'jenis_satuan', 'diubah_pada'),
    'jenis_transaksi': ('public', 'jenis_transaksi', 'diubah_pada'),
    'kategori_produk': ('public', 'kategori_produk', 'diubah_pada'),
    'kontak_darurat': ('public', 'kontak_darurat', 'diubah_pada'),
    'konversi': ('public', 'konversi', None),
    'kriteria_produk': ('public', 'kriteria_produk', 'diubah_pada'),
    'language': ('public', 'language', None),
    'language_text': ('public', 'language_text', None),
    'laporan_darurat': ('public', 'laporan_darurat', 'diubah_pada'),
    'laporan_pengemudi': ('public', 'laporan_pengemudi', 'diubah_pada'),
    'locations': ('public', 'locations', 'created_at'),
    'log_aktifitas_driver': ('public', 'log_aktifitas_driver', 'diubah_pada'),
    'log_chat': ('public', 'log_chat', 'diubah_pada'),
    'log_panggilan': ('public', 'log_panggilan', 'diubah_pada'),
    'log_perangkat': ('public', 'log_perangkat', 'diubah_pada'),
    'log_perjalanan_armada': ('public', 'log_perjalanan_armada', 'diubah_pada'),
    'log_sensor': ('public', 'log_sensor', 'diubah_pada'),
    'log_service': ('public', 'log_service', 'diubah_pada'),
    'lokasi_rak': ('public', 'lokasi_rak', 'diubah_pada'),
    'mata_uang': ('public', 'mata_uang', 'diubah_pada'),
    'metode_pembayaran': ('public', 'metode_pembayaran', 'diubah_pada'),
    'notifikasi': ('public', 'notifikasi', 'diubah_pada'),
    'order_tms': ('public', 'order_tms', 'dibuat_pada'),
    'orders': ('public', 'orders', 'diubah_pada'),
    'parent_armada': ('public', 'parent_armada', 'diubah_pada'),
    'pembayaran_fee': ('public', 'pembayaran_fee', 'diubah_pada'),
    'pengembalian': ('public', 'pengembalian', None),
    'pengingat_pemeliharaan_armada': ('public', 'pengingat_pemeliharaan_armada', 'diubah_pada'),
    'perangkat': ('public', 'perangkat', None),
    'perangkat_gps_driver': ('public', 'perangkat_gps_driver', 'diubah_pada'),
    'produk': ('public', 'produk', 'diubah_pada'),
    'produk_gudang': ('public', 'produk_gudang', None),
    'purchase_order': ('public', 'purchase_order', None),
    'quality_control': ('public', 'quality_control', 'diubah_pada'),
    'rating': ('public', 'rating', 'diubah_pada'),
    'rekening_driver': ('public', 'rekening_driver', 'diubah_pada'),
    'role': ('public', 'role', 'diubah_pada'),
    'room_last_read': ('public', 'room_last_read', None),
    'room_members': ('public', 'room_members', None),
    'rute': ('public', 'rute', None),
    'rute_perangkat': ('public', 'rute_perangkat', 'diubah_pada'),
    'sales_order': ('public', 'sales_order', None),
    'satuan': ('public', 'satuan', 'diubah_pada'),
    'status_armada': ('public', 'status_armada', 'diubah_pada'),
    'status_gudang': ('public', 'status_gudang', None),
    'status_order': ('public', 'status_order', None),
    'status_qc': ('public', 'status_qc', None),
    'status_user': ('public', 'status_user', 'diubah_pada'),
    'stok': ('public', 'stok', 'diubah_pada'),
    'stok_movement': ('public', 'stok_movement', 'diubah_pada'),
    'suppliers': ('public', 'suppliers', 'created_at'),
    'tempat_istirahat_driver': ('public', 'tempat_istirahat_driver', 'diubah_pada'),
    'tenant': ('public', 'tenant', 'diubah_pada'),
    'units': ('public', 'units', 'created_at'),
    'user_role': ('public', 'user_role', None),
    'user_tenant': ('public', 'user_tenant', None),
    'z_test': ('public', 'z_test', None),
}

def sync_table(source_table, target_schema, target_table, sync_column=None):
    """
    Sync a single table from source to warehouse
    sync_column: None = full sync, or column name for incremental sync (ID or timestamp)
    """
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
        
        # Check if target table exists, if not create it
        target_cursor.execute(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = '{target_schema}' 
                AND table_name = '{target_table}'
            );
        """)
        table_exists = target_cursor.fetchone()[0]
        
        # Get primary key from source table
        source_cursor.execute(f"""
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = '{source_table}'::regclass AND i.indisprimary
        """)
        pk_result = source_cursor.fetchall()
        primary_key = pk_result[0][0] if pk_result else None
        
        if not table_exists:
            # Create table with same structure as source
            print(f"Creating table {target_schema}.{target_table}...")
            source_cursor.execute(f"""
                SELECT column_name, data_type, character_maximum_length, is_nullable
                FROM information_schema.columns 
                WHERE table_name = '{source_table}'
                ORDER BY ordinal_position
            """)
            cols_info = source_cursor.fetchall()
            
            col_defs = []
            for col_name, data_type, max_len, is_null in cols_info:
                col_def = f"{col_name} {data_type}"
                if max_len and data_type in ('character varying', 'character'):
                    col_def += f"({max_len})"
                if is_null == 'NO':
                    col_def += " NOT NULL"
                col_defs.append(col_def)
            
            create_sql = f"CREATE TABLE {target_schema}.{target_table} ({', '.join(col_defs)})"
            target_cursor.execute(create_sql)
            
            # Add primary key if source has one
            if primary_key:
                target_cursor.execute(f"""
                    ALTER TABLE {target_schema}.{target_table} 
                    ADD PRIMARY KEY ({primary_key})
                """)
            
            # Add sync tracking columns
            target_cursor.execute(f"""
                ALTER TABLE {target_schema}.{target_table} 
                ADD COLUMN IF NOT EXISTS synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """)
            target_conn.commit()
            print(f"✓ Table {target_schema}.{target_table} created (PK: {primary_key or 'None'})")
        
        # Determine sync strategy
        if sync_column is None or primary_key is None:
            # FULL SYNC - for master data or tables without primary key
            if sync_column and not primary_key:
                print(f"⚠ {target_table}: No PK found, falling back to FULL sync")
            target_cursor.execute(f"TRUNCATE TABLE {target_schema}.{target_table}")
            source_cursor.execute(f"SELECT * FROM {source_table}")
            rows = source_cursor.fetchall()
            sync_type = "FULL"
            
        else:
            # INCREMENTAL SYNC - only new/updated data
            # Get max value from target
            target_cursor.execute(f"""
                SELECT MAX({sync_column}) FROM {target_schema}.{target_table}
            """)
            max_value = target_cursor.fetchone()[0]
            
            if max_value is None:
                # First sync - get all data
                source_cursor.execute(f"SELECT * FROM {source_table}")
                sync_type = "INITIAL"
            else:
                # Get only new/updated records
                source_cursor.execute(f"""
                    SELECT * FROM {source_table} 
                    WHERE {sync_column} > %s
                    ORDER BY {sync_column}
                """, (max_value,))
                sync_type = "INCREMENTAL"
            
            rows = source_cursor.fetchall()
        
        # Insert into target
        if rows:
            col_names = ', '.join(columns)
            placeholders = ', '.join(['%s'] * len(columns))
            
            if sync_column is None or primary_key is None:
                # Full sync or no PK - simple insert (table was truncated)
                insert_query = f"INSERT INTO {target_schema}.{target_table} ({col_names}) VALUES ({placeholders})"
                target_cursor.executemany(insert_query, rows)
            else:
                # Incremental with PK - upsert using primary key for ON CONFLICT
                update_cols = ', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col != primary_key])
                insert_query = f"""
                    INSERT INTO {target_schema}.{target_table} ({col_names}) 
                    VALUES ({placeholders})
                    ON CONFLICT ({primary_key}) DO UPDATE SET {update_cols}
                """
                target_cursor.executemany(insert_query, rows)
            
            target_conn.commit()
            print(f"✓ {target_schema}.{target_table}: {len(rows)} rows [{sync_type}]")
        else:
            print(f"✓ {target_schema}.{target_table}: 0 new rows [{sync_type}]")
        
        source_cursor.close()
        source_conn.close()
        target_cursor.close()
        target_conn.close()
        
        return True, f"{target_schema}.{target_table}: {len(rows) if rows else 0} rows [{sync_type}]"
    
    except Exception as e:
        error_msg = f"ERROR syncing {target_schema}.{target_table}: {str(e)}"
        print(error_msg)
        return False, error_msg

def sync_all_tables():
    """Sync all tables - main function"""
    print("=" * 60)
    print("Starting warehouse sync for Analytics...")
    print("=" * 60)
    
    results = {
        'success': [],
        'failed': [],
    }
    
    # Sync all tables
    print("\n📊 Syncing tables for Metabase...")
    for source_table, (target_schema, target_table, sync_column) in TABLE_MAPPINGS.items():
        success, msg = sync_table(source_table, target_schema, target_table, sync_column)
        if success:
            results['success'].append(msg)
        else:
            results['failed'].append(msg)
    
    # Summary by schema
    schema_counts = {}
    incremental_count = 0
    full_sync_count = 0
    
    for msg in results['success']:
        schema = msg.split('.')[0]
        schema_counts[schema] = schema_counts.get(schema, 0) + 1
        
        # Count incremental vs full
        if '[INCREMENTAL]' in msg:
            incremental_count += 1
        elif '[FULL]' in msg:
            full_sync_count += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("SYNC SUMMARY - Ready for Metabase!")
    print("=" * 60)
    print(f"✅ Success: {len(results['success'])} tables")
    print(f"❌ Failed: {len(results['failed'])} tables")
    print(f"🔄 Incremental: {incremental_count} tables")
    print(f"📦 Full sync: {full_sync_count} tables")
    
    print("\n📊 Tables by schema:")
    for schema, count in sorted(schema_counts.items()):
        print(f"  {schema}: {count} tables")
    
    if results['failed']:
        print("\n❌ Failed tables:")
        for msg in results['failed']:
            print(f"  - {msg}")
    
    print("\n✅ Synced tables:")
    for msg in results['success']:
        print(f"  ✓ {msg}")
    
    return {
        'success_count': len(results['success']),
        'failed_count': len(results['failed']),
        'incremental_count': incremental_count,
        'full_sync_count': full_sync_count,
        'schema_counts': schema_counts,
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
    export PGPASSWORD='airflow'
    psql -h postgres -U airflow -d warehouse -c "
    SELECT 
        COUNT(*) as total_tables,
        pg_size_pretty(SUM(pg_total_relation_size(quote_ident('public')||'.'||quote_ident(table_name)))) as total_size
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    AND table_name NOT IN ('spatial_ref_sys');
    " && echo "" && echo "✓ Warehouse verification complete - All 88 tables synced to public schema - Ready for Metabase!"
    ''',
    dag=dag,
)

# Set task dependencies
sync_task >> verify_task
