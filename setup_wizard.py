#!/usr/bin/env python3
"""
🚀 SETUP ASSISTANT - Database Connection & ETL Setup
Membantu Anda setup dari awal step-by-step
"""

import sys
import subprocess
from pathlib import Path

def clear_screen():
    subprocess.run("clear" if sys.platform != "win32" else "cls", shell=True)

def show_banner():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║          🚀 AIRFLOW DRIVER KPI ETL - SETUP WIZARD                        ║
║                                                                            ║
║  Membantu Anda setup koneksi database & ETL dari awal                   ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

def main_menu():
    """Main menu"""
    show_banner()
    
    print("""
┌─ PILIH OPSI ──────────────────────────────────────────────────────────────┐
│                                                                            │
│  📋 INFORMASI SISTEM                                                      │
│  ├─ 1️⃣  Status Docker & Services                                        │
│  ├─ 2️⃣  Cek PostgreSQL Connection                                       │
│  └─ 3️⃣  Explore Database Struktur                                       │
│                                                                            │
│  📊 DATA IMPORT                                                           │
│  ├─ 4️⃣  Download CSV Export Template                                    │
│  ├─ 5️⃣  Import CSV ke Airflow                                           │
│  └─ 6️⃣  Verify Import Success                                           │
│                                                                            │
│  ⚙️  ETL PIPELINE                                                        │
│  ├─ 7️⃣  Trigger ETL DAG                                                │
│  ├─ 8️⃣  View ETL Logs                                                  │
│  └─ 9️⃣  ETL Documentation                                               │
│                                                                            │
│  📞 BANTUAN                                                               │
│  ├─ 📘 Baca Full Documentation                                           │
│  ├─ 🔧 Troubleshooting Guide                                             │
│  └─ 0️⃣  Exit                                                            │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
""")
    
    choice = input("Pilih opsi (0-9 atau ?, h untuk help): ").strip().lower()
    return choice

def check_docker_status():
    """Check Docker containers status"""
    print("\n" + "=" * 80)
    print("🐳 DOCKER SERVICES STATUS")
    print("=" * 80 + "\n")
    
    result = subprocess.run(
        "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(result.stdout)
        print("\n✅ Docker containers running")
        
        # Check specific services
        required_services = [
            'airflow-webserver',
            'airflow-scheduler',
            'postgres',
            'redis',
            'pgadmin'
        ]
        
        print("\n📋 Required Services:")
        for service in required_services:
            result = subprocess.run(
                f"docker ps --filter 'name={service}' --format '{{{{.Names}}}}'",
                shell=True,
                capture_output=True,
                text=True
            )
            status = "✅" if result.stdout.strip() else "❌"
            print(f"   {status} {service}")
    else:
        print("❌ Docker not available or no containers running")

def check_db_connection():
    """Check PostgreSQL connection"""
    print("\n" + "=" * 80)
    print("🔌 DATABASE CONNECTION TEST")
    print("=" * 80 + "\n")
    
    result = subprocess.run(
        """docker exec airflow-webserver python3 -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='postgres',
        database='airflow',
        user='airflow',
        password='airflow',
        port=5432
    )
    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    version = cursor.fetchone()
    print('✅ Local Airflow DB: CONNECTED')
    print(f'   PostgreSQL {version[0].split(\",\")[0]}')
    cursor.close()
    conn.close()
except Exception as e:
    print(f'❌ Connection Failed: {str(e)}')
" 2>/dev/null""",
        shell=True,
        capture_output=True,
        text=True
    )
    
    print(result.stdout)

def check_csv_files():
    """Check if CSV files exist"""
    print("\n" + "=" * 80)
    print("📁 CSV FILES STATUS")
    print("=" * 80 + "\n")
    
    data_folder = Path("/home/rafiez/airflow-stack/data")
    data_folder.mkdir(exist_ok=True)
    
    required_files = [
        'driver_armada.csv',
        'rating.csv',
        'delivery_order.csv',
        'perangkat_gps_driver.csv',
        'rekening_driver.csv'
    ]
    
    print(f"Data folder: {data_folder}\n")
    
    for csv_file in required_files:
        file_path = data_folder / csv_file
        if file_path.exists():
            size = file_path.stat().st_size / 1024  # KB
            print(f"   ✅ {csv_file:<30} ({size:.2f} KB)")
        else:
            print(f"   ❌ {csv_file:<30} NOT FOUND")
    
    csv_count = len(list(data_folder.glob("*.csv")))
    if csv_count == 0:
        print("\n⚠️  No CSV files found!")
        print("📋 Please export CSV from pgAdmin4:")
        print("   1. Buka http://localhost:5050 (pgAdmin4)")
        print("   2. Tools → Query Tool")
        print("   3. SELECT * FROM table_name;")
        print("   4. Download hasil sebagai CSV")
        print("   5. Simpan di /home/rafiez/airflow-stack/data/")
    else:
        print(f"\n✅ {csv_count} CSV files found")

def import_csv():
    """Run CSV import script"""
    print("\n" + "=" * 80)
    print("📥 IMPORTING CSV DATA")
    print("=" * 80 + "\n")
    
    result = subprocess.run(
        "cd /home/rafiez/airflow-stack && python3 import_csv.py",
        shell=True,
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.returncode != 0:
        print("❌ Error:", result.stderr)

def trigger_dag():
    """Trigger ETL DAG"""
    print("\n" + "=" * 80)
    print("▶️  TRIGGER ETL DAG")
    print("=" * 80 + "\n")
    
    print("Opsi:")
    print("  1. Via Airflow UI (Recommended)")
    print("  2. Via CLI command\n")
    
    choice = input("Pilih (1 or 2): ").strip()
    
    if choice == "1":
        print("""
✅ Buka http://localhost:8080
   ├─ Login: admin / rafie123
   ├─ Navigasi ke: DAGs → etl_driver_kpi
   ├─ Klik tombol ▶️ (Play/Trigger)
   └─ Monitor di Graph View

Logs tersimpan di:
   /home/rafiez/airflow-stack/airflow/logs/
""")
    elif choice == "2":
        print("\n⏳ Triggering DAG via CLI...\n")
        result = subprocess.run(
            "docker exec airflow-scheduler airflow dags trigger etl_driver_kpi",
            shell=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if "successfully" in result.stdout.lower():
            print("✅ DAG triggered successfully!")
        else:
            print("Status:", result.stderr if result.returncode != 0 else result.stdout)

def view_documentation():
    """Show documentation menu"""
    print("\n" + "=" * 80)
    print("📚 DOCUMENTATION")
    print("=" * 80)
    
    docs = [
        ("PENJELASAN_ETL_DAG.md", "Penjelasan detail ETL & DAG logic"),
        ("MAPPING_KOLOM_DATA.md", "Schema mapping & column structure"),
        ("PANDUAN_IMPORT_DATA.md", "Step-by-step import guide"),
        ("DOKUMENTASI_ETL.md", "Architecture & detailed implementation")
    ]
    
    print("\nAvailable Documentation:\n")
    for i, (file, desc) in enumerate(docs, 1):
        path = f"/home/rafiez/airflow-stack/{file}"
        exists = "✅" if Path(path).exists() else "❌"
        print(f"  {i}. {exists} {file:<25} - {desc}")
    
    choice = input("\nPilih file (1-4) atau 0 untuk back: ").strip()
    if choice in ["1", "2", "3", "4"]:
        file = docs[int(choice) - 1][0]
        print(f"\n--- {file} ---\n")
        subprocess.run(f"cat /home/rafiez/airflow-stack/{file} | head -100", shell=True)

def show_help():
    """Show help information"""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                          📚 SETUP WIZARD HELP                             ║
╚════════════════════════════════════════════════════════════════════════════╝

🎯 WORKFLOW:

1. CHECK STATUS
   ├─ Verifikasi Docker services running
   ├─ Test PostgreSQL connection
   └─ Check CSV files ready

2. IMPORT DATA
   ├─ Export CSV dari pgAdmin4
   ├─ Simpan di /home/rafiez/airflow-stack/data/
   └─ Run import script

3. RUN ETL
   ├─ Trigger ETL DAG
   ├─ Monitor execution
   └─ View results

💾 CSV FILES REQUIRED:
   • driver_armada.csv
   • rating.csv
   • delivery_order.csv
   • perangkat_gps_driver.csv
   • rekening_driver.csv

🔗 CONNECTIONS:
   • Airflow:    http://localhost:8080 (admin/rafie123)
   • pgAdmin4:   http://localhost:5050
   • PostgreSQL: localhost:5432
   • Metabase:   http://localhost:3000

📖 DOCUMENTATION:
   • PENJELASAN_ETL_DAG.md - ETL logic explanation
   • MAPPING_KOLOM_DATA.md - Column mapping
   • PANDUAN_IMPORT_DATA.md - Import guide
   • DOKUMENTASI_ETL.md - Architecture details

💡 QUICK COMMANDS:
   • Check status:    python3 setup_wizard.py
   • Import CSV:      python3 import_csv.py
   • Explore DB:      python3 explore_db.py
   • Connection help: python3 connection_assistant.py

❓ COMMON ISSUES:

   Q: "Connection refused"
   A: - Check Docker: docker ps
      - Check PostgreSQL: docker logs postgres
      
   Q: "CSV not found"
   A: - Create folder: mkdir -p /home/rafiez/airflow-stack/data
      - Export from pgAdmin4 Tools → Query Tool
      
   Q: "DAG not running"
   A: - Check Airflow logs: docker logs airflow-scheduler
      - Verify connection in Airflow UI Admin → Connections

""")

def main():
    """Main loop"""
    while True:
        clear_screen()
        choice = main_menu()
        
        if choice == "1":
            check_docker_status()
        elif choice == "2":
            check_db_connection()
        elif choice == "3":
            print("\n🔍 Database Explorer\nRun: python3 explore_db.py")
        elif choice == "4":
            print("\n📋 CSV Export Template")
            print("Jalankan di pgAdmin4 Query Editor untuk setiap table:\n")
            tables = ['driver_armada', 'rating', 'delivery_order', 
                     'perangkat_gps_driver', 'rekening_driver']
            for table in tables:
                print(f"SELECT * FROM {table};")
                print("→ Download hasil sebagai CSV")
                print("→ Simpan di /home/rafiez/airflow-stack/data/\n")
        elif choice == "5":
            import_csv()
        elif choice == "6":
            check_csv_files()
        elif choice == "7":
            trigger_dag()
        elif choice == "8":
            print("\n📋 View ETL Logs")
            print("Logs folder: /home/rafiez/airflow-stack/airflow/logs/")
            subprocess.run("ls -lh /home/rafiez/airflow-stack/airflow/logs/ | head -20", shell=True)
        elif choice == "9":
            view_documentation()
        elif choice in ["?", "h"]:
            show_help()
        elif choice == "0":
            print("\n👋 Terima kasih! Goodbye!\n")
            break
        else:
            print("\n❌ Invalid option")
        
        if choice not in ["0", ""]:
            input("\n✅ Press Enter untuk continue...")

if __name__ == "__main__":
    main()
