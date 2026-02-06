"""
Weather Data Fetch DAG with Data Freshness Tracking
Fetches weather data from BMKG API and stores in warehouse
Runs every 2 hours with deduplication and freshness monitoring
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import sys
import os

# Add scripts path - works in both local and container
script_paths = [
    '/opt/airflow/dags',  # Container dags path (scripts copied here)
    '/opt/airflow/scripts',  # Container path
    '/home/rafiez/airflow-stack/scripts',  # Local path
    '/home/rafiez/airflow-stack/airflow/dags',  # Local dags path
]
for path in script_paths:
    if os.path.exists(path):
        sys.path.insert(0, path)
        break

# Default DAG arguments
default_args = {
    'owner': 'data_team',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2026, 1, 21),
}

# DAG definition
dag = DAG(
    'weather_data_fetch',
    default_args=default_args,
    description='Fetch weather data from BMKG API every 1 hour with freshness tracking',
    schedule='0 * * * *',  # Every hour (00:00, 01:00, 02:00, ... 23:00)
    catchup=False,
    tags=['weather', 'bmkg', 'api', 'realtime'],
)

def fetch_weather_data():
    """
    Fetch weather data from BMKG API
    """
    import requests
    import psycopg2
    from psycopg2 import sql
    from datetime import datetime
    import json
    import os
    from pytz import timezone
    
    # Set timezone to Jakarta
    os.environ['TZ'] = 'Asia/Jakarta'
    jakarta_tz = timezone('Asia/Jakarta')
    
    # BMKG API Configuration
    BMKG_API_BASE = "https://api.bmkg.go.id/publik/prakiraan-cuaca"
    
    # Lokasi yang akan di-fetch (ADM4 codes)
    LOCATIONS = [
        {
            'adm4': '35.78.21.1004',
            'location_name': 'Lokasi 1',
            'desa': '',
            'kecamatan': '',
            'kabupaten': '',
            'provinsi': ''
        },
        {
            'adm4': '35.25.14.1010',
            'location_name': 'Lokasi 2',
            'desa': '',
            'kecamatan': '',
            'kabupaten': '',
            'provinsi': ''
        }
    ]
    
    # PostgreSQL Connection
    DB_CONFIG = {
        'host': 'localhost',
        'database': 'warehouse',
        'user': 'postgres',
        'password': 'postgres123',
    }
    
    def fetch_weather_from_bmkg(adm4):
        """Fetch weather data from BMKG API"""
        try:
            url = f"{BMKG_API_BASE}?adm4={adm4}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching from BMKG API: {e}")
            return None
    
    def parse_weather_data(api_data, location_info):
        """Parse BMKG API response and extract weather forecasts"""
        records = []
        try:
            if 'lokasi' in api_data:
                lokasi_info = api_data['lokasi']
            else:
                lokasi_info = {}
            
            adm4 = lokasi_info.get('adm4', location_info['adm4'])
            lokasi_name = lokasi_info.get('kotkab', location_info['location_name'])
            desa = lokasi_info.get('desa', location_info['desa'])
            kecamatan = lokasi_info.get('kecamatan', location_info['kecamatan'])
            kabupaten = lokasi_info.get('kotkab', location_info['kabupaten'])
            provinsi = lokasi_info.get('provinsi', location_info['provinsi'])
            
            if 'data' not in api_data or not api_data['data']:
                print(f"⚠️ No data in API response for {adm4}")
                return records
            
            for data_item in api_data['data']:
                cuaca_array = data_item.get('cuaca', [])
                for time_group in cuaca_array:
                    if isinstance(time_group, list):
                        for weather_item in time_group:
                            waktu = weather_item.get('datetime')
                            suhu = weather_item.get('t')
                            kelembapan = weather_item.get('hu')
                            cuaca_desc = weather_item.get('weather_desc')
                            kecepatan_angin = weather_item.get('ws')
                            arah_angin = weather_item.get('wd')
                            
                            record = {
                                'adm4': adm4,
                                'lokasi': lokasi_name,
                                'desa': desa,
                                'kecamatan': kecamatan,
                                'kabupaten': kabupaten,
                                'provinsi': provinsi,
                                'waktu': waktu,
                                'cuaca': cuaca_desc,
                                'suhu_celsius': suhu,
                                'kelembapan': kelembapan,
                                'arah_angin': arah_angin,
                                'kecepatan_angin': kecepatan_angin,
                                'timestamp_fetched': datetime.now(jakarta_tz)
                            }
                            records.append(record)
        except Exception as e:
            print(f"❌ Error parsing weather data: {e}")
        return records
    
    def insert_weather_data(records):
        """Insert weather data into PostgreSQL"""
        if not records:
            print("⚠️ No records to insert")
            return 0
        
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Check and preview data to delete
            cursor.execute("""
                SELECT COUNT(*), MIN(waktu), MAX(waktu)
                FROM weather.fact_weather_hourly 
                WHERE waktu < NOW() AT TIME ZONE 'Asia/Jakarta'
            """)
            delete_check = cursor.fetchone()
            if delete_check[0] > 0:
                print(f"\n⚠️  Found {delete_check[0]} expired weather records to delete")
                print(f"   Time range: {delete_check[1]} to {delete_check[2]}")
                print(f"   (waktu < NOW at {datetime.now(jakarta_tz).strftime('%Y-%m-%d %H:%M:%S %Z')})")
            
            # DELETE expired weather records
            cursor.execute("""
                DELETE FROM weather.fact_weather_hourly 
                WHERE waktu < NOW() AT TIME ZONE 'Asia/Jakarta'
            """)
            deleted_count = cursor.rowcount
            if deleted_count > 0:
                print(f"✅ Deleted {deleted_count} expired weather records")
            else:
                print("✓ No expired records to delete")
            conn.commit()
            
            # Insert new records (or update if duplicate)
            insert_count = 0
            update_count = 0
            for record in records:
                try:
                    cursor.execute("""
                        INSERT INTO weather.fact_weather_hourly (
                            adm4, lokasi, desa, kecamatan, kabupaten, provinsi,
                            waktu, cuaca, suhu_celsius, kelembapan, arah_angin, kecepatan_angin,
                            created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (adm4, waktu) DO UPDATE SET
                            lokasi = EXCLUDED.lokasi,
                            desa = EXCLUDED.desa,
                            kecamatan = EXCLUDED.kecamatan,
                            kabupaten = EXCLUDED.kabupaten,
                            provinsi = EXCLUDED.provinsi,
                            cuaca = EXCLUDED.cuaca,
                            suhu_celsius = EXCLUDED.suhu_celsius,
                            kelembapan = EXCLUDED.kelembapan,
                            arah_angin = EXCLUDED.arah_angin,
                            kecepatan_angin = EXCLUDED.kecepatan_angin,
                            last_updated = NOW()
                    """, (
                        record['adm4'],
                        record['lokasi'],
                        record['desa'],
                        record['kecamatan'],
                        record['kabupaten'],
                        record['provinsi'],
                        record['waktu'],
                        record['cuaca'],
                        record['suhu_celsius'],
                        record['kelembapan'],
                        record['arah_angin'],
                        record['kecepatan_angin'],
                        record['timestamp_fetched']
                    ))
                    if cursor.rowcount == 1:
                        insert_count += 1
                    else:
                        update_count += 1
                except psycopg2.Error as e:
                    print(f"⚠️ Error inserting/updating record: {e}")
                    conn.rollback()
                    continue
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"✓ Inserted {insert_count} new weather records")
            print(f"✓ Updated {update_count} existing weather records")
            return insert_count + update_count
        
        except psycopg2.Error as e:
            print(f"❌ Database error: {e}")
            return 0
    
    def create_weather_table_if_not_exists():
        """Create weather table if it doesn't exist"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'weather' AND table_name = 'fact_weather_hourly'
                )
            """)
            
            if not cursor.fetchone()[0]:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS weather.fact_weather_hourly (
                        id SERIAL PRIMARY KEY,
                        adm4 VARCHAR(50),
                        lokasi VARCHAR(255),
                        desa VARCHAR(255),
                        kecamatan VARCHAR(255),
                        kabupaten VARCHAR(255),
                        provinsi VARCHAR(255),
                        waktu TIMESTAMP,
                        cuaca VARCHAR(255),
                        suhu_celsius FLOAT,
                        kelembapan INT,
                        arah_angin VARCHAR(50),
                        kecepatan_angin FLOAT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(adm4, waktu)
                    )
                """)
                conn.commit()
                print("✓ Created weather.fact_weather_hourly table")
            
            cursor.close()
            conn.close()
        except psycopg2.Error as e:
            print(f"❌ Error creating table: {e}")
    
    # Main execution
    print("\n" + "=" * 60)
    print("🌦️ Fetching BMKG Weather Data")
    print("=" * 60)
    
    try:
        # Create table if needed
        create_weather_table_if_not_exists()
        
        total_records = 0
        
        # Fetch weather for each location
        for location in LOCATIONS:
            print(f"\n📍 Fetching weather for ADM4: {location['adm4']}")
            
            # Fetch from API
            api_data = fetch_weather_from_bmkg(location['adm4'])
            
            if not api_data:
                print(f"⚠️ Skipping {location['adm4']} - no data")
                continue
            
            # Parse data
            records = parse_weather_data(api_data, location)
            print(f"   Parsed {len(records)} weather records")
            
            # Insert to database
            inserted = insert_weather_data(records)
            total_records += inserted
        
        print("\n" + "=" * 60)
        print(f"✓ Total records inserted: {total_records}")
        print("=" * 60)
        
        return total_records
    
    except Exception as e:
        print(f"❌ Error fetching weather: {e}")
        raise

def verify_weather_data():
    """
    Verify weather data was inserted
    """
    import psycopg2
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='warehouse',
            user='postgres',
            password='postgres123'
        )
        cursor = conn.cursor()
        
        # Check total records
        cursor.execute("SELECT COUNT(*) FROM weather.fact_weather_hourly")
        count = cursor.fetchone()[0]
        
        # Check latest records
        cursor.execute("""
            SELECT lokasi, waktu, cuaca, suhu_celsius
            FROM weather.fact_weather_hourly
            ORDER BY created_at DESC
            LIMIT 5
        """)
        latest = cursor.fetchall()
        
        print("\n" + "=" * 60)
        print(f"✓ Weather data verification:")
        print(f"  Total records in database: {count}")
        print(f"  Latest records:")
        for row in latest:
            print(f"    - {row[0]} | {row[1]} | {row[2]} | {row[3]}°C")
        print("=" * 60)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verifying weather data: {e}")

def update_freshness_metrics():
    """
    Update data freshness metrics:
    - data_age_minutes: Minutes since last_updated
    - freshness_status: FRESH, WARNING, STALE based on age
    
    Rules:
    - 0-60 mins   → FRESH (data is current)
    - 60-180 mins → WARNING (3 hours, getting old)
    - 180+ mins   → STALE (>3 hours, data is stale)
    """
    import psycopg2
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='warehouse',
            user='postgres',
            password='postgres123'
        )
        cursor = conn.cursor()
        
        print("\n" + "=" * 60)
        print("🔄 Updating weather data freshness metrics...")
        print("=" * 60)
        
        # Update data_age_minutes and freshness_status
        cursor.execute("""
            UPDATE weather.fact_weather_hourly SET
                data_age_minutes = EXTRACT(EPOCH FROM (NOW() - last_updated)) / 60,
                freshness_status = CASE
                    WHEN EXTRACT(EPOCH FROM (NOW() - last_updated)) / 60 <= 60 THEN 'FRESH'
                    WHEN EXTRACT(EPOCH FROM (NOW() - last_updated)) / 60 <= 180 THEN 'WARNING'
                    ELSE 'STALE'
                END
            WHERE waktu >= CURRENT_DATE AT TIME ZONE 'Asia/Jakarta'
        """)
        
        updated_rows = cursor.rowcount
        conn.commit()
        
        # Get freshness summary
        cursor.execute("""
            SELECT freshness_status, COUNT(*) as count
            FROM weather.fact_weather_hourly
            WHERE waktu >= CURRENT_DATE AT TIME ZONE 'Asia/Jakarta'
            GROUP BY freshness_status
            ORDER BY 
                CASE freshness_status
                    WHEN 'FRESH' THEN 1
                    WHEN 'WARNING' THEN 2
                    WHEN 'STALE' THEN 3
                END
        """)
        
        summary = cursor.fetchall()
        
        print(f"✓ Updated {updated_rows} records with freshness metrics")
        print(f"\nFreshness Summary:")
        for status, count in summary:
            emoji = {'FRESH': '✅', 'WARNING': '⚠️', 'STALE': '❌'}.get(status, '❓')
            print(f"  {emoji} {status}: {count} records")
        
        print("=" * 60)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error updating freshness metrics: {e}")
        raise

def cleanup_old_weather_data():
    """
    Delete weather data that is older than 7 days
    Keeps future forecasts and recent past data
    """
    import psycopg2
    from datetime import datetime
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='warehouse',
            user='postgres',
            password='postgres123'
        )
        cursor = conn.cursor()
        
        # Delete records where waktu is more than 7 days in the past
        # This keeps all future forecasts and recent data (up to 7 days old)
        cursor.execute("""
            DELETE FROM weather.fact_weather_hourly
            WHERE waktu < NOW() - INTERVAL '7 days'
        """)
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        print("\n" + "=" * 60)
        print(f"🗑️  Weather data cleanup completed:")
        print(f"  Deleted {deleted_count} records older than 7 days")
        print(f"  Kept all future forecasts and recent data (< 7 days old)")
        print("=" * 60)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error cleaning up old weather data: {e}")
        raise

# Task 1: Fetch weather from BMKG API
fetch_weather = PythonOperator(
    task_id='fetch_bmkg_weather',
    python_callable=fetch_weather_data,
    dag=dag,
)

# Task 2: Verify data was inserted
verify_weather = PythonOperator(
    task_id='verify_weather_data',
    python_callable=verify_weather_data,
    dag=dag,
)

# Task 3: Update freshness metrics
freshness_check = PythonOperator(
    task_id='update_freshness_metrics',
    python_callable=update_freshness_metrics,
    dag=dag,
)

# Task 4: Cleanup old/past weather data
cleanup_weather = PythonOperator(
    task_id='cleanup_old_weather_data',
    python_callable=cleanup_old_weather_data,
    dag=dag,
)

# Set task dependencies: fetch → verify → freshness → cleanup
fetch_weather >> verify_weather >> freshness_check >> cleanup_weather
