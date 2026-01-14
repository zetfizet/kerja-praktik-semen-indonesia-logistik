#!/usr/bin/env python3
"""
Interactive Database Connection Assistant
Membantu Anda connect ke database aplikasi untuk ETL

Pilihan:
1. Export data via pgAdmin4 → Import ke Airflow
2. Setup SSH tunnel ke database server
3. Test koneksi dengan credentials berbeda
"""

import sys
import subprocess
from pathlib import Path

def show_menu():
    print("\n" + "=" * 80)
    print("🔧 DATABASE CONNECTION SETUP")
    print("=" * 80)
    print("\nPilihan cara connect ke database aplikasi Anda:\n")
    print("1️⃣  Export via pgAdmin4 (Recommended)")
    print("   → Buka pgAdmin4 → Query Editor")
    print("   → Select data dari tabel → Export as CSV")
    print("   → Simpan di folder: /home/rafiez/airflow-stack/data/\n")
    
    print("2️⃣  Direct Connect Test (jika network berubah)")
    print("   → Test koneksi dengan credentials baru\n")
    
    print("3️⃣  Setup SSH Tunnel (Advanced)")
    print("   → Koneksi via SSH ke server database\n")
    
    print("4️⃣  Generate SQL untuk Export")
    print("   → Generate SQL script untuk export data\n")
    
    print("5️⃣  View Setup Instructions")
    print("   → Lihat step-by-step panduan\n")
    
    print("0️⃣  Exit")
    print("\n" + "=" * 80)
    
    choice = input("\nPilih opsi (0-5): ").strip()
    return choice

def option_pgadmin():
    """Option 1: pgAdmin4 Export Instructions"""
    print("\n" + "=" * 80)
    print("📊 EXPORT DATA VIA PGADMIN4")
    print("=" * 80)
    
    instructions = """
STEP 1: Buka pgAdmin4
   → URL: http://localhost:5050
   → Login dengan credentials Anda
   
STEP 2: Koneksi ke Database Aplikasi
   → Di sidebar kiri: Add New Server
   → Name: "devom.silog.co.id"
   → Host: devom.silog.co.id
   → Username: om
   → Password: om
   → Port: 5432
   → Save
   
STEP 3: Query dan Export setiap table
   Untuk setiap table berikut, jalankan query:
   
   a) driver_armada.csv
      SELECT * FROM driver_armada;
      → Right click hasil → Export → CSV → Download
      → Simpan sebagai: /home/rafiez/airflow-stack/data/driver_armada.csv
      
   b) rating.csv
      SELECT * FROM rating;
      → Export sebagai: /home/rafiez/airflow-stack/data/rating.csv
      
   c) delivery_order.csv
      SELECT * FROM delivery_order;
      → Export sebagai: /home/rafiez/airflow-stack/data/delivery_order.csv
      
   d) perangkat_gps_driver.csv
      SELECT * FROM perangkat_gps_driver;
      → Export sebagai: /home/rafiez/airflow-stack/data/perangkat_gps_driver.csv
      
   e) rekening_driver.csv
      SELECT * FROM rekening_driver;
      → Export sebagai: /home/rafiez/airflow-stack/data/rekening_driver.csv

STEP 4: Verify file sudah di folder data/
   $ ls -lh /home/rafiez/airflow-stack/data/
   
STEP 5: Run import script
   $ cd /home/rafiez/airflow-stack
   $ python3 import_csv.py
   
✨ Done! Data sudah di Airflow analytics schema
"""
    print(instructions)

def option_test_connect():
    """Option 2: Test connection dengan credentials baru"""
    print("\n" + "=" * 80)
    print("🔌 TEST DATABASE CONNECTION")
    print("=" * 80)
    
    print("\nMasukkan credentials untuk test:\n")
    host = input("Host [devom.silog.co.id]: ").strip() or "devom.silog.co.id"
    db = input("Database [devom.silog.co.id]: ").strip() or "devom.silog.co.id"
    user = input("User [om]: ").strip() or "om"
    password = input("Password [om]: ").strip() or "om"
    port = input("Port [5432]: ").strip() or "5432"
    
    print(f"\n🔌 Testing connection to {host}:{port}...")
    
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=host,
            database=db,
            user=user,
            password=password,
            port=port
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ SUCCESS! Connected to PostgreSQL")
        print(f"   Version: {version[0][:50]}...\n")
        
        # List tables
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """)
        tables = cursor.fetchall()
        print(f"📋 Tables found ({len(tables)}):")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]};")
            count = cursor.fetchone()[0]
            print(f"   • {table[0]:<30} ({count:,} rows)")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print(f"\n💡 Mungkin:")
        print(f"   • Credentials salah")
        print(f"   • Network tidak bisa reach host")
        print(f"   • Database tidak ada")

def option_ssh_tunnel():
    """Option 3: Setup SSH Tunnel"""
    print("\n" + "=" * 80)
    print("🔐 SETUP SSH TUNNEL")
    print("=" * 80)
    
    instructions = """
SSH Tunnel memungkinkan koneksi ke remote database via SSH.

LANGKAH 1: Pastikan Anda punya SSH access ke server
   $ ssh -i your_key.pem your_user@devom.silog.co.id
   
LANGKAH 2: Setup SSH tunnel di local machine
   $ ssh -L 5433:localhost:5432 your_user@devom.silog.co.id -N -f
   
   Ini membuat:
   - Local port 5433 → tunnel → Remote 5432
   - Process berjalan di background (-f flag)

LANGKAH 3: Connect via tunnel
   python3 -c "
   import psycopg2
   conn = psycopg2.connect(
       host='127.0.0.1',
       port=5433,  # Local tunnel port
       database='devom.silog.co.id',
       user='om',
       password='om'
   )
   print('✅ Connected via SSH tunnel!')
   "
   
LANGKAH 4: Update credentials untuk Airflow
   Dalam explore_db.py atau direct_db_sync.py, ubah:
   - host: '127.0.0.1'
   - port: 5433 (tunnel port)

LANGKAH 5: Stop tunnel jika tidak perlu
   $ killall ssh
"""
    print(instructions)

def option_sql_export():
    """Option 4: Generate SQL untuk export"""
    print("\n" + "=" * 80)
    print("📄 SQL EXPORT QUERIES")
    print("=" * 80)
    
    sql_queries = """
Jalankan queries ini di pgAdmin4 Query Editor atau psql:

1️⃣  EXPORT driver_armada
    COPY (SELECT * FROM driver_armada) 
    TO '/tmp/driver_armada.csv' WITH CSV HEADER;

2️⃣  EXPORT rating
    COPY (SELECT * FROM rating) 
    TO '/tmp/rating.csv' WITH CSV HEADER;

3️⃣  EXPORT delivery_order
    COPY (SELECT * FROM delivery_order) 
    TO '/tmp/delivery_order.csv' WITH CSV HEADER;

4️⃣  EXPORT perangkat_gps_driver
    COPY (SELECT * FROM perangkat_gps_driver) 
    TO '/tmp/perangkat_gps_driver.csv' WITH CSV HEADER;

5️⃣  EXPORT rekening_driver
    COPY (SELECT * FROM rekening_driver) 
    TO '/tmp/rekening_driver.csv' WITH CSV HEADER;

Atau gunakan simple query dengan SELECT untuk copy-paste hasil ke CSV:

    SELECT * FROM driver_armada;
    SELECT * FROM rating;
    SELECT * FROM delivery_order;
    SELECT * FROM perangkat_gps_driver;
    SELECT * FROM rekening_driver;

Setelah export, simpan CSV files di:
    /home/rafiez/airflow-stack/data/
"""
    print(sql_queries)

def option_setup_help():
    """Option 5: Show full setup instructions"""
    print("\n" + "=" * 80)
    print("📋 COMPLETE SETUP INSTRUCTIONS")
    print("=" * 80)
    
    instructions = """
🎯 TUJUAN:
   Connect database aplikasi → Extract data → Transform (ETL) → Analytics

📝 PREREQUISITES:
   ✅ pgAdmin4 accessible (Anda sudah bisa akses)
   ✅ Database credentials (om/om @ devom.silog.co.id)
   ✅ Python 3 & psycopg2 installed

🔄 WORKFLOW:

TAHAP 1: EXPORT DATA dari Database Aplikasi
   
   Option A (Recommended): Via pgAdmin4
   ├─ Buka http://localhost:5050
   ├─ Login dengan credentials Anda
   ├─ Navigate ke database: devom.silog.co.id
   ├─ Untuk setiap table:
   │  ├─ Tools → Query Tool
   │  ├─ SELECT * FROM table_name;
   │  ├─ Execute
   │  ├─ Download hasil sebagai CSV
   │  └─ Simpan di /home/rafiez/airflow-stack/data/
   └─ File harus bernama:
      ├─ driver_armada.csv
      ├─ rating.csv
      ├─ delivery_order.csv
      ├─ perangkat_gps_driver.csv
      └─ rekening_driver.csv
   
   Option B: Direct Database Connection
   ├─ Jika network support
   ├─ Gunakan explore_db.py untuk test
   ├─ Atau setup SSH tunnel

TAHAP 2: IMPORT CSV ke Airflow Analytics
   
   $ cd /home/rafiez/airflow-stack
   $ python3 import_csv.py
   
   Output:
   ✅ Successfully imported X rows to driver_armada
   ✅ Successfully imported X rows to rating
   ... dst

TAHAP 3: TRIGGER ETL DAG
   
   Buka http://localhost:8080
   ├─ Login: admin / rafie123
   ├─ Navigate ke: DAGs → etl_driver_kpi
   ├─ Klik tombol ▶️ (Play/Trigger)
   └─ Monitor execution:
      ├─ Task 1: extract_oltp_data
      ├─ Task 2: transform_load_analytics
      └─ Task 3: validate_data_quality

TAHAP 4: VERIFY RESULTS
   
   Di Airflow Webserver:
   ├─ Lihat logs setiap task
   ├─ Cek status: Success/Failed/Pending
   
   Di Database:
   $ psql -h postgres -U airflow -d airflow
   SELECT * FROM analytics.fact_driver_performance LIMIT 5;
   SELECT COUNT(*) FROM analytics.fact_driver_performance;

TAHAP 5: SETUP DASHBOARD (Optional)
   
   Metabase (sudah siap di http://localhost:3000)
   ├─ Create data source → PostgreSQL → Airflow DB
   ├─ Create dashboard
   ├─ Add cards untuk metrics dari analytics.fact_driver_performance
   └─ Share dengan team

📊 TROUBLESHOOTING:

Problem: "Connection refused"
Solution: 
   ├─ Check docker containers running: docker ps
   ├─ Check network: ping devom.silog.co.id
   └─ Verify credentials di pgAdmin4

Problem: "File not found: data/driver_armada.csv"
Solution:
   ├─ Create folder: mkdir -p /home/rafiez/airflow-stack/data
   ├─ Verify CSV files: ls -la /home/rafiez/airflow-stack/data/
   └─ Check file names match exactly

Problem: "Column mismatch"
Solution:
   ├─ Check struktur table di pgAdmin4
   ├─ Verify CSV header sesuai dengan columns
   ├─ Gunakan MAPPING_KOLOM_DATA.md sebagai reference

🚀 AUTOMATION (Setelah initial setup)
   
   DAG berjalan otomatis setiap hari pukul 00:00 UTC
   ├─ Tidak perlu manual trigger setelah hari pertama
   ├─ Logs otomatis tersimpan
   └─ Alerts bisa disetup untuk failures

📞 SUPPORT

   Dokumentasi:
   ├─ PENJELASAN_ETL_DAG.md - Detailed ETL logic
   ├─ MAPPING_KOLOM_DATA.md - Column mapping
   ├─ DOKUMENTASI_ETL.md - Architecture details
   └─ PANDUAN_IMPORT_DATA.md - Step-by-step guide
"""
    print(instructions)

def main():
    """Main menu"""
    while True:
        choice = show_menu()
        
        if choice == "1":
            option_pgadmin()
        elif choice == "2":
            option_test_connect()
        elif choice == "3":
            option_ssh_tunnel()
        elif choice == "4":
            option_sql_export()
        elif choice == "5":
            option_setup_help()
        elif choice == "0":
            print("\n👋 Goodbye!\n")
            break
        else:
            print("\n❌ Invalid option. Please choose 0-5")
        
        input("\nPress Enter untuk continue...")

if __name__ == "__main__":
    main()
