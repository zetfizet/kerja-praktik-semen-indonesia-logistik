#!/usr/bin/env python3
"""
📊 CSV IMPORT TOOL - Simple Version
Import CSV files directly ke Airflow PostgreSQL

Bisa dijalankan dari:
1. Docker container (recommended)
2. Host machine (jika network configured)
"""

import csv
import psycopg2
from psycopg2.extras import execute_batch
from pathlib import Path
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    "host": "postgres",  # Docker network
    "database": "airflow",
    "user": "airflow",
    "password": "airflow",
    "port": 5432
}

DATA_FOLDER = Path("/home/rafiez/airflow-stack/data")

def connect_db():
    """Connect to PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info(f"✅ Connected to PostgreSQL")
        return conn
    except Exception as e:
        logger.error(f"❌ Connection failed: {str(e)}")
        logger.info("\n💡 Tips:")
        logger.info("   If running from host machine, execute from Docker container:")
        logger.info("   docker exec airflow-webserver python3 /workspace/import_csv.py")
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
            
            # Create table if not exists
            col_defs = ', '.join([f'"{col}" TEXT' for col in headers])
            create_table_sql = f"""
                CREATE TABLE IF NOT EXISTS public.{table_name} (
                    id SERIAL PRIMARY KEY,
                    {col_defs}
                );
            """
            
            cursor.execute(create_table_sql)
            conn.commit()
            logger.info(f"   📋 Table {table_name} verified")
            
            # Clear existing data
            cursor.execute(f"TRUNCATE TABLE public.{table_name} CASCADE;")
            conn.commit()
            
            # Insert data in batches
            rows = list(reader)
            batch_size = 100
            rows_inserted = 0
            
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i+batch_size]
                
                for row in batch:
                    cols = list(row.keys())
                    vals = [row[col] if row[col].strip() else None for col in cols]
                    
                    cols_str = ', '.join([f'"{c}"' for c in cols])
                    placeholders = ', '.join(['%s'] * len(cols))
                    
                    insert_sql = f"INSERT INTO public.{table_name} ({cols_str}) VALUES ({placeholders})"
                    cursor.execute(insert_sql, vals)
                
                rows_inserted = len(rows)
            
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
    
    # Create data folder if not exists
    DATA_FOLDER.mkdir(parents=True, exist_ok=True)
    
    # Find CSV files
    csv_files = list(DATA_FOLDER.glob("*.csv"))
    
    if not csv_files:
        print(f"\n⚠️  No CSV files found in {DATA_FOLDER}")
        print("\n📋 Steps:")
        print("   1. Buka pgAdmin4: http://localhost:5050")
        print("   2. Tools → Query Tool")
        print("   3. For each table, run: SELECT * FROM table_name;")
        print("   4. Download hasil sebagai CSV")
        print("   5. Simpan di folder: /home/rafiez/airflow-stack/data/")
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
        print(f"   • {f.name}")
    
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
    for csv_path in csv_files:
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
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
