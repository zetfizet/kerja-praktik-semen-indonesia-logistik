#!/usr/bin/env python3
"""
🚀 COMPLETE ETL WORKFLOW - One Command Solution
Langkah 5-8 terotomasi dalam satu command
"""

import subprocess
import psycopg2
from pathlib import Path
import time
import sys

def print_header(title):
    print("\n" + "=" * 80)
    print(f"🔷 {title}")
    print("=" * 80 + "\n")

def check_csv_files():
    """Check if CSV files exist"""
    print_header("STEP 1: Check CSV Files")
    
    data_folder = Path("/home/rafiez/airflow-stack/data")
    data_folder.mkdir(parents=True, exist_ok=True)
    
    csv_files = list(data_folder.glob("*.csv"))
    
    if not csv_files:
        print("❌ No CSV files found!")
        print(f"\n📋 Expected files in {data_folder}:")
        expected = [
            "driver_armada.csv",
            "rating.csv",
            "delivery_order.csv",
            "perangkat_gps_driver.csv",
            "rekening_driver.csv"
        ]
        for f in expected:
            print(f"   • {f}")
        print("\n📖 Follow WORKFLOW_PRAKTIS.md untuk export dari pgAdmin4")
        return False
    
    print(f"✅ Found {len(csv_files)} CSV file(s):\n")
    for f in csv_files:
        size_kb = f.stat().st_size / 1024
        print(f"   ✓ {f.name:<35} ({size_kb:.2f} KB)")
    
    return True

def import_csv_to_airflow():
    """Import CSV files to Airflow PostgreSQL"""
    print_header("STEP 2: Import CSV to Airflow PostgreSQL")
    
    try:
        conn = psycopg2.connect(
            host="postgres",
            database="airflow",
            user="airflow",
            password="airflow",
            port=5432
        )
        print("✅ Connected to PostgreSQL\n")
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print("   Run from Docker container: docker exec airflow-webserver python3 etl_workflow.py")
        return False
    
    import csv
    data_folder = Path("/home/rafiez/airflow-stack/data")
    csv_files = sorted(data_folder.glob("*.csv"))
    
    cursor = conn.cursor()
    total_rows = 0
    
    for csv_path in csv_files:
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
            
            # Clear existing data
            cursor.execute(f'TRUNCATE TABLE public.{table_name} CASCADE;')
            
            # Insert rows
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
            rows_count = len(rows)
            total_rows += rows_count
            print(f"   ✓ {table_name:<35} {rows_count:>6} rows")
    
    cursor.close()
    conn.close()
    
    print(f"\n✅ Total: {total_rows} rows imported\n")
    return True

def trigger_dag():
    """Trigger ETL DAG"""
    print_header("STEP 3: Trigger ETL DAG")
    
    try:
        result = subprocess.run(
            "docker exec airflow-scheduler airflow dags trigger etl_driver_kpi",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ DAG triggered successfully!\n")
            print("   Execution ID:", result.stdout.strip().split('\n')[0] if result.stdout else "N/A")
            return True
        else:
            print(f"⚠️  Response: {result.stdout if result.stdout else result.stderr}")
            return True  # Still continue even if trigger unclear
            
    except Exception as e:
        print(f"⚠️  {str(e)}")
        return True

def monitor_dag():
    """Show monitoring instructions"""
    print_header("STEP 4: Monitor DAG Execution")
    
    print("🔍 Open Airflow UI to monitor:")
    print("   URL: http://localhost:8080")
    print("   Login: admin / rafie123")
    print("   Navigate: DAGs → etl_driver_kpi")
    print("\n   View:")
    print("   ├─ Graph View: Task dependencies & status")
    print("   ├─ Tree View: Historical runs")
    print("   └─ Logs: Detailed execution logs")
    print("\n   Task sequence:")
    print("   1️⃣  extract_oltp_data → Check 5 tables exist")
    print("   2️⃣  transform_load_analytics → Complex JOIN + KPI")
    print("   3️⃣  validate_data_quality → Quality report")

def verify_results():
    """Show verification instructions"""
    print_header("STEP 5: Verify Results")
    
    print("✅ After DAG completes successfully:\n")
    print("Check analytics table:")
    print("""
docker exec postgres psql -U airflow -d airflow << EOF
  SELECT COUNT(*) as total_records 
  FROM analytics.fact_driver_performance;
  
  SELECT uuid_user, id_armada, avg_rating, kpi_score 
  FROM analytics.fact_driver_performance 
  ORDER BY kpi_score DESC 
  LIMIT 5;
EOF
""")
    
    print("\nExpected output: 50 drivers with KPI scores calculated")

def show_next_steps():
    """Show next steps"""
    print_header("✨ WORKFLOW COMPLETE!")
    
    print("""
🎉 Setup selesai! Selanjutnya:

1️⃣  Monitor DAG execution (sambil menunggu)
    • Open http://localhost:8080
    • Watch Graph View untuk progress
    • Check logs untuk troubleshoot

2️⃣  Setelah DAG selesai, verify results
    • Query analytics.fact_driver_performance
    • Check KPI scores calculated

3️⃣  Setup Dashboard (Optional)
    • Open Metabase: http://localhost:3000
    • Connect to Airflow PostgreSQL
    • Create visualizations dari analytics table

4️⃣  Automate Future Runs
    • DAG berjalan otomatis setiap hari 00:00 UTC
    • Tidak perlu setup ulang
    • Logs otomatis tersimpan

📖 Dokumentasi:
    • WORKFLOW_PRAKTIS.md - Setup panduan
    • PENJELASAN_ETL_DAG.md - Technical details
    • MAPPING_KOLOM_DATA.md - Column mapping
""")

def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║           🚀 AIRFLOW DRIVER KPI ETL - COMPLETE WORKFLOW                  ║
║                                                                            ║
║  One-command solution untuk langkah 2-5 setelah CSV siap                ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")
    
    # Step 1: Check CSV files
    if not check_csv_files():
        sys.exit(1)
    
    input("Press Enter untuk lanjut...")
    
    # Step 2: Import CSV
    if not import_csv_to_airflow():
        sys.exit(1)
    
    input("Press Enter untuk lanjut...")
    
    # Step 3: Trigger DAG
    trigger_dag()
    
    input("Press Enter untuk lanjut...")
    
    # Step 4: Monitor
    monitor_dag()
    
    input("Press Enter untuk lanjut...")
    
    # Step 5: Verify
    verify_results()
    
    input("Press Enter untuk selesai...")
    
    # Next steps
    show_next_steps()
    
    print("\n👋 Terima kasih! Workflow started.\n")

if __name__ == "__main__":
    main()
