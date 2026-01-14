#!/usr/bin/env python3
"""
Script untuk import CSV files ke PostgreSQL Airflow database

Cara pakai:
1. Export tabel dari database aplikasi sebagai CSV
2. Simpan di folder: /home/rafiez/airflow-stack/data/
3. Run: python3 import_csv.py

File CSV harus bernama:
- jenis_armada.csv
- driver_armada.csv
- rating.csv
- orders.csv
"""

import csv
import psycopg2
from pathlib import Path
from datetime import datetime
import os

# Auto-detect if running inside Docker or host
# Inside Docker: use 'postgres' hostname
# On host machine: use 'localhost'
IN_DOCKER = os.path.exists("/.dockerenv")

TARGET_DB = {
    "host": "postgres" if IN_DOCKER else "localhost",
    "database": "airflow",
    "user": "airflow",
    "password": "airflow",
    "port": 5432
}

DATA_FOLDER = Path("/home/rafiez/airflow-stack/data")

# Mapping CSV file ke table dan kolom
CSV_MAPPINGS = {
    "driver_armada.csv": {
        "table": "driver_armada",
        "skip_rows": 0
    },
    "rating.csv": {
        "table": "rating",
        "skip_rows": 0
    },
    "rekening_driver.csv": {
        "table": "rekening_driver",
        "skip_rows": 0
    },
    "perangkat_gps_driver.csv": {
        "table": "perangkat_gps_driver",
        "skip_rows": 0
    },
    "delivery_order.csv": {
        "table": "delivery_order",
        "skip_rows": 0
    },
    "log_perjalanan_armada.csv": {
        "table": "log_perjalanan_armada",
        "skip_rows": 0
    },
    "log_aktifitas_driver.csv": {
        "table": "log_aktifitas_driver",
        "skip_rows": 0
    }
}

def connect_db():
    try:
        conn = psycopg2.connect(
            host=TARGET_DB["host"],
            database=TARGET_DB["database"],
            user=TARGET_DB["user"],
            password=TARGET_DB["password"],
            port=TARGET_DB["port"]
        )
        return conn
    except psycopg2.Error as e:
        print(f"❌ Gagal connect: {e}")
        return None

def create_table_from_csv(conn, table_name, csv_file, headers):
    """Create table jika belum ada dengan struktur dari CSV headers"""
    cursor = conn.cursor()
    
    # Mapping tipe data (default semua VARCHAR)
    col_defs = [f'"{col}" VARCHAR' for col in headers]
    col_defs.append('"id" SERIAL PRIMARY KEY')
    
    create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(col_defs)})"
    
    try:
        cursor.execute(create_sql)
        conn.commit()
        print(f"✅ Table {table_name} created/verified")
        cursor.close()
        return True
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        cursor.close()
        return False

def import_csv(conn, table_name, csv_file):
    """Import CSV file ke table"""
    cursor = conn.cursor()
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if not headers:
                print(f"❌ CSV kosong atau tidak valid: {csv_file}")
                return 0
            
            # Create table
            if not create_table_from_csv(conn, table_name, csv_file, headers):
                return 0
            
            # Clear table
            cursor.execute(f"TRUNCATE TABLE {table_name} CASCADE")
            conn.commit()
            
            # Insert data
            rows_count = 0
            for row in reader:
                cols = list(row.keys())
                vals = [row[col] if row[col] else None for col in cols]
                
                cols_str = ', '.join([f'"{c}"' for c in cols])
                placeholders = ', '.join(['%s'] * len(cols))
                
                insert_sql = f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders})"
                cursor.execute(insert_sql, vals)
                rows_count += 1
            
            conn.commit()
            print(f"✅ Imported {rows_count} rows to {table_name}")
            cursor.close()
            return rows_count
            
    except Exception as e:
        print(f"❌ Error importing {csv_file}: {e}")
        conn.rollback()
        cursor.close()
        return 0

def main():
    print("=" * 60)
    print("📊 CSV IMPORT TOOL")
    print("=" * 60)
    print(f"Data folder: {DATA_FOLDER}\n")
    
    # Check if data folder exists
    if not DATA_FOLDER.exists():
        print(f"📁 Creating data folder: {DATA_FOLDER}")
        DATA_FOLDER.mkdir(parents=True, exist_ok=True)
        print(f"⚠️  Place your CSV files in: {DATA_FOLDER}\n")
        print("Expected files:")
        for csv_file in CSV_MAPPINGS.keys():
            print(f"  - {csv_file}")
        return
    
    # Check for CSV files
    csv_files = list(DATA_FOLDER.glob("*.csv"))
    if not csv_files:
        print(f"❌ Tidak ada CSV files di {DATA_FOLDER}")
        print(f"\nSilakan place CSV files di: {DATA_FOLDER}")
        return
    
    print(f"📁 Found {len(csv_files)} CSV files\n")
    
    # Connect to database
    print("🔗 Connecting to database...")
    conn = connect_db()
    if not conn:
        return
    print("✅ Connected\n")
    
    # Import setiap CSV
    total_imported = 0
    for csv_file in sorted(csv_files):
        table_name = csv_file.stem  # filename without extension
        
        print(f"\n{'='*60}")
        print(f"Importing: {csv_file.name} → {table_name}")
        print('='*60)
        
        count = import_csv(conn, table_name, csv_file)
        total_imported += count
    
    # Summary
    print(f"\n{'='*60}")
    print(f"✅ IMPORT COMPLETE!")
    print(f"{'='*60}")
    print(f"Total rows imported: {total_imported}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n💡 Tip: Sekarang Anda bisa jalankan ETL DAG di Airflow!")
    
    conn.close()

if __name__ == "__main__":
    main()
