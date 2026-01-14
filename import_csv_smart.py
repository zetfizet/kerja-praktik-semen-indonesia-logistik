#!/usr/bin/env python3
"""
📊 CSV IMPORT TOOL - Smart Version
Auto-detect path dan import CSV ke Airflow PostgreSQL
"""

import csv
import psycopg2
from pathlib import Path
import sys
import logging
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    "host": "postgres",
    "database": "airflow",
    "user": "airflow",
    "password": "airflow",
    "port": 5432
}

# Auto-detect data folder
POSSIBLE_PATHS = [
    Path("/home/rafiez/airflow-stack/data"),  # Host machine
    Path("/home/airflow/data"),                # Docker airflow user
    Path("/opt/airflow/dags/../data"),         # Docker airflow home
    Path(os.getcwd()) / "data",                # Current directory
]

DATA_FOLDER = None
for path in POSSIBLE_PATHS:
    if path.exists():
        DATA_FOLDER = path
        break

if DATA_FOLDER is None:
    # Use first preferred path
    DATA_FOLDER = POSSIBLE_PATHS[0]

def connect_db():
    """Connect to PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info(f"✅ Connected to PostgreSQL")
        return conn
    except Exception as e:
        logger.error(f"❌ Connection failed: {str(e)}")
        return None

def import_csv_file(conn, csv_path, table_name):
    """Import CSV file to PostgreSQL table"""
    try:
        cursor = conn.cursor()
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if not headers:
                logger.error(f"❌ CSV empty or invalid: {csv_path}")
                return 0
            
            # Sanitize column names (remove special chars)
            clean_headers = []
            for h in headers:
                # Replace spaces and special chars with underscore
                clean = ''.join(c if c.isalnum() or c == '_' else '_' for c in h)
                clean_headers.append(clean)
            
            # Create table if not exists
            col_defs = ', '.join([f'"{col}" TEXT' for col in clean_headers])
            create_table_sql = f"""
                CREATE TABLE IF NOT EXISTS public.{table_name} (
                    id SERIAL PRIMARY KEY,
                    {col_defs},
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """
            
            cursor.execute(create_table_sql)
            conn.commit()
            logger.info(f"   📋 Table {table_name} verified")
            
            # Clear existing data
            cursor.execute(f"TRUNCATE TABLE public.{table_name} CASCADE;")
            conn.commit()
            
            # Re-read file for data import
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                rows_inserted = 0
                for row in reader:
                    # Map original headers to clean headers
                    clean_row = {}
                    for i, orig_header in enumerate(headers):
                        clean_row[clean_headers[i]] = row[orig_header]
                    
                    cols = list(clean_row.keys())
                    vals = [clean_row[col] if str(clean_row[col]).strip() else None for col in cols]
                    
                    cols_str = ', '.join([f'"{c}"' for c in cols])
                    placeholders = ', '.join(['%s'] * len(cols))
                    
                    insert_sql = f"INSERT INTO public.{table_name} ({cols_str}) VALUES ({placeholders})"
                    cursor.execute(insert_sql, vals)
                    
                    rows_inserted += 1
                    
                    # Commit every 100 rows
                    if rows_inserted % 100 == 0:
                        conn.commit()
            
            conn.commit()
            logger.info(f"✅ {table_name:<30} {rows_inserted:>6} rows imported")
            cursor.close()
            return rows_inserted
            
    except Exception as e:
        logger.error(f"❌ Error importing {csv_path}: {str(e)}")
        conn.rollback()
        return 0

def main():
    print("\n" + "=" * 80)
    print("📊 CSV IMPORT TOOL")
    print("=" * 80)
    
    print(f"\n📁 Data folder: {DATA_FOLDER}")
    
    # Check if folder exists
    if not DATA_FOLDER.exists():
        print(f"⚠️  Folder does not exist, creating...")
        try:
            DATA_FOLDER.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            logger.error(f"❌ Cannot create folder: {DATA_FOLDER}")
            print("\n💡 Try running from Docker container:")
            print("   docker exec airflow-webserver python3 /home/airflow/import_csv_simple.py")
            return False
    
    # Find CSV files
    csv_files = list(DATA_FOLDER.glob("*.csv"))
    
    if not csv_files:
        print(f"\n⚠️  No CSV files found in {DATA_FOLDER}")
        print("\n📋 Steps:")
        print("   1. Buka pgAdmin4: http://localhost:5050")
        print("   2. Tools → Query Tool")
        print("   3. For each table, run: SELECT * FROM table_name;")
        print("   4. Download hasil sebagai CSV")
        print(f"   5. Simpan di folder: {DATA_FOLDER}")
        print("\n📝 Expected CSV files:")
        expected = [
            'driver_armada.csv',
            'rating.csv',
            'delivery_order.csv',
            'perangkat_gps_driver.csv',
            'rekening_driver.csv'
        ]
        for f in expected:
            print(f"   • {f}")
        return False
    
    print(f"\n📁 Found {len(csv_files)} CSV file(s):")
    for f in csv_files:
        size = f.stat().st_size / 1024  # KB
        print(f"   • {f.name:<35} ({size:.2f} KB)")
    
    # Connect to database
    print("\n🔌 Connecting to PostgreSQL...")
    conn = connect_db()
    
    if not conn:
        return False
    
    # Import each CSV
    print("\n" + "=" * 80)
    print("📥 IMPORTING DATA")
    print("=" * 80 + "\n")
    
    total_rows = 0
    for csv_path in sorted(csv_files):
        table_name = csv_path.stem  # filename without .csv
        rows = import_csv_file(conn, csv_path, table_name)
        total_rows += rows
    
    conn.close()
    
    # Summary
    print("\n" + "=" * 80)
    print(f"✨ Import Complete! Total: {total_rows} rows")
    print("=" * 80)
    
    print("\n🎉 Next steps:")
    print("   1. Buka Airflow UI: http://localhost:8080")
    print("   2. Navigasi ke: DAGs → etl_driver_kpi")
    print("   3. Klik tombol ▶️ untuk trigger DAG")
    print("   4. Monitor execution di Graph View")
    print("\n📊 Verify data di database:")
    print("   docker exec postgres psql -U airflow -d airflow -c \\")
    print(f"   \"SELECT COUNT(*) FROM driver_armada;\"")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
