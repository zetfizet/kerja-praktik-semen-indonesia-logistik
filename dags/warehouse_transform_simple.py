"""
Warehouse Transform DAG - Simple Analytics
===========================================

Transform sederhana dari public.* ke analytics.*
Fokus: Daily counts & basic aggregations tanpa asumsi kolom

Setup manual sekali:
  CREATE SCHEMA IF NOT EXISTS analytics;

Schedule: 3 AM daily
"""

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from datetime import datetime, timedelta
import psycopg2

default_args = {
    'owner': 'data_team',
    'retries': 1,
    'retry_delay': timedelta(minutes=3),
    'start_date': datetime(2026, 2, 6),
}

dag = DAG(
    'warehouse_transform_simple',
    default_args=default_args,
    description='🔄 Simple Transform: public.* → analytics.* (daily counts)',
    schedule='0 3 * * *',
    catchup=False,
    tags=['warehouse', 'transform', 'analytics'],
)

TARGET_DB_CONFIG = {
    'host': 'postgres',
    'database': 'warehouse',
    'user': 'airflow',
    'password': 'airflow',
    'port': 5432,
}


def transform_daily_table_counts():
    """
    Simple daily count untuk tabel-tabel utama
    Hardcoded untuk reliability
    """
    conn = psycopg2.connect(**TARGET_DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        print("🔄 Transforming daily table counts...")
        
        cursor.execute("DROP TABLE IF EXISTS analytics.daily_table_counts")
        
        # Get list of all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        
        # Build UNION ALL query dynamically
        union_parts = []
        for table in tables:
            union_parts.append(f"""
                SELECT 
                    CURRENT_DATE as count_date,
                    '{table}' as table_name,
                    COUNT(*) as total_rows
                FROM public.{table}
            """)
        
        full_query = f"""
            CREATE TABLE analytics.daily_table_counts AS
            {' UNION ALL '.join(union_parts)}
            ORDER BY total_rows DESC
        """
        
        cursor.execute(full_query)
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM analytics.daily_table_counts")
        count = cursor.fetchone()[0]
        
        print(f"✓ daily_table_counts: {count} tables tracked")
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def transform_orders_daily_summary():
    """
    Daily summary untuk tabel orders (defensive - auto-detect columns)
    """
    conn = psycopg2.connect(**TARGET_DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        print("🔄 Transforming orders daily summary...")
        
        # Check if table exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'orders'
        """)
        
        if cursor.fetchone()[0] == 0:
            print("  ⚠ orders table not found, skipping")
            return
        
        # Check columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'orders' 
            AND table_schema = 'public'
        """)
        
        columns = [row[0] for row in cursor.fetchall()]
        
        # Find date column
        date_column = None
        for col in ['created_at', 'dibuat_pada', 'diubah_pada', 'updated_at', 'tanggal']:
            if col in columns:
                date_column = col
                break
        
        if not date_column:
            print(f"  ⚠ No date column found in orders, creating simple count only")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics.orders_daily_summary (
                    order_date DATE PRIMARY KEY,
                    total_orders BIGINT,
                    transformed_at TIMESTAMP
                )
            """)
            cursor.execute("DELETE FROM analytics.orders_daily_summary WHERE order_date = CURRENT_DATE")
            cursor.execute("""
                INSERT INTO analytics.orders_daily_summary
                SELECT 
                    CURRENT_DATE as order_date,
                    COUNT(*) as total_orders,
                    CURRENT_TIMESTAMP as transformed_at
                FROM public.orders
            """)
        else:
            has_deleted_at = 'deleted_at' in columns
            
            # Create table structure if not exists
            deleted_cols = "active_orders BIGINT, deleted_orders BIGINT," if has_deleted_at else ""
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS analytics.orders_daily_summary (
                    order_date DATE PRIMARY KEY,
                    total_orders BIGINT,
                    {deleted_cols}
                    transformed_at TIMESTAMP
                )
            """)
            
            # Delete last 7 days (reprocess untuk catch updates & late data)
            cursor.execute(f"""
                DELETE FROM analytics.orders_daily_summary 
                WHERE order_date >= CURRENT_DATE - INTERVAL '7 days'
            """)
            
            deleted_counts = """
                COUNT(CASE WHEN deleted_at IS NULL THEN 1 END) as active_orders,
                COUNT(CASE WHEN deleted_at IS NOT NULL THEN 1 END) as deleted_orders,
            """ if has_deleted_at else ""
            
            # Insert only last 7 days
            cursor.execute(f"""
                INSERT INTO analytics.orders_daily_summary
                SELECT 
                    DATE({date_column}) as order_date,
                    COUNT(*) as total_orders,
                    {deleted_counts}
                    CURRENT_TIMESTAMP as transformed_at
                FROM public.orders
                WHERE DATE({date_column}) >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY DATE({date_column})
                ORDER BY order_date DESC
            """)
        
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM analytics.orders_daily_summary")
        count = cursor.fetchone()[0]
        
        print(f"✓ orders_daily_summary: {count} days")
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


def transform_customers_summary():
    """
    Customer summary statistics (defensive - check table exists)
    """
    conn = psycopg2.connect(**TARGET_DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        print("🔄 Transforming customers summary...")
        
        # Check if table exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'customers'
        """)
        
        if cursor.fetchone()[0] == 0:
            print("  ⚠ customers table not found, skipping")
            return
        
        # Check for columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'customers'
        """)
        columns = [row[0] for row in cursor.fetchall()]
        
        has_deleted_at = 'deleted_at' in columns
        has_created_at = 'created_at' in columns
        
        cursor.execute("DROP TABLE IF EXISTS analytics.customers_summary")
        
        deleted_filter = "COUNT(CASE WHEN deleted_at IS NULL THEN 1 END) as active_customers, COUNT(CASE WHEN deleted_at IS NOT NULL THEN 1 END) as deleted_customers," if has_deleted_at else "0 as active_customers, 0 as deleted_customers,"
        created_filter = "COUNT(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as new_customers_30d, COUNT(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as new_customers_7d," if has_created_at else "0 as new_customers_30d, 0 as new_customers_7d,"
        
        cursor.execute(f"""
            CREATE TABLE analytics.customers_summary AS
            SELECT 
                COUNT(*) as total_customers,
                {deleted_filter}
                {created_filter}
                CURRENT_TIMESTAMP as transformed_at
            FROM public.customers
        """)
        
        conn.commit()
        
        cursor.execute("SELECT total_customers FROM analytics.customers_summary")
        count = cursor.fetchone()[0]
        
        print(f"✓ customers_summary: {count} total customers")
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def transform_delivery_daily_summary():
    """
    Daily summary untuk delivery_order (defensive - auto-detect columns)
    """
    conn = psycopg2.connect(**TARGET_DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        print("🔄 Transforming delivery daily summary...")
        
        # Check if table exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'delivery_order'
        """)
        
        if cursor.fetchone()[0] == 0:
            print("  ⚠ delivery_order table not found, skipping")
            return
        
        # Check columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'delivery_order' 
            AND table_schema = 'public'
        """)
        
        columns = [row[0] for row in cursor.fetchall()]
        
        # Find date column
        date_column = None
        for col in ['created_at', 'dibuat_pada', 'diubah_pada', 'tanggal_kirim', 'tanggal']:
            if col in columns:
                date_column = col
                break
        
        if not date_column:
            print(f"  ⚠ No date column found, creating simple count")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics.delivery_daily_summary (
                    delivery_date DATE PRIMARY KEY,
                    total_deliveries BIGINT,
                    transformed_at TIMESTAMP
                )
            """)
            cursor.execute("DELETE FROM analytics.delivery_daily_summary WHERE delivery_date = CURRENT_DATE")
            cursor.execute("""
                INSERT INTO analytics.delivery_daily_summary
                SELECT 
                    CURRENT_DATE as delivery_date,
                    COUNT(*) as total_deliveries,
                    CURRENT_TIMESTAMP as transformed_at
                FROM public.delivery_order
            """)
        else:
            has_deleted_at = 'deleted_at' in columns
            
            # Create table structure if not exists
            deleted_col = "active_deliveries BIGINT," if has_deleted_at else ""
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS analytics.delivery_daily_summary (
                    delivery_date DATE PRIMARY KEY,
                    total_deliveries BIGINT,
                    {deleted_col}
                    transformed_at TIMESTAMP
                )
            """)
            
            # Delete last 7 days (reprocess untuk catch updates)
            cursor.execute(f"""
                DELETE FROM analytics.delivery_daily_summary 
                WHERE delivery_date >= CURRENT_DATE - INTERVAL '7 days'
            """)
            
            deleted_count = "COUNT(CASE WHEN deleted_at IS NULL THEN 1 END) as active_deliveries," if has_deleted_at else ""
            
            # Insert only last 7 days
            cursor.execute(f"""
                INSERT INTO analytics.delivery_daily_summary
                SELECT 
                    DATE({date_column}) as delivery_date,
                    COUNT(*) as total_deliveries,
                    {deleted_count}
                    CURRENT_TIMESTAMP as transformed_at
                FROM public.delivery_order
                WHERE DATE({date_column}) >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY DATE({date_column})
                ORDER BY delivery_date DESC
            """)
        
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM analytics.delivery_daily_summary")
        count = cursor.fetchone()[0]
        
        print(f"✓ delivery_daily_summary: {count} days")
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


def transform_inventory_summary():
    """
    Current inventory status summary
    Auto-detect columns untuk defensive programming
    """
    conn = psycopg2.connect(**TARGET_DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        print("🔄 Transforming inventory summary...")
        
        # Check if stok table exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'stok'
        """)
        
        if cursor.fetchone()[0] == 0:
            print("  ⚠ stok table not found, skipping")
            return
        
        # Check available columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'stok'
        """)
        
        columns = [row[0] for row in cursor.fetchall()]
        print(f"  ℹ Found columns in stok: {columns[:10]}")
        
        # Find quantity column
        qty_col = None
        for col in ['jumlah', 'qty', 'quantity', 'stok_qty', 'jumlah_stok']:
            if col in columns:
                qty_col = col
                break
        
        # Find warehouse/location column
        warehouse_col = None
        for col in ['id_lokasi', 'id_gudang', 'lokasi_id', 'gudang_id']:
            if col in columns:
                warehouse_col = col
                break
        
        # Find product column
        product_col = 'id_produk' if 'id_produk' in columns else None
        
        # Find minimum stock column
        min_col = None
        for col in ['minimum_stok', 'min_stok', 'minimum_qty', 'stok_minimum', 'min_qty']:
            if col in columns:
                min_col = col
                break
        
        cursor.execute("DROP TABLE IF EXISTS analytics.inventory_summary")
        
        # Build query based on available columns
        qty_query = f"SUM({qty_col})" if qty_col else "0"
        warehouse_query = f"COUNT(DISTINCT {warehouse_col})" if warehouse_col else "0"
        product_query = f"COUNT(DISTINCT {product_col})" if product_col else "0"
        zero_check = f"COUNT(CASE WHEN {qty_col} <= 0 THEN 1 END)" if qty_col else "0"
        low_check = f"COUNT(CASE WHEN {qty_col} < {min_col} THEN 1 END)" if (qty_col and min_col) else "0"
        
        cursor.execute(f"""
            CREATE TABLE analytics.inventory_summary AS
            SELECT 
                COUNT(*) as total_stock_records,
                {qty_query} as total_quantity,
                {warehouse_query} as total_locations,
                {product_query} as total_products,
                {zero_check} as out_of_stock_count,
                {low_check} as low_stock_count,
                CURRENT_TIMESTAMP as transformed_at
            FROM public.stok
        """)
        
        conn.commit()
        
        cursor.execute("SELECT total_stock_records FROM analytics.inventory_summary")
        count = cursor.fetchone()[0]
        
        print(f"✓ inventory_summary: {count} stock records")
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def print_summary():
    """Print analytics summary"""
    conn = psycopg2.connect(**TARGET_DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        print("\n" + "=" * 60)
        print("📊 ANALYTICS SUMMARY")
        print("=" * 60)
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables
            WHERE table_schema = 'analytics'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        
        for (table_name,) in tables:
            cursor.execute(f"SELECT COUNT(*) FROM analytics.{table_name}")
            count = cursor.fetchone()[0]
            print(f"  ✓ {table_name}: {count} rows")
        
        print("=" * 60)
        print(f"✅ Total: {len(tables)} analytics tables ready!")
        print("=" * 60)
        
    except Exception as e:
        print(f"⚠ Summary error: {e}")
    finally:
        cursor.close()
        conn.close()


# ============================================================================
# TASKS
# ============================================================================

task_table_counts = PythonOperator(
    task_id='transform_daily_table_counts',
    python_callable=transform_daily_table_counts,
    dag=dag,
)

task_orders = PythonOperator(
    task_id='transform_orders_daily',
    python_callable=transform_orders_daily_summary,
    dag=dag,
)

task_customers = PythonOperator(
    task_id='transform_customers_summary',
    python_callable=transform_customers_summary,
    dag=dag,
)

task_delivery = PythonOperator(
    task_id='transform_delivery_daily',
    python_callable=transform_delivery_daily_summary,
    dag=dag,
)

task_inventory = PythonOperator(
    task_id='transform_inventory_summary',
    python_callable=transform_inventory_summary,
    dag=dag,
)

task_summary = PythonOperator(
    task_id='print_summary',
    python_callable=print_summary,
    dag=dag,
)

# Dependencies - parallel transforms then summary
[task_table_counts, task_orders, task_customers, task_delivery, task_inventory] >> task_summary
