from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import psycopg2
from psycopg2 import sql
import logging

logger = logging.getLogger(__name__)

# Database connection parameters
DB_HOST = "postgres"
DB_NAME = "airflow"
DB_USER = "airflow"
DB_PASSWORD = "airflow"
DB_PORT = 5432


def extract_data(**context):
    """
    EXTRACT: Read data dari PostgreSQL OLTP (public schema)
    Validasi bahwa semua source tables ada dan ada data
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        cursor = conn.cursor()
        
        # Check source tables existence dan row counts
        source_tables = [
            'driver_armada',
            'rating',
            'rekening_driver',
            'perangkat_gps_driver',
            'delivery_order'
        ]
        
        table_stats = {}
        for table in source_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                table_stats[table] = count
                logger.info(f"✓ {table}: {count} rows")
            except Exception as e:
                logger.warning(f"⚠ {table}: Not found or error - {str(e)}")
                table_stats[table] = 0
        
        cursor.close()
        conn.close()
        
        logger.info(f"\n=== EXTRACT SUMMARY ===\n{table_stats}\n")
        return {"status": "success", "tables": table_stats}
    
    except Exception as e:
        logger.error(f"Extract failed: {str(e)}")
        raise


def transform_and_load(**context):
    """
    TRANSFORM & LOAD: 
    - Join data dari multiple OLTP tables
    - Calculate driver KPI metrics
    - Load ke Analytics schema (fact_driver_performance)
    
    Metrics calculated:
    - avg_rating: Average rating dari tabel rating (last 30 days)
    - total_delivery: Total delivery orders (last 30 days)
    - gps_active_ratio: % perangkat GPS yang aktif
    - delivery_success_rate: % delivery dengan status DELIVERED
    - kpi_score: Weighted score (0-5)
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        cursor = conn.cursor()
        
        # Create analytics schema dan fact table jika belum ada
        logger.info("Creating analytics schema and fact tables...")
        cursor.execute("""
            CREATE SCHEMA IF NOT EXISTS analytics;
            
            CREATE TABLE IF NOT EXISTS analytics.fact_driver_performance (
                driver_kpi_id SERIAL PRIMARY KEY,
                uuid_user UUID NOT NULL,
                id_armada INTEGER,
                avg_rating DECIMAL(3, 2),
                total_delivery INTEGER,
                delivery_success_rate DECIMAL(5, 2),
                gps_active_ratio DECIMAL(5, 2),
                rekening_status VARCHAR(50),
                kpi_score DECIMAL(5, 2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(uuid_user, updated_at::DATE)
            );
            
            CREATE INDEX IF NOT EXISTS idx_driver_kpi_uuid ON analytics.fact_driver_performance(uuid_user);
            CREATE INDEX IF NOT EXISTS idx_driver_kpi_updated_at ON analytics.fact_driver_performance(updated_at);
        """)
        conn.commit()
        logger.info("✓ Analytics schema and tables created/verified")
        
        # Execute ETL transformation
        logger.info("\nRunning ETL transformation...")
        etl_sql = """
        INSERT INTO analytics.fact_driver_performance (
            uuid_user,
            id_armada,
            avg_rating,
            total_delivery,
            delivery_success_rate,
            gps_active_ratio,
            rekening_status,
            kpi_score
        )
        SELECT 
            da.uuid_user,
            da.id_armada,
            -- METRIC 1: Average rating dari tabel rating (last 30 days)
            COALESCE(ROUND(AVG(r.rating)::NUMERIC, 2), 0)::DECIMAL(3, 2) as avg_rating,
            -- METRIC 2: Total delivery orders (last 30 days)
            COUNT(DISTINCT do.uuid_delivery)::INTEGER as total_delivery,
            -- METRIC 3: Delivery success rate (% DELIVERED status)
            CASE 
                WHEN COUNT(DISTINCT do.uuid_delivery) > 0
                THEN ROUND(
                    (COUNT(CASE WHEN do.status_delivery = 'DELIVERED' THEN 1 END)::DECIMAL 
                     / COUNT(DISTINCT do.uuid_delivery) * 100)::NUMERIC, 
                    2
                )::DECIMAL(5, 2)
                ELSE 0::DECIMAL(5, 2)
            END as delivery_success_rate,
            -- METRIC 4: GPS active ratio (% perangkat aktif)
            CASE 
                WHEN COUNT(DISTINCT pgd.id_gps_driver) > 0
                THEN ROUND(
                    (COUNT(CASE WHEN pgd.latitude IS NOT NULL AND pgd.longtitude IS NOT NULL 
                                THEN 1 END)::DECIMAL 
                     / COUNT(DISTINCT pgd.id_gps_driver) * 100)::NUMERIC, 
                    2
                )::DECIMAL(5, 2)
                ELSE 0::DECIMAL(5, 2)
            END as gps_active_ratio,
            -- METRIC 5: Rekening status
            COALESCE(rd.status_aktif, 'UNKNOWN') as rekening_status,
            -- METRIC 6: KPI Score (weighted calculation)
            ROUND(
                (
                    COALESCE(AVG(r.rating)::NUMERIC, 0) * 0.30 +  -- 30% rating weight
                    CASE 
                        WHEN COUNT(DISTINCT do.uuid_delivery) > 0
                        THEN (COUNT(CASE WHEN do.status_delivery = 'DELIVERED' THEN 1 END)::DECIMAL 
                              / COUNT(DISTINCT do.uuid_delivery) * 5)
                        ELSE 0
                    END * 0.40 +  -- 40% delivery success weight
                    CASE 
                        WHEN COUNT(DISTINCT pgd.id_gps_driver) > 0
                        THEN (COUNT(CASE WHEN pgd.latitude IS NOT NULL AND pgd.longtitude IS NOT NULL 
                                        THEN 1 END)::DECIMAL 
                              / COUNT(DISTINCT pgd.id_gps_driver) * 5)
                        ELSE 0
                    END * 0.30  -- 30% GPS active weight
                )::NUMERIC, 
                2
            ) as kpi_score
        FROM 
            driver_armada da
            LEFT JOIN rating r ON da.uuid_user = r.uuid_user 
                AND r.dibuat_pada >= CURRENT_DATE - INTERVAL '30 days'
            LEFT JOIN delivery_order do ON da.id_armada = do.id_armada 
                AND do.tanggal_kirim >= CURRENT_DATE - INTERVAL '30 days'
            LEFT JOIN perangkat_gps_driver pgd ON da.uuid_user = pgd.uuid_user
            LEFT JOIN rekening_driver rd ON da.uuid_user = rd.uuid_user
        WHERE da.uuid_user IS NOT NULL
        GROUP BY 
            da.uuid_user, da.id_armada, rd.status_aktif
        ON CONFLICT (uuid_user, updated_at::DATE) 
        DO UPDATE SET
            id_armada = EXCLUDED.id_armada,
            avg_rating = EXCLUDED.avg_rating,
            total_delivery = EXCLUDED.total_delivery,
            delivery_success_rate = EXCLUDED.delivery_success_rate,
            gps_active_ratio = EXCLUDED.gps_active_ratio,
            rekening_status = EXCLUDED.rekening_status,
            kpi_score = EXCLUDED.kpi_score,
            updated_at = CURRENT_TIMESTAMP;
        """
        
        cursor.execute(etl_sql)
        conn.commit()
        logger.info("✓ ETL transformation completed successfully")
        
        cursor.close()
        conn.close()
        
        return {"status": "success"}
    
    except Exception as e:
        logger.error(f"Transform & Load failed: {str(e)}")
        raise


def validate_data(**context):
    """
    VALIDATE: Quality checks pada fact table
    Generate report tentang data yang ter-load
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        cursor = conn.cursor()
        
        # Data quality checks
        logger.info("\n=== DATA QUALITY REPORT ===\n")
        
        # Query stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT uuid_user) as unique_drivers,
                ROUND(AVG(kpi_score)::NUMERIC, 2) as avg_kpi_score,
                MIN(kpi_score) as min_kpi_score,
                MAX(kpi_score) as max_kpi_score,
                ROUND(AVG(avg_rating)::NUMERIC, 2) as avg_rating_score,
                ROUND(AVG(delivery_success_rate)::NUMERIC, 2) as avg_delivery_success,
                ROUND(AVG(gps_active_ratio)::NUMERIC, 2) as avg_gps_active
            FROM analytics.fact_driver_performance
            WHERE updated_at >= CURRENT_DATE
        """)
        
        stats = cursor.fetchone()
        report = f"""
        Total Records Loaded: {stats[0]}
        Unique Drivers: {stats[1]}
        
        KPI Score Statistics:
          - Average: {stats[2]}
          - Min: {stats[3]}
          - Max: {stats[4]}
        
        Component Averages:
          - Avg Rating: {stats[5]}/5.0
          - Delivery Success Rate: {stats[6]}%
          - GPS Active Ratio: {stats[7]}%
        
        Top 5 Drivers by KPI Score:
        """
        logger.info(report)
        
        cursor.execute("""
            SELECT 
                uuid_user, 
                id_armada, 
                ROUND(kpi_score::NUMERIC, 2) as kpi_score,
                ROUND(avg_rating::NUMERIC, 2) as rating,
                total_delivery as orders,
                ROUND(delivery_success_rate::NUMERIC, 1) as success_rate
            FROM analytics.fact_driver_performance
            WHERE updated_at >= CURRENT_DATE
            ORDER BY kpi_score DESC
            LIMIT 5
        """)
        
        top_drivers = cursor.fetchall()
        for row in top_drivers:
            logger.info(f"  {row[0]} (ID:{row[1]}) - KPI:{row[2]} Rating:{row[3]} Orders:{row[4]} Success:{row[5]}%")
        
        cursor.close()
        conn.close()
        
        return {"status": "validated", "records": stats[0]}
    
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise


with DAG(
    dag_id="etl_driver_kpi",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["driver", "kpi", "etl"],
    description="ETL Pipeline untuk Driver KPI Analytics - Aggregate rating, delivery success, dan GPS metrics"
) as dag:
    
    # Task 1: Extract dari OLTP
    extract = PythonOperator(
        task_id="extract_oltp_data",
        python_callable=extract_data,
        doc_md="""
        **Extract Task**
        
        Read data dari PostgreSQL OLTP tables:
        - driver_armada: Master data driver (id_armada, no_sim, uuid_user)
        - rating: Rating dan ulasan (id_rating, rating, ulasan, waktu_rating)
        - delivery_order: Delivery transactions (id_armada, uuid_delivery, status_delivery)
        - perangkat_gps_driver: GPS device status (id_gps_driver, latitude, longtitude, uuid_user)
        - rekening_driver: Bank account status (id_rekening, status_aktif, uuid_user)
        """
    )
    
    # Task 2: Transform & Load ke Analytics
    transform_load = PythonOperator(
        task_id="transform_load_analytics",
        python_callable=transform_and_load,
        doc_md="""
        **Transform & Load Task**
        
        Aggregate dan transform data:
        1. Join multiple OLTP tables by uuid_user dan id_armada
        2. Calculate metrics (30-day window)
        3. Compute weighted KPI score
        4. Insert/Update analytics.fact_driver_performance
        
        **Metrics:**
        - avg_rating: Average rating (0-5) dari tabel rating
        - total_delivery: Count of distinct delivery_order records
        - delivery_success_rate: % dengan status_delivery='DELIVERED'
        - gps_active_ratio: % GPS devices dengan latitude & longitude
        - kpi_score: Weighted (30% rating, 40% delivery success, 30% GPS active)
        """
    )
    
    # Task 3: Validate hasil ETL
    validate = PythonOperator(
        task_id="validate_data_quality",
        python_callable=validate_data,
        doc_md="""
        **Validation Task**
        
        Quality checks dan reporting:
        - Count total records & unique drivers
        - Calculate average metrics per component
        - Show top 5 drivers by KPI score
        - Log validation report
        
        Logs show:
        - Individual driver performance
        - Component-level statistics
        - Overall data quality metrics
        """
    )
    
    # Define task dependencies
    extract >> transform_load >> validate
