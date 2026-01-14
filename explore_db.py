#!/usr/bin/env python3
"""
Script untuk Connect langsung ke Database Aplikasi Anda
dan Explore struktur table serta data

Ini berguna untuk:
1. Melihat struktur table
2. Melihat sample data
3. Validate bahwa koneksi berhasil
"""

import psycopg2
from psycopg2.extras import DictCursor
import json
from datetime import datetime

# Database Aplikasi Anda (yang accessible via pgAdmin4)
SOURCE_DB = {
    "host": "devom.silog.co.id",
    "database": "devom.silog.co.id",  # Sesuai dengan Airflow connection
    "user": "om",
    "password": "om",
    "port": 5432
}

print("\n" + "=" * 80)
print("🔍 DATABASE EXPLORER - Direct Connection")
print("=" * 80)

try:
    # Test koneksi
    print(f"\n🔌 Connecting to {SOURCE_DB['host']}:{SOURCE_DB['port']}...")
    conn = psycopg2.connect(**SOURCE_DB)
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    print("✅ Connected successfully!\n")
    
    # Get database info
    cursor.execute("""
        SELECT datname, pg_size_pretty(pg_database_size(datname)) as size
        FROM pg_database 
        WHERE datname = current_database();
    """)
    db_info = cursor.fetchone()
    print(f"Database: {db_info['datname']}")
    print(f"Size: {db_info['size']}\n")
    
    # List all tables
    print("📋 All Tables in 'public' schema:")
    print("-" * 80)
    
    cursor.execute("""
        SELECT 
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
        FROM pg_tables 
        WHERE schemaname = 'public'
        ORDER BY tablename;
    """)
    
    tables = cursor.fetchall()
    for table in tables:
        print(f"  📊 {table['tablename']:<30} ({table['size']})")
    
    print("\n" + "=" * 80)
    print("📋 DETAILED TABLE STRUCTURE")
    print("=" * 80)
    
    # List important tables untuk ETL
    important_tables = [
        'driver_armada',
        'rating', 
        'delivery_order',
        'perangkat_gps_driver',
        'rekening_driver'
    ]
    
    for table_name in important_tables:
        try:
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (table_name,))
            
            exists = cursor.fetchone()[0]
            
            if exists:
                print(f"\n✅ TABLE: {table_name.upper()}")
                print("-" * 80)
                
                # Get columns
                cursor.execute("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name = %s
                    ORDER BY ordinal_position;
                """, (table_name,))
                
                columns = cursor.fetchall()
                print(f"  Columns ({len(columns)}):")
                for col in columns:
                    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                    default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                    print(f"    • {col['column_name']:<25} {col['data_type']:<15} {nullable}{default}")
                
                # Get row count
                cursor.execute(f"SELECT COUNT(*) as cnt FROM {table_name};")
                count = cursor.fetchone()['cnt']
                print(f"\n  Row Count: {count:,} rows")
                
                # Get sample data
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                samples = cursor.fetchall()
                if samples:
                    print(f"  Sample Data (first 3 rows):")
                    for i, row in enumerate(samples, 1):
                        print(f"    Row {i}: {dict(row)}")
                
            else:
                print(f"\n❌ TABLE: {table_name.upper()} - NOT FOUND")
                
        except Exception as e:
            print(f"\n❌ Error processing {table_name}: {str(e)}")
    
    print("\n" + "=" * 80)
    print("✨ Exploration Complete!")
    print("=" * 80)
    
    cursor.close()
    conn.close()
    
except psycopg2.OperationalError as e:
    print(f"\n❌ CONNECTION ERROR:")
    print(f"   {str(e)}")
    print(f"\n⚠️  Credentials used:")
    print(f"   Host: {SOURCE_DB['host']}")
    print(f"   Database: {SOURCE_DB['database']}")
    print(f"   User: {SOURCE_DB['user']}")
    print(f"   Port: {SOURCE_DB['port']}")
    print(f"\n💡 Tips:")
    print(f"   1. Verify credentials in pgAdmin4")
    print(f"   2. Check if database/table names are correct")
    print(f"   3. Verify network connectivity: ping {SOURCE_DB['host']}")
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")

print()
