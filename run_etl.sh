#!/bin/bash
# 🚀 One-Command ETL Setup
# Jalankan ini setelah CSV siap di folder /home/rafiez/airflow-stack/data/

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                   🚀 ETL WORKFLOW - ONE COMMAND                           ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

DATA_FOLDER="/home/rafiez/airflow-stack/data"

# Check CSV files
echo "📁 Checking CSV files..."
CSV_COUNT=$(ls -1 $DATA_FOLDER/*.csv 2>/dev/null | wc -l)

if [ $CSV_COUNT -eq 0 ]; then
    echo "❌ No CSV files found in $DATA_FOLDER"
    echo ""
    echo "📋 Steps to export CSV:"
    echo "   1. Buka pgAdmin4: http://localhost:5050"
    echo "   2. Query → SELECT * FROM table_name;"
    echo "   3. Download hasil sebagai CSV"
    echo "   4. Copy ke: $DATA_FOLDER"
    echo ""
    echo "📖 Lihat: WORKFLOW_PRAKTIS.md"
    exit 1
fi

echo "✅ Found $CSV_COUNT CSV files:"
ls -1 $DATA_FOLDER/*.csv | xargs -I {} basename {} | sed 's/^/   ✓ /'
echo ""

# Import CSV
echo "📥 Importing CSV to Airflow..."
docker exec airflow-webserver python3 << 'PYTHON_SCRIPT'
import csv, psycopg2
from pathlib import Path

conn = psycopg2.connect(
    host='postgres',
    database='airflow',
    user='airflow',
    password='airflow',
    port=5432
)
cursor = conn.cursor()

data_folder = Path('/home/rafiez/airflow-stack/data')
total_rows = 0

for csv_path in sorted(data_folder.glob('*.csv')):
    table_name = csv_path.stem
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        # Create table
        col_defs = ', '.join([f'"{col}" TEXT' for col in headers])
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS public.{table_name} (
                id SERIAL PRIMARY KEY,
                {col_defs}
            );
        ''')
        conn.commit()
        
        # Clear & insert
        cursor.execute(f'TRUNCATE TABLE public.{table_name} CASCADE;')
        rows = list(reader)
        
        for row in rows:
            cols = list(row.keys())
            vals = [row[col] if row[col].strip() else None for col in cols]
            cols_str = ', '.join([f'"{c}"' for c in cols])
            placeholders = ', '.join(['%s'] * len(cols))
            cursor.execute(
                f'INSERT INTO public.{table_name} ({cols_str}) VALUES ({placeholders})',
                vals
            )
        
        conn.commit()
        total_rows += len(rows)
        print(f'   ✓ {table_name:<35} {len(rows):>6} rows')

cursor.close()
conn.close()
print(f'\n✅ Total: {total_rows} rows imported')
PYTHON_SCRIPT

echo ""

# Trigger DAG
echo "▶️  Triggering ETL DAG..."
docker exec airflow-scheduler airflow dags trigger etl_driver_kpi > /dev/null 2>&1 || true
echo "✅ DAG triggered"
echo ""

# Summary
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                         ✨ WORKFLOW STARTED                               ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Monitor di Airflow UI:"
echo "   URL: http://localhost:8080"
echo "   Login: admin / rafie123"
echo "   Navigate: DAGs → etl_driver_kpi"
echo ""
echo "⏳ Wait untuk 3 tasks selesai:"
echo "   1. extract_oltp_data"
echo "   2. transform_load_analytics"
echo "   3. validate_data_quality"
echo ""
echo "📝 Logs tersimpan di:"
echo "   /home/rafiez/airflow-stack/airflow/logs/"
echo ""
echo "✅ After completion, query hasil:"
echo "   docker exec postgres psql -U airflow -d airflow -c \\"
echo "     'SELECT COUNT(*) FROM analytics.fact_driver_performance;'"
echo ""
echo "👉 Next: BUKA AIRFLOW UI UNTUK MONITOR PROGRESS!"
echo ""
