#!/usr/bin/env python3
"""
Script untuk meng-copy struktur semua tables dari DEVOM ke Warehouse
Akan membuat semua tables dengan atribut yang sama di warehouse.public
"""

import psycopg2
from psycopg2 import sql
import sys

# Source database (DEVOM)
SOURCE_CONFIG = {
    'host': 'devom.silog.co.id',
    'port': 5432,
    'database': 'om',
    'user': 'om',
    'password': 'om',
}

# Target database (WAREHOUSE)
TARGET_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'warehouse',
    'user': 'postgres',
    'password': 'postgres123',
}

def get_all_tables_from_devom():
    """Get list of all tables from DEVOM database"""
    try:
        print("\n" + "="*70)
        print("📊 CONNECTING TO DEVOM DATABASE...")
        print("="*70)
        
        conn = psycopg2.connect(**SOURCE_CONFIG, connect_timeout=30)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"✅ Found {len(tables)} tables in DEVOM database")
        print("\nTables:")
        for i, table in enumerate(tables, 1):
            print(f"  {i:3d}. {table}")
        
        cursor.close()
        conn.close()
        
        return tables
    
    except Exception as e:
        print(f"❌ Error connecting to DEVOM: {e}")
        return []

def get_table_ddl(table_name):
    """Generate CREATE TABLE DDL from source table"""
    try:
        conn = psycopg2.connect(**SOURCE_CONFIG, connect_timeout=30)
        cursor = conn.cursor()
        
        # Get columns info
        cursor.execute("""
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                numeric_precision,
                numeric_scale,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = %s
            ORDER BY ordinal_position;
        """, (table_name,))
        
        columns = cursor.fetchall()
        
        # Get primary key
        cursor.execute("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_schema = 'public'
            AND tc.table_name = %s
            AND tc.constraint_type = 'PRIMARY KEY'
            ORDER BY kcu.ordinal_position;
        """, (table_name,))
        
        pk_columns = [row[0] for row in cursor.fetchall()]
        
        # Get foreign keys
        cursor.execute("""
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.table_schema = 'public'
            AND tc.table_name = %s
            AND tc.constraint_type = 'FOREIGN KEY';
        """, (table_name,))
        
        fk_columns = cursor.fetchall()
        
        # Get unique constraints
        cursor.execute("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_schema = 'public'
            AND tc.table_name = %s
            AND tc.constraint_type = 'UNIQUE'
            ORDER BY kcu.ordinal_position;
        """, (table_name,))
        
        unique_columns = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        # Generate DDL
        ddl = f"CREATE TABLE IF NOT EXISTS public.{table_name} (\n"
        
        column_defs = []
        for col in columns:
            col_name, data_type, char_len, num_prec, num_scale, is_null, col_default = col
            
            # Build column definition
            col_def = f"    {col_name} "
            
            # Data type
            if data_type == 'character varying':
                if char_len:
                    col_def += f"VARCHAR({char_len})"
                else:
                    col_def += "VARCHAR"
            elif data_type == 'character':
                col_def += f"CHAR({char_len})" if char_len else "CHAR"
            elif data_type == 'numeric':
                if num_prec and num_scale:
                    col_def += f"NUMERIC({num_prec},{num_scale})"
                else:
                    col_def += "NUMERIC"
            elif data_type == 'timestamp without time zone':
                col_def += "TIMESTAMP"
            elif data_type == 'timestamp with time zone':
                col_def += "TIMESTAMPTZ"
            elif data_type == 'USER-DEFINED':
                col_def += "TEXT"  # Fallback for custom types
            else:
                col_def += data_type.upper()
            
            # Nullable
            if is_null == 'NO':
                col_def += " NOT NULL"
            
            # Default value
            if col_default:
                # Don't add default if it's a sequence (SERIAL)
                if 'nextval' not in str(col_default):
                    col_def += f" DEFAULT {col_default}"
            
            column_defs.append(col_def)
        
        ddl += ",\n".join(column_defs)
        
        # Add primary key
        if pk_columns:
            pk_list = ", ".join(pk_columns)
            ddl += f",\n    PRIMARY KEY ({pk_list})"
        
        # Add unique constraints
        if unique_columns:
            for uc in unique_columns:
                ddl += f",\n    UNIQUE ({uc})"
        
        ddl += "\n);\n"
        
        # Add indexes
        ddl += f"\n-- Indexes for {table_name}\n"
        if pk_columns:
            ddl += f"CREATE INDEX IF NOT EXISTS idx_{table_name}_pk ON public.{table_name}({', '.join(pk_columns)});\n"
        
        # Add comment
        ddl += f"\nCOMMENT ON TABLE public.{table_name} IS 'Synced from DEVOM database';\n"
        
        return ddl
    
    except Exception as e:
        print(f"  ⚠️  Error getting DDL for {table_name}: {e}")
        return None

def create_tables_in_warehouse(tables):
    """Create all tables in warehouse database"""
    try:
        print("\n" + "="*70)
        print("🏗️  CREATING TABLES IN WAREHOUSE DATABASE...")
        print("="*70)
        
        conn = psycopg2.connect(**TARGET_CONFIG)
        cursor = conn.cursor()
        
        # Ensure public schema exists
        cursor.execute("CREATE SCHEMA IF NOT EXISTS public;")
        conn.commit()
        
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for table_name in tables:
            print(f"\n📋 Processing: {table_name}")
            
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
                print(f"   ⏭️  Table already exists, skipping...")
                skip_count += 1
                continue
            
            # Get DDL
            ddl = get_table_ddl(table_name)
            
            if ddl:
                try:
                    # Execute DDL (remove foreign key constraints for initial creation)
                    # We'll add FKs later in a separate pass
                    cursor.execute(ddl)
                    conn.commit()
                    print(f"   ✅ Created successfully")
                    success_count += 1
                except Exception as e:
                    print(f"   ⚠️  Error creating: {e}")
                    conn.rollback()
                    error_count += 1
            else:
                error_count += 1
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*70)
        print("📊 SUMMARY:")
        print(f"   ✅ Created: {success_count}")
        print(f"   ⏭️  Skipped: {skip_count}")
        print(f"   ⚠️  Errors: {error_count}")
        print("="*70)
        
        return success_count > 0
    
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def generate_ddl_file(tables):
    """Generate SQL file with all DDL statements"""
    filename = "sql/06_devom_tables_ddl.sql"
    
    print(f"\n📝 Generating DDL file: {filename}")
    
    try:
        with open(filename, 'w') as f:
            f.write("-- ============================================================================\n")
            f.write("-- DEVOM TABLES DDL - AUTO-GENERATED\n")
            f.write("-- ============================================================================\n")
            f.write("-- Structure dari semua tables di DEVOM database\n")
            f.write("-- Database Target: warehouse (schema: public)\n")
            f.write("-- Generated automatically from devom.silog.co.id\n")
            f.write("-- ============================================================================\n\n")
            
            f.write("-- Create public schema if not exists\n")
            f.write("CREATE SCHEMA IF NOT EXISTS public;\n\n")
            
            for table_name in tables:
                print(f"   Generating DDL for: {table_name}")
                ddl = get_table_ddl(table_name)
                if ddl:
                    f.write(f"-- Table: {table_name}\n")
                    f.write(f"-- {'='*70}\n")
                    f.write(ddl)
                    f.write("\n")
        
        print(f"✅ DDL file generated: {filename}")
        return True
    
    except Exception as e:
        print(f"❌ Error generating DDL file: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("🔄 COPY STRUCTURE DATABASE DEVOM → WAREHOUSE")
    print("="*70)
    print("\nSource: devom.silog.co.id (database: om)")
    print("Target: localhost:5433 (database: warehouse, schema: public)")
    print("="*70)
    
    # Step 1: Get all tables from DEVOM
    tables = get_all_tables_from_devom()
    
    if not tables:
        print("\n❌ No tables found or connection failed!")
        sys.exit(1)
    
    # Step 2: Generate DDL file
    print("\n" + "="*70)
    print("📝 Step 1: Generate DDL file")
    print("="*70)
    generate_ddl_file(tables)
    
    # Step 3: Create tables in warehouse
    print("\n" + "="*70)
    print("🏗️  Step 2: Create tables in warehouse")
    print("="*70)
    
    response = input("\n🤔 Proceed with creating tables in warehouse? (y/n): ")
    if response.lower() == 'y':
        create_tables_in_warehouse(tables)
    else:
        print("\n⏭️  Skipped table creation. DDL file has been generated.")
        print("   You can review and execute it manually:")
        print("   sql/06_devom_tables_ddl.sql")
    
    print("\n" + "="*70)
    print("✅ DONE!")
    print("="*70)
    print("\n📖 Next steps:")
    print("   1. Review DDL file: sql/06_devom_tables_ddl.sql")
    print("   2. Run data sync: bash airflow/dags/daily_warehouse_sync.py")
    print("   3. Verify in pgAdmin4: SELECT * FROM information_schema.tables WHERE table_schema='public';")
    print("")

if __name__ == "__main__":
    main()
