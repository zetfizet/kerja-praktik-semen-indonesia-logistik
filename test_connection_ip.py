#!/usr/bin/env python3
"""
🔌 Test Database Connection via IP Address
Test koneksi ke 172.20.145.83 (alternative ke devom.silog.co.id)
"""

import psycopg2
from psycopg2.extras import DictCursor
import sys

# Database aplikasi - test dengan IP address
SOURCE_DB_IP = {
    "host": "172.20.145.83",  # IP address langsung
    "database": "devom.silog.co.id",
    "user": "om",
    "password": "om",
    "port": 5432
}

SOURCE_DB_DOMAIN = {
    "host": "devom.silog.co.id",  # Domain
    "database": "devom.silog.co.id",
    "user": "om",
    "password": "om",
    "port": 5432
}

print("\n" + "=" * 80)
print("🔌 DATABASE CONNECTION TEST")
print("=" * 80)

# Test 1: IP Address
print("\n🔹 Test 1: Connect via IP (172.20.145.83)")
print("-" * 80)

try:
    conn = psycopg2.connect(**SOURCE_DB_IP)
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    
    print("✅ SUCCESS! Connected via IP address")
    print(f"   PostgreSQL: {version['version'][:60]}...")
    
    # List tables
    cursor.execute("""
        SELECT tablename FROM pg_tables 
        WHERE schemaname = 'public'
        ORDER BY tablename;
    """)
    tables = cursor.fetchall()
    
    print(f"\n📋 Tables found ({len(tables)}):")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) as cnt FROM {table['tablename']};")
        count = cursor.fetchone()['cnt']
        print(f"   • {table['tablename']:<35} ({count:,} rows)")
    
    cursor.close()
    conn.close()
    
    print("\n✨ Connection is working! You can use 172.20.145.83 for direct ETL sync")
    
except psycopg2.OperationalError as e:
    print(f"❌ Connection failed via IP")
    print(f"   Error: {str(e)}")

# Test 2: Domain
print("\n\n🔹 Test 2: Connect via Domain (devom.silog.co.id)")
print("-" * 80)

try:
    conn = psycopg2.connect(**SOURCE_DB_DOMAIN)
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    
    print("✅ SUCCESS! Connected via domain")
    print(f"   PostgreSQL: {version['version'][:60]}...")
    
    cursor.close()
    conn.close()
    
except psycopg2.OperationalError as e:
    print(f"❌ Connection failed via domain")
    print(f"   Error: {str(e)[:100]}...")

print("\n" + "=" * 80)
print("📊 CREDENTIALS REFERENCE")
print("=" * 80)
print(f"""
Source Database (Application):
  ├─ Host (IP):     172.20.145.83
  ├─ Host (Domain): devom.silog.co.id
  ├─ Database:      devom.silog.co.id
  ├─ User:          om
  ├─ Password:      om
  └─ Port:          5432

Target Database (Airflow Analytics):
  ├─ Host:          postgres (Docker) / localhost (Host)
  ├─ Database:      airflow
  ├─ User:          airflow
  ├─ Password:      airflow
  └─ Port:          5432
""")

print("=" * 80)
