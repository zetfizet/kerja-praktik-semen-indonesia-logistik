"""
Fetch Weather Data from BMKG API
Indonesian Meteorological and Climatological Agency (Badan Meteorologi, Klimatologi, dan Geofisika)

API Specification:
- Service: BMKG Public API - Prakiraan Cuaca Kelurahan/Desa
- Coverage: All villages/subdistricts in Indonesia
- Forecast Horizon: 3 days (72 hours)
- Data Interval: Every 3 hours (8 forecasts per day)
- Update Frequency: 2 times daily
- Location Code: Administrative region level IV (ADM4)
- Example: Kemayoran = 31.71.03.1001
- Data Format: JSON
- Rate Limit: 60 requests/minute/IP
- Attribution: Data source BMKG (must be mentioned)

Reference: https://www.bmkg.go.id/
API Reference: https://api.bmkg.go.id/publik/prakiraan-cuaca
Regulation: Keputusan Menteri Dalam Negeri Nomor 100.1.1-6117 Tahun 2022
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
    """
    Fetch weather data from BMKG API
    
    Data converted from UTC to Asia/Jakarta timezone (WIB)
    
    Args:
        adm4: Administrative region level IV code
        Example: 35.78.21.1004 (Dukuh Pakis, Kota Surabaya)
    
    Returns:
        dict: JSON response from BMKG API
    """
    try:
        url = f"{BMKG_API_BASE}?adm4={adm4}"
        print(f"Fetching from: {url}")
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return data
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching from BMKG API: {e}")
        return None

def parse_weather_data(api_data, location_info):
    """
    Parse BMKG API response and extract weather forecasts
    Returns list of parsed weather records
    """
    records = []
    
    try:
        # Get location info from API response
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
        
        # BMKG data structure: {'data': [{'cuaca': [[{...}, {...}]]}]}
        if 'data' not in api_data or not api_data['data']:
            print(f"⚠️ No data in API response for {adm4}")
            return records
        
        for data_item in api_data['data']:
            cuaca_array = data_item.get('cuaca', [])
            
            # cuaca is array of arrays
            for time_group in cuaca_array:
                if isinstance(time_group, list):
                    # Get last forecast in the group
                    for weather_item in time_group:
                        # Convert UTC timestamp to Asia/Jakarta timezone
                        waktu_utc_str = weather_item.get('datetime')
                        if waktu_utc_str:
                            try:
                                # Parse ISO format UTC datetime (e.g., "2026-01-30T04:00:00Z")
                                waktu_utc = datetime.fromisoformat(waktu_utc_str.replace('Z', '+00:00'))
                                # Convert to Jakarta timezone
                                waktu_local = waktu_utc.astimezone(jakarta_tz)
                                # Format as string without timezone info (for DB storage)
                                waktu = waktu_local.strftime('%Y-%m-%d %H:%M:%S')
                            except Exception as e:
                                print(f"⚠️ Warning: Could not convert datetime {waktu_utc_str}: {e}")
                                waktu = waktu_utc_str
                        else:
                            waktu = None
                        
                        suhu = weather_item.get('t')  # Temperature
                        kelembapan = weather_item.get('hu')  # Humidity
                        cuaca_desc = weather_item.get('weather_desc')
                        kecepatan_angin = weather_item.get('ws')  # Wind speed
                        arah_angin = weather_item.get('wd')  # Wind direction
                        
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

def decode_weather_code(code):
    """
    Decode BMKG weather codes to description
    """
    weather_codes = {
        '0': 'Cerah',
        '1': 'Cerah Berawan',
        '2': 'Berawan',
        '3': 'Berawan Tebal',
        '4': 'Berkabut',
        '5': 'Hujan Ringan',
        '10': 'Hujan Sedang',
        '11': 'Hujan Lebat',
        '12': 'Hujan Lebat Berlanjut',
        '13': 'Hujan Sangat Lebat',
        '20': 'Hujan Ringan Berawan',
        '25': 'Hujan Petir',
        '26': 'Hujan Petir Berlanjut',
        '30': 'Cerah Dingin',
        '31': 'Cerah Berawan Dingin',
        '32': 'Berawan Dingin',
        '33': 'Berawan Tebal Dingin',
        '40': 'Kabut Tipis',
        '41': 'Kabut',
        '45': 'Kabut Tebal',
        '50': 'Drizzle',
        '55': 'Hujan Gerimis',
        '60': 'Hujan Ringan Terputus',
        '61': 'Hujan Ringan Terputus Berawan',
        '63': 'Hujan Sedang Terputus',
        '65': 'Hujan Lebat Terputus',
        '80': 'Hujan Ringan Menyeluruh',
        '81': 'Hujan Sedang Menyeluruh',
        '82': 'Hujan Lebat Menyeluruh',
        '85': 'Hujan Petir Menyeluruh',
        '90': 'Tornado',
        '91': 'Puting Beliung'
    }
    return weather_codes.get(str(code), f'Unknown ({code})')

def insert_weather_data(records):
    """
    Insert weather data into PostgreSQL
    """
    if not records:
        print("⚠️ No records to insert")
        return 0
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check dan preview data yang akan dihapus
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
        
        # DELETE data cuaca yang sudah lewat (waktu < NOW)
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
        
        # Insert or Update records (UPSERT for deduplication)
        insert_count = 0
        update_count = 0
        for record in records:
            try:
                cursor.execute("""
                    INSERT INTO weather.fact_weather_hourly (
                        adm4, lokasi, desa, kecamatan, kabupaten, provinsi,
                        waktu, cuaca, suhu_celsius, kelembapan, arah_angin, kecepatan_angin,
                        created_at, last_updated, data_age_minutes, freshness_status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                        last_updated = EXCLUDED.last_updated,
                        freshness_status = 'FRESH'
                    RETURNING xmax = 0 as is_insert
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
                    record['timestamp_fetched'],
                    record['timestamp_fetched'],
                    0,  # data_age_minutes
                    'FRESH'
                ))
                
                result = cursor.fetchone()
                if result and result[0]:  # xmax = 0 means INSERT
                    insert_count += 1
                else:  # UPDATE
                    update_count += 1
            
            except psycopg2.Error as e:
                print(f"⚠️ Error inserting/updating record: {e}")
                conn.rollback()
                continue
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✓ Inserted {insert_count} new weather records")
        print(f"✓ Updated {update_count} existing records (deduplication)")
        print(f"\n📌 Data Source: BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)")
        print(f"   Timestamp: Converted to Asia/Jakarta (WIB)")
        return insert_count + update_count
    
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return 0

def create_weather_table_if_not_exists():
    """
    Create weather table if it doesn't exist
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'weather' AND table_name = 'fact_weather_hourly'
            )
        """)
        
        if not cursor.fetchone()[0]:
            # Create table
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

def main():
    """
    Main function to fetch and store weather data
    
    Fetches weather forecasts from BMKG Public API for Indonesia
    - Forecast Horizon: 3 days
    - Update Interval: Every 3 hours
    - Timezone: Asia/Jakarta (WIB)
    """
    print("=" * 60)
    print("🌦️  BMKG Weather Data Fetch (Prakiraan Cuaca)")
    print("=" * 60)
    print(f"Data Source: BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)")
    print(f"URL: https://api.bmkg.go.id/publik/prakiraan-cuaca")
    print(f"Timezone: Asia/Jakarta (UTC+7, WIB)")
    print("=" * 60)
    
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

if __name__ == '__main__':
    main()
