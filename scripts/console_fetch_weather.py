#!/usr/bin/env python3
"""
Console-based Weather Data Fetch Script
Alternative untuk fetch data cuaca - jalankan sebagai script console

Mengambil data dari BMKG API dan output ke JSON
Ini adalah alternatif console script dari fetch_weather_bmkg.py

Lokasi:
- Keputih, Surabaya: ADM4 35.78.09.1001
- Kebomas, Gresik: ADM4 35.25.14.1010

Output: JSON format dengan struktur records
"""

import json
import sys
from datetime import datetime
from pytz import timezone

try:
    import requests
except ImportError:
    print("❌ Error: Missing required module (requests)", file=sys.stderr)
    print("   Install with: pip install requests", file=sys.stderr)
    sys.exit(1)

# Set timezone to Jakarta
jakarta_tz = timezone('Asia/Jakarta')

# BMKG API Configuration
BMKG_API_BASE = "https://api.bmkg.go.id/publik/prakiraan-cuaca"

# PostgreSQL Connection - Scrapping Fetch Database
DB_CONFIG = {
    'host': 'localhost',
    'database': 'scrapping_fetch',
    'user': 'rafie',
    'password': '123',
}

# Lokasi yang akan di-fetch dari API BMKG
LOCATIONS = {
    '35.78.09.1001': {
        'kotkab': 'Kota Surabaya',
        'kecamatan': 'Sukolilo',
        'desa': 'Keputih',
        'provinsi': 'Jawa Timur'
    },
    '35.25.14.1010': {
        'kotkab': 'Kabupaten Gresik',
        'kecamatan': 'Kebomas',
        'desa': 'Kebomas',
        'provinsi': 'Jawa Timur'
    }
}


def fetch_weather_from_api(adm4):
    """
    Fetch weather data dari BMKG API
    
    Args:
        adm4: ADM4 code
    
    Returns:
        dict: JSON response dari BMKG API atau None jika gagal
    """
    try:
        url = f"{BMKG_API_BASE}?adm4={adm4}"
        print(f"📍 Fetching from API: {adm4}", file=sys.stderr)
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return data
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching from BMKG API: {e}", file=sys.stderr)
        return None


def parse_weather_data(api_data, adm4, location_info):
    """
    Parse BMKG API response dan extract weather forecasts
    Returns list of parsed weather records
    """
    records = []
    jakarta_tz_obj = timezone('Asia/Jakarta')
    
    try:
        # Get location info dari API
        if 'lokasi' in api_data:
            lokasi_info = api_data['lokasi']
        else:
            lokasi_info = {}
        
        adm4_code = lokasi_info.get('adm4', adm4)
        lokasi_name = lokasi_info.get('kotkab', location_info['kotkab'])
        desa = lokasi_info.get('desa', location_info['desa'])
        kecamatan = lokasi_info.get('kecamatan', location_info['kecamatan'])
        kabupaten = lokasi_info.get('kotkab', location_info['kotkab'])
        provinsi = lokasi_info.get('provinsi', location_info['provinsi'])
        
        # BMKG data structure
        if 'data' not in api_data or not api_data['data']:
            print(f"⚠️  No data in API response for {adm4}", file=sys.stderr)
            return records
        
        for data_item in api_data['data']:
            cuaca_array = data_item.get('cuaca', [])
            
            # cuaca is array of arrays
            for time_group in cuaca_array:
                if isinstance(time_group, list):
                    for weather_item in time_group:
                        # Convert UTC timestamp to Asia/Jakarta timezone
                        waktu_utc_str = weather_item.get('datetime')
                        if waktu_utc_str:
                            try:
                                waktu_utc = datetime.fromisoformat(waktu_utc_str.replace('Z', '+00:00'))
                                waktu_local = waktu_utc.astimezone(jakarta_tz_obj)
                                waktu = waktu_local.strftime('%Y-%m-%d %H:%M:%S')
                            except Exception as e:
                                print(f"⚠️  Warning: Could not convert datetime {waktu_utc_str}: {e}", file=sys.stderr)
                                waktu = waktu_utc_str
                        else:
                            waktu = None
                        
                        suhu = weather_item.get('t')
                        kelembapan = weather_item.get('hu')
                        cuaca_desc = weather_item.get('weather_desc')
                        kecepatan_angin = weather_item.get('ws')
                        arah_angin = weather_item.get('wd')
                        
                        record = {
                            'adm4': adm4_code,
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
                            'timestamp_fetched': datetime.now(jakarta_tz_obj).isoformat()
                        }
                        records.append(record)
    
    except Exception as e:
        print(f"❌ Error parsing weather data: {e}", file=sys.stderr)
    
    return records


def fetch_weather_console(adm4_list=None):
    """
    Fetch weather data dari BMKG API (console script wrapper)
    
    Args:
        adm4_list: List of ADM4 codes to fetch. Defaults to all available
    
    Returns:
        dict: Weather data untuk semua lokasi
    """
    if adm4_list is None:
        adm4_list = list(LOCATIONS.keys())
    
    result = {
        'status': 'success',
        'timestamp_fetched': datetime.now(jakarta_tz).isoformat(),
        'source': 'console_script_bmkg_api',
        'records': []
    }
    
    for adm4 in adm4_list:
        if adm4 not in LOCATIONS:
            print(f"⚠️  ADM4 {adm4} not found in configuration", file=sys.stderr)
            continue
        
        location_info = LOCATIONS[adm4]
        
        # Fetch dari API
        api_data = fetch_weather_from_api(adm4)
        if not api_data:
            continue
        
        # Parse data
        records = parse_weather_data(api_data, adm4, location_info)
        print(f"✓ Parsed {len(records)} records from {location_info['kotkab']}", file=sys.stderr)
        
        result['records'].extend(records)
    
    return result


def parse_console_data(console_data):
    """
    Extract records dari console data
    
    Args:
        console_data: Output dari fetch_weather_console()
    
    Returns:
        list: List of weather records
    """
    return console_data.get('records', [])


def main():
    """
    Main function - fetch dan output data dalam format JSON
    
    Console script untuk fetch data cuaca dari BMKG API
    Bisa dijalankan sebagai: python3 console_fetch_weather.py
    
    Output: JSON format dengan list of records
    """
    print("=" * 60, file=sys.stderr)
    print("🌦️  BMKG Weather Data - Console Script Version", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("Source: BMKG API (Prakiraan Cuaca)", file=sys.stderr)
    print("Locations: Keputih Surabaya, Kebomas Gresik", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    # Fetch data
    console_data = fetch_weather_console()
    print(f"✓ Total records fetched: {len(console_data['records'])}", file=sys.stderr)
    
    if console_data['status'] != 'success':
        print(f"❌ Error: {console_data.get('error', 'Unknown error')}", file=sys.stderr)
        sys.exit(1)
    
    # Output as JSON to stdout
    output = {
        'status': 'success',
        'timestamp_fetched': console_data['timestamp_fetched'],
        'source': console_data['source'],
        'records_count': len(console_data['records']),
        'records': console_data['records']
    }
    
    # Print JSON to stdout
    print(json.dumps(output, indent=2, default=str))
    
    return len(console_data['records'])


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
