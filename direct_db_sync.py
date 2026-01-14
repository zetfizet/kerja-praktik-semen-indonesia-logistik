#!/usr/bin/env python3
"""
Script untuk Direct Database-to-Database ETL
Mengambil data langsung dari database aplikasi ke analytics warehouse
"""

import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Source Database (Aplikasi Anda)
SOURCE_DB = {
    "host": "devom.silog.co.id",
    "database": "silog_app",  # sesuaikan dengan nama DB Anda
    "user": "your_user",        # sesuaikan username
    "password": "your_password", # sesuaikan password
    "port": 5432
}

# Target Database (Analytics/Airflow)
TARGET_DB = {
    "host": "127.0.0.1",
    "database": "airflow",
    "user": "om",
    "password": "om",
    "port": 5432
}

def test_connection(db_config, db_name):
    """Test koneksi ke database"""
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        logger.info(f"✅ {db_name} terkoneksi: {version[0][:50]}...")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ {db_name} gagal terkoneksi: {str(e)}")
        return False

def extract_data(source_conn, table_name):
    """Extract data dari source database"""
    try:
        cursor = source_conn.cursor(cursor_factory=DictCursor)
        cursor.execute(f"SELECT * FROM public.{table_name};")
        rows = cursor.fetchall()
        logger.info(f"✅ {table_name}: {len(rows)} baris diambil")
        cursor.close()
        return rows
    except Exception as e:
        logger.error(f"❌ Gagal extract {table_name}: {str(e)}")
        return []

def create_analytics_table(target_conn):
    """Create analytics schema dan fact_driver_performance table"""
    try:
        cursor = target_conn.cursor()
        
        # Create schema
        cursor.execute("CREATE SCHEMA IF NOT EXISTS analytics;")
        
        # Create fact_driver_performance table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS analytics.fact_driver_performance (
            id SERIAL PRIMARY KEY,
            uuid_user VARCHAR(100) NOT NULL,
            id_armada INT,
            avg_rating DECIMAL(3,2),
            total_delivery INT,
            delivery_success_rate DECIMAL(5,2),
            gps_active_ratio DECIMAL(5,2),
            rekening_status VARCHAR(50),
            kpi_score DECIMAL(3,2),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(uuid_user, updated_at::DATE)
        );
        """
        cursor.execute(create_table_sql)
        target_conn.commit()
        logger.info("✅ Analytics table siap")
        cursor.close()
    except Exception as e:
        logger.error(f"❌ Gagal create table: {str(e)}")
        target_conn.rollback()

def load_data(target_conn, source_conn):
    """Load data dengan complex ETL transformation"""
    try:
        cursor = target_conn.cursor()
        
        # Complex ETL Query dengan 5-table JOIN
        etl_sql = """
        INSERT INTO analytics.fact_driver_performance 
        (uuid_user, id_armada, avg_rating, total_delivery, 
         delivery_success_rate, gps_active_ratio, rekening_status, kpi_score)
        
        SELECT 
            da.uuid_user,
            da.id_armada,
            COALESCE(AVG(r.rating)::DECIMAL(3,2), 0) as avg_rating,
            COUNT(DISTINCT do.uuid_order)::INT as total_delivery,
            COALESCE((
                COUNT(CASE WHEN do.status_delivery = 'DELIVERED' THEN 1 END)::DECIMAL / 
                NULLIF(COUNT(DISTINCT do.uuid_order), 0) * 100
            )::DECIMAL(5,2), 0) as delivery_success_rate,
            COALESCE((
                COUNT(CASE WHEN pgd.latitude IS NOT NULL AND pgd.longtitude IS NOT NULL THEN 1 END)::DECIMAL /
                NULLIF(COUNT(DISTINCT pgd.id_gps_driver), 0) * 100
            )::DECIMAL(5,2), 0) as gps_active_ratio,
            COALESCE(rd.status_aktif, 'UNKNOWN') as rekening_status,
            COALESCE((
                COALESCE(AVG(r.rating)::DECIMAL(3,2), 0) * 0.30 +
                (COALESCE((
                    COUNT(CASE WHEN do.status_delivery = 'DELIVERED' THEN 1 END)::DECIMAL / 
                    NULLIF(COUNT(DISTINCT do.uuid_order), 0) * 100
                )::DECIMAL(5,2), 0) / 100 * 5) * 0.40 +
                (COALESCE((
                    COUNT(CASE WHEN pgd.latitude IS NOT NULL AND pgd.longtitude IS NOT NULL THEN 1 END)::DECIMAL /
                    NULLIF(COUNT(DISTINCT pgd.id_gps_driver), 0) * 100
                )::DECIMAL(5,2), 0) / 100 * 5) * 0.30
            )::DECIMAL(3,2), 0) as kpi_score
            
        FROM public.driver_armada da
        LEFT JOIN public.rating r ON da.uuid_user = r.uuid_user 
            AND r.timestamps >= NOW() - INTERVAL '30 days'
        LEFT JOIN public.delivery_order do ON da.uuid_user = do.uuid_user
            AND do.tanggal_kirim >= NOW() - INTERVAL '30 days'
        LEFT JOIN public.perangkat_gps_driver pgd ON da.uuid_user = pgd.uuid_user
        LEFT JOIN public.rekening_driver rd ON da.uuid_user = rd.uuid_user
            
        GROUP BY da.uuid_user, da.id_armada, rd.status_aktif
        
        ON CONFLICT (uuid_user, updated_at::DATE) 
        DO UPDATE SET
            avg_rating = EXCLUDED.avg_rating,
            total_delivery = EXCLUDED.total_delivery,
            delivery_success_rate = EXCLUDED.delivery_success_rate,
            gps_active_ratio = EXCLUDED.gps_active_ratio,
            kpi_score = EXCLUDED.kpi_score;
        """
        
        cursor.execute(etl_sql)
        target_conn.commit()
        logger.info(f"✅ ETL load selesai - {cursor.rowcount} rows")
        cursor.close()
        
    except Exception as e:
        logger.error(f"❌ Gagal load data: {str(e)}")
        target_conn.rollback()

def main():
    """Main function"""
    logger.info("=" * 70)
    logger.info("🚀 DIRECT DATABASE ETL SYNC")
    logger.info("=" * 70)
    
    # Test koneksi
    logger.info("\n📡 Testing Database Connections...")
    source_ok = test_connection(SOURCE_DB, "Source DB (devom.silog.co.id)")
    target_ok = test_connection(TARGET_DB, "Target DB (Airflow Local)")
    
    if not source_ok or not target_ok:
        logger.error("\n❌ Koneksi database gagal. Silakan cek kredensial:")
        logger.info("\nSource DB (Application):")
        logger.info(f"  Host: {SOURCE_DB['host']}")
        logger.info(f"  Database: {SOURCE_DB['database']}")
        logger.info(f"  User: {SOURCE_DB['user']}")
        logger.info(f"  Port: {SOURCE_DB['port']}")
        return False
    
    # Connect ke databases
    try:
        source_conn = psycopg2.connect(**SOURCE_DB)
        target_conn = psycopg2.connect(**TARGET_DB)
        
        # Create analytics table
        logger.info("\n📊 Creating analytics schema...")
        create_analytics_table(target_conn)
        
        # Load data
        logger.info("\n🔄 Executing ETL transformation...")
        load_data(target_conn, source_conn)
        
        # Validation
        logger.info("\n✅ Validasi hasil...")
        cursor = target_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM analytics.fact_driver_performance;")
        count = cursor.fetchone()[0]
        logger.info(f"✅ Total records di fact table: {count}")
        cursor.close()
        
        logger.info("\n" + "=" * 70)
        logger.info("✨ ETL Sync Selesai!")
        logger.info("=" * 70)
        
        source_conn.close()
        target_conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    main()
