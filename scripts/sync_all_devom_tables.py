#!/usr/bin/env python3
"""
Sync all tables from devom.silog.co.id to warehouse database
This script will:
1. List all tables from source
2. Create matching tables in warehouse schema
3. Copy data from source to warehouse
"""
import psycopg2
from psycopg2 import sql

SOURCE_DB = {
    'host': 'devom.silog.co.id',
    'database': 'om',
    'user': 'om',
    'password': 'om',
    'port': 5432
}

TARGET_DB = {
    'host': 'localhost',
    'database': 'warehouse',
    'user': 'postgres',
    'password': 'postgres123',
    'port': 5433
}

def get_all_source_tables():
    """Get list of all tables from source database"""
    try:
        conn = psycopg2.connect(**SOURCE_DB)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema='public' 
            AND table_type='BASE TABLE'
            ORDER BY table_name;
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        return tables
    except Exception as e:
        print(f"❌ Error getting source tables: {e}")
        return []

def get_table_structure(table_name):
    """Get table structure (CREATE TABLE statement)"""
    try:
        conn = psycopg2.connect(**SOURCE_DB)
        cursor = conn.cursor()
        
        # Get columns
        cursor.execute(f"""
            SELECT 
                column_name, 
                data_type, 
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_schema='public' AND table_name='{table_name}'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return columns
    except Exception as e:
        print(f"❌ Error getting structure for {table_name}: {e}")
        return []

def create_table_in_warehouse(table_name, columns):
    """Create table in warehouse schema"""
    try:
        conn = psycopg2.connect(**TARGET_DB)
        cursor = conn.cursor()
        
        # Build CREATE TABLE statement
        col_definitions = []
        for col in columns:
            col_name = col[0]
            data_type = col[1]
            max_length = col[2]
            nullable = col[3]
            default = col[4]
            
            # Build column definition
            if data_type == 'character varying' and max_length:
                col_def = f"{col_name} VARCHAR({max_length})"
            elif data_type == 'character':
                col_def = f"{col_name} CHAR({max_length})" if max_length else f"{col_name} CHAR"
            elif data_type == 'timestamp without time zone':
                col_def = f"{col_name} TIMESTAMP"
            elif data_type == 'timestamp with time zone':
                col_def = f"{col_name} TIMESTAMPTZ"
            elif data_type == 'USER-DEFINED':
                col_def = f"{col_name} TEXT"  # Fallback for custom types
            else:
                col_def = f"{col_name} {data_type.upper()}"
            
            # Add NOT NULL if applicable
            if nullable == 'NO':
                col_def += " NOT NULL"
            
            # Add default if exists
            if default:
                col_def += f" DEFAULT {default}"
            
            col_definitions.append(col_def)
        
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS warehouse.{table_name} (
            {', '.join(col_definitions)}
        );
        """
        
        cursor.execute(create_sql)
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"❌ Error creating table {table_name}: {e}")
        return False

def sync_table_data(table_name):
    """Copy data from source to warehouse"""
    try:
        # Connect to both databases
        source_conn = psycopg2.connect(**SOURCE_DB)
        source_cursor = source_conn.cursor()
        
        target_conn = psycopg2.connect(**TARGET_DB)
        target_cursor = target_conn.cursor()
        
        # Get column names
        source_cursor.execute(f"SELECT * FROM {table_name} LIMIT 0")
        columns = [desc[0] for desc in source_cursor.description]
        col_names = ', '.join(columns)
        
        # Clear target table
        target_cursor.execute(f"TRUNCATE TABLE warehouse.{table_name} CASCADE")
        
        # Fetch data from source
        source_cursor.execute(f"SELECT * FROM {table_name}")
        rows = source_cursor.fetchall()
        
        # Insert into target
        if rows:
            placeholders = ', '.join(['%s'] * len(columns))
            insert_query = f"INSERT INTO warehouse.{table_name} ({col_names}) VALUES ({placeholders})"
            target_cursor.executemany(insert_query, rows)
            target_conn.commit()
        
        source_cursor.close()
        source_conn.close()
        target_cursor.close()
        target_conn.close()
        
        return True, len(rows) if rows else 0
    except Exception as e:
        print(f"❌ Error syncing data for {table_name}: {e}")
        return False, 0

def main():
    print("=" * 70)
    print("SYNCING ALL TABLES FROM devom.silog.co.id TO WAREHOUSE")
    print("=" * 70)
    
    # Get all source tables
    print("\n[1/3] Getting list of source tables...")
    source_tables = get_all_source_tables()
    print(f"✓ Found {len(source_tables)} tables in source database")
    
    # Create tables in warehouse
    print("\n[2/3] Creating tables in warehouse schema...")
    created_count = 0
    for i, table_name in enumerate(source_tables, 1):
        print(f"  [{i}/{len(source_tables)}] Creating warehouse.{table_name}...", end=" ")
        
        # Get table structure
        columns = get_table_structure(table_name)
        if not columns:
            print("❌ SKIP (no structure)")
            continue
        
        # Create table
        if create_table_in_warehouse(table_name, columns):
            print("✓")
            created_count += 1
        else:
            print("❌")
    
    print(f"\n✓ Created {created_count}/{len(source_tables)} tables")
    
    # Sync data
    print("\n[3/3] Syncing data...")
    synced_count = 0
    total_rows = 0
    
    for i, table_name in enumerate(source_tables, 1):
        print(f"  [{i}/{len(source_tables)}] Syncing warehouse.{table_name}...", end=" ")
        
        success, row_count = sync_table_data(table_name)
        if success:
            print(f"✓ ({row_count} rows)")
            synced_count += 1
            total_rows += row_count
        else:
            print("❌")
    
    # Summary
    print("\n" + "=" * 70)
    print("SYNC COMPLETE")
    print("=" * 70)
    print(f"✅ Tables created: {created_count}/{len(source_tables)}")
    print(f"✅ Tables synced: {synced_count}/{len(source_tables)}")
    print(f"✅ Total rows copied: {total_rows:,}")
    print("=" * 70)

if __name__ == "__main__":
    main()
