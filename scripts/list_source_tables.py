#!/usr/bin/env python3
"""
List all tables from devom.silog.co.id source database
"""
import psycopg2

try:
    conn = psycopg2.connect(
        host='devom.silog.co.id',
        database='om',
        user='om',
        password='om',
        port=5432,
        connect_timeout=10
    )
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema='public' 
        ORDER BY table_name;
    """)
    tables = cursor.fetchall()
    
    print(f'✅ Connected to devom.silog.co.id')
    print(f'Total tables: {len(tables)}\n')
    print('Tables:')
    for i, table in enumerate(tables, 1):
        print(f'{i:3d}. {table[0]}')
    
    conn.close()
    
except Exception as e:
    print(f'❌ Connection failed: {e}')
    exit(1)
