#!/usr/bin/env python3
"""
🔄 AUTO EXTRACT - Directly from PostgreSQL to CSV
Mengambil data langsung dari database aplikasi ke CSV files
"""

import psycopg2
from psycopg2.extras import DictCursor
import csv
from pathlib import Path
import sys

# Database aplikasi
APP_DB = {
    "host": "devom.silog.co.id",
    "database": "devom.silog.co.id",
    "user": "om",
    "password": "om",
    "port": 5432
}

# Output folder
OUTPUT_FOLDER = Path("/home/rafiez/airflow-stack/data")
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

# Tables to extract
TABLES = [
    "driver_armada",
    "rating",
    "delivery_order",
    "perangkat_gps_driver",
    "rekening_driver"
]

def extract_table_to_csv(conn, table_name):
    """Extract single table to CSV"""
    try:
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        # Get all data
        cursor.execute(f"SELECT * FROM {table_name};")
        rows = cursor.fetchall()
        
        if not rows:
            print(f"⚠️  {table_name}: No data found")
            cursor.close()
            return 0
        
        # Get column names
        columns = rows[0].keys()
        
        # Write to CSV
        csv_path = OUTPUT_FOLDER / f"{table_name}.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"✅ {table_name:<35} {len(rows):>6} rows → {csv_path.name}")
        cursor.close()
        return len(rows)
        
    except Exception as e:
        print(f"❌ {table_name}: {str(e)}")
        return 0

def main():
    print("\n" + "=" * 80)
    print("🔄 AUTO EXTRACT - PostgreSQL to CSV")
    print("=" * 80 + "\n")
    
    # Test connection
    print("🔌 Connecting to database...")
    try:
        conn = psycopg2.connect(**APP_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Connected to PostgreSQL")
        print(f"   {version[0][:60]}...\n")
        cursor.close()
    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {str(e)}\n")
        print("⚠️  This is expected if:")
        print("   • Network can't reach devom.silog.co.id")
        print("   • Firewall blocking port 5432")
        print("   • Database offline\n")
        print("✨ ALTERNATIVE: Use pgAdmin4 export method")
        print("   Buka: http://localhost:5050")
        print("   Query → Export as CSV → Copy to /data/ folder")
        return False
    
    # Extract tables
    print("📥 Extracting tables...\n")
    total_rows = 0
    
    for table in TABLES:
        rows = extract_table_to_csv(conn, table)
        total_rows += rows
    
    conn.close()
    
    # Summary
    print(f"\n✨ Complete! Total: {total_rows} rows exported to {OUTPUT_FOLDER}\n")
    
    # List files
    csv_files = list(OUTPUT_FOLDER.glob("*.csv"))
    if csv_files:
        print("📁 CSV files created:")
        for f in sorted(csv_files):
            size_kb = f.stat().st_size / 1024
            print(f"   • {f.name:<35} ({size_kb:>8.2f} KB)")
        
        print(f"\n🚀 Next step: Import CSV to Airflow")
        print(f"   bash /home/rafiez/airflow-stack/run_etl.sh")
    else:
        print("❌ No CSV files created")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
