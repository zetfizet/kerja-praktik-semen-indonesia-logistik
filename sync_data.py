#!/usr/bin/env python3
"""
Script untuk sync data dari database aplikasi (devom.silog.co.id) 
ke database Airflow (localhost) untuk ETL processing

RUN: python3 sync_data.py
"""

import psycopg2
from psycopg2 import sql
import sys
from datetime import datetime

# Source database (aplikasi)
SOURCE_DB = {
    "host": "devom.silog.co.id",
    "database": "devom.silog.co.id",
    "user": "om",
    "password": "om",
    "port": 5432
}

# Target database (Airflow local)
TARGET_DB = {
    "host": "127.0.0.1",  # localhost
    "database": "airflow",
    "user": "airflow",
    "password": "airflow",
    "port": 5432
}

# Mapping tabel yang akan di-sync (EDIT SESUAI TABEL ANDA)
# Format: "source_table": "target_table"
TABLE_MAPPINGS = {
    "jenis_armada": "jenis_armada",
    "driver_armada": "driver_armada",
    "rating": "rating",
    "delivery_order": "orders",
}

def connect_db(db_config):
    """Connect ke database"""
    try:
        conn = psycopg2.connect(
            host=db_config["host"],
            database=db_config["database"],
            user=db_config["user"],
            password=db_config["password"],
            port=db_config["port"]
        )
        return conn
    except psycopg2.Error as e:
        print(f"❌ Gagal connect ke {db_config['host']}: {e}")
        return None

def create_table_in_target(source_conn, target_conn, source_table, target_table):
    """Create tabel di target database dengan struktur yang sama dari source"""
    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()
    
    try:
        # Get struktur tabel dari source
        source_cursor.execute(f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = '{source_table}'
            ORDER BY ordinal_position
        """)
        columns = source_cursor.fetchall()
        
        if not columns:
            print(f"⚠️  Tabel {source_table} tidak ditemukan atau kosong")
            return False
        
        # Build CREATE TABLE statement
        col_definitions = []
        for col_name, data_type, is_nullable, col_default in columns:
            col_def = f'"{col_name}" {data_type}'
            if col_default:
                col_def += f" DEFAULT {col_default}"
            if is_nullable == "NO":
                col_def += " NOT NULL"
            col_definitions.append(col_def)
        
        create_sql = f"""
            CREATE TABLE IF NOT EXISTS {target_table} (
                {', '.join(col_definitions)}
            )
        """
        
        print(f"📋 Creating table: {target_table}")
        target_cursor.execute(create_sql)
        target_conn.commit()
        print(f"✅ Table {target_table} created successfully")
        
        source_cursor.close()
        target_cursor.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        target_conn.rollback()
        source_cursor.close()
        target_cursor.close()
        return False

def copy_data(source_conn, target_conn, source_table, target_table):
    """Copy data dari source ke target"""
    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()
    
    try:
        # Get data dari source
        print(f"📥 Reading data from {source_table}...")
        source_cursor.execute(f"SELECT * FROM {source_table}")
        rows = source_cursor.fetchall()
        
        if not rows:
            print(f"⚠️  {source_table} is empty, skipping...")
            return 0
        
        # Get column names
        source_cursor.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{source_table}'
            ORDER BY ordinal_position
        """)
        columns = [row[0] for row in source_cursor.fetchall()]
        
        # Clear target table
        print(f"🗑️  Clearing {target_table}...")
        target_cursor.execute(f"TRUNCATE TABLE {target_table} CASCADE")
        
        # Insert data ke target
        print(f"📤 Inserting {len(rows)} rows to {target_table}...")
        cols_str = ', '.join([f'"{col}"' for col in columns])
        placeholders = ', '.join(['%s'] * len(columns))
        
        insert_sql = f"INSERT INTO {target_table} ({cols_str}) VALUES ({placeholders})"
        
        for row in rows:
            target_cursor.execute(insert_sql, row)
        
        target_conn.commit()
        print(f"✅ Successfully inserted {len(rows)} rows to {target_table}\n")
        
        source_cursor.close()
        target_cursor.close()
        return len(rows)
        
    except Exception as e:
        print(f"❌ Error copying data: {e}")
        target_conn.rollback()
        source_cursor.close()
        target_cursor.close()
        return 0

def main():
    print("=" * 60)
    print("🔄 DATABASE SYNC TOOL")
    print("=" * 60)
    print(f"Source: {SOURCE_DB['host']} → Target: {TARGET_DB['host']}\n")
    
    # Connect ke source
    print("🔗 Connecting to source database...")
    source_conn = connect_db(SOURCE_DB)
    if not source_conn:
        sys.exit(1)
    print("✅ Connected to source\n")
    
    # Connect ke target
    print("🔗 Connecting to target database...")
    target_conn = connect_db(TARGET_DB)
    if not target_conn:
        source_conn.close()
        sys.exit(1)
    print("✅ Connected to target\n")
    
    # Sync setiap tabel
    total_synced = 0
    for source_table, target_table in TABLE_MAPPINGS.items():
        print(f"\n{'='*60}")
        print(f"Syncing: {source_table} → {target_table}")
        print('='*60)
        
        # Create table if not exists
        if not create_table_in_target(source_conn, target_conn, source_table, target_table):
            print(f"⏭️  Skipping {source_table}\n")
            continue
        
        # Copy data
        count = copy_data(source_conn, target_conn, source_table, target_table)
        total_synced += count
    
    # Summary
    print(f"\n{'='*60}")
    print(f"✅ SYNC COMPLETE!")
    print(f"{'='*60}")
    print(f"Total rows synced: {total_synced}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nData sekarang siap di Airflow analytics schema!")
    
    source_conn.close()
    target_conn.close()

if __name__ == "__main__":
    main()
