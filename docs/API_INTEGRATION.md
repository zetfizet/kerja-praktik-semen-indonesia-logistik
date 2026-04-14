# 📖 API Integration & Data Sources

**External APIs and data source documentation**

---

## 📑 Table of Contents

- [BMKG Weather API](#bmkg-weather-api)
- [DEVOM Warehouse Connection](#devom-warehouse-connection)
- [Data Source Reliability](#data-source-reliability)
- [Integration Best Practices](#integration-best-practices)

---

## BMKG Weather API

### Overview

**Provider:** BMKG (Badan Meteorologi, Klimatologi, dan Geofisika - Indonesian Meteorological Agency)  
**Type:** Public REST API  
**License:** Open Public Data  
**Coverage:** Indonesia-wide (50+ administrative divisions)  
**Data Retention:** Real-time + 30-day rolling window (in warehouse)  
**Cost:** Free (no authentication required)

### API Endpoint Details

#### Main Weather Forecast Endpoint

```http
GET https://api.bmkg.go.id/publik/prakiraan-cuaca
    ?adm4={ADM4_CODE}
```

**Parameters:**

```
adm4              Required - ADM4 location code (Indonesian administrative level 4)
                  Example: "35.78.21.1004" (Jakarta area)
                  Others: "35.25.14.1010", "35.09.15.1001", etc.
```

**Request Headers:**

```
Content-Type: application/json (if POST)
Timeout: 10 seconds (recommended)
```

**Response Format:** JSON

### API Response Structure

#### Sample Response

```json
{
  "lokasi": {
    "adm4": "35.78.21.1004",
    "adm3": "35.78",
    "adm2": "35",
    "adm1": "DKI Jakarta",
    "province": "DKI Jakarta",
    "kotkab": "Jakarta Pusat",
    "kecamatan": "Menteng",
    "desa": "Cideng"
  },
  "data": [
    {
      "cuaca": [
        [
          {
            "datetime": "2026-04-13T10:00:00+07:00",
            "t": "28.5",
            "hu": "72",
            "weather_desc": "Partly Cloudy",
            "trend": "Meningkat",
            "ws": "4.2",
            "wd": "Timur",
            "wd_desc": "East",
            "wind_pressure": "1012"
          }
        ]
      ]
    }
  ]
}
```

**Response Fields:**

```
lokasi.adm4                   - Administrative division code (level 4)
lokasi.kotkab                 - City/regency name
lokasi.kecamatan              - Sub-district name
lokasi.desa                   - Village name
lokasi.province               - Province name

data[0].cuaca[0][0].datetime  - Forecast timestamp (ISO 8601)
data[0].cuaca[0][0].t         - Temperature (Celsius)
data[0].cuaca[0][0].hu        - Humidity (percentage: 0-100)
data[0].cuaca[0][0].cuaca     - Weather description (in Indonesian)
data[0].cuaca[0][0].weather_desc  - Weather in English
data[0].cuaca[0][0].ws        - Wind speed (km/h)
data[0].cuaca[0][0].wd        - Wind direction (abbreviation)
data[0].cuaca[0][0].wind_pressure  - Atmospheric pressure (hPa)
```

### Configured Locations in DAG

The `weather_data_fetch` DAG is configured to fetch data for these locations:

```python
LOCATIONS = [
    {
        'adm4': '35.78.21.1004',
        'location_name': 'Lokasi 1 (Jakarta)',
        'desa': '',
        'kecamatan': '',
        'kabupaten': '',
        'provinsi': ''
    },
    {
        'adm4': '35.25.14.1010',
        'location_name': 'Lokasi 2 (Bandung)',
        'desa': '',
        'kecamatan': '',
        'kabupaten': '',
        'provinsi': ''
    }
]
```

### Common ADM4 Codes (Reference)

```
Jakarta Area:
  35.78.21.1004 - Jakarta Pusat
  35.78.14.1001 - Jakarta Utara
  35.78.12.1001 - Jakarta Barat
  35.78.71.1001 - Jakarta Timur
  35.78.72.1001 - Jakarta Selatan

West Java:
  35.25.14.1010 - Bandung
  35.34.12.1001 - Bekasi
  35.16.14.1005 - Bogor

Other Major Cities:
  35.09.15.1001 - Semarang (Central Java)
  35.02.13.1010 - Surabaya (East Java)
  36.01.14.1003 - Medan (North Sumatra)
```

### Rate Limits & Performance

```
Requests per hour:    Unlimited (as of last update)
Timeout per request:  30 seconds (DAG uses 10s timeout)
Concurrent requests:  Unlimited
Response size:        ~2-5KB typical
Avg response time:    500-2000ms
```

### Error Responses

#### HTTP 200 OK (Success)

```json
{
  "status": "success",
  "data": { ... }
}
```

#### HTTP 404 Not Found

```json
{
  "status": "error",
  "message": "ADM4 code not found"
}
```

#### HTTP 500 Server Error

```json
{
  "status": "error",
  "message": "Internal server error"
}
```

### Error Handling in DAG Code

```python
def fetch_weather_from_bmkg(adm4):
    """Fetch weather data from BMKG API with retry logic"""
    try:
        url = f"{BMKG_API_BASE}?adm4={adm4}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise exception on non-200
        return response.json()
    
    except requests.exceptions.Timeout:
        print(f"⏱️ Timeout fetching {adm4}")
        raise  # Will trigger DAG-level retry
    
    except requests.exceptions.ConnectionError:
        print(f"🔌 Connection error for {adm4}")
        raise
    
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP error {e.response.status_code}: {e}")
        raise
    
    except Exception as e:
        print(f"❌ Error fetching from BMKG API: {e}")
        return None
```

### Data Deduplication Strategy

```sql
-- BMKG data is deduplicated using:
INSERT INTO weather.fact_weather_hourly (...)
VALUES (...)
ON CONFLICT (adm4, waktu) DO UPDATE SET
    suhu_celsius = EXCLUDED.suhu_celsius,
    kelembapan = EXCLUDED.kelembapan,
    ...
```

**Deduplication Key:** `(adm4, waktu)` - Location + Timestamp

**Logic:**
- If same location + time exists: UPDATE with new values (in case forecast updated)
- If new location + time: INSERT as new record

### Testing BMKG API

#### Command Line Test

```bash
# Quick test of API connectivity
curl -s "https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4=35.78.21.1004" | jq '.lokasi.kotkab, .data[0].cuaca[0][0]'

# Expected output (2 lines):
# "Jakarta Pusat"
# {"datetime": "2026-...", "t": "28.5", "hu": "72", ...}
```

#### Python Test

```python
import requests
import json

adm4 = "35.78.21.1004"
url = f"https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={adm4}"

try:
    response = requests.get(url, timeout=10)
    data = response.json()
    print(f"Status: {response.status_code}")
    print(f"Location: {data['lokasi']['kotkab']}")
    print(f"Latest reading:")
    print(json.dumps(data['data'][0]['cuaca'][0][0], indent=2))
except Exception as e:
    print(f"Error: {e}")
```

---

## DEVOM Warehouse Connection

### Connection Details

```
Host:               devom.silog.co.id
Port:               5432 (PostgreSQL default)
Database:           om
User:               om
Password:           om
SSL/TLS:            Standard PostgreSQL protocol
```

### Connection Methods

#### Direct psycopg2 Connection (Used in DAGs)

```python
import psycopg2

conn = psycopg2.connect(
    host='devom.silog.co.id',
    port=5432,
    database='om',
    user='om',
    password='om'
)
```

#### From Command Line

```bash
psql -h devom.silog.co.id -U om -d om -p 5432
```

#### From Docker Container

```bash
docker-compose exec airflow-scheduler bash
psql -h devom.silog.co.id -U om -d om -p 5432
```

### Database Structure

**Available Schemas:**
```sql
-- See all schemas
SELECT schema_name FROM information_schema.schemata;

-- List tables in public schema
SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;
```

**90 Tables Synced by daily_warehouse_sync:**

See [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) for complete list of all 90 tables.

### Data Volume & Performance

```
Total size:               2-5GB (~2-3GB typical)
Estimated row count:      500K - 2M total
Largest tables:           delivery_order, detail_*, log_* (100K-500K rows)
Daily data growth:        10-100MB
Sync strategy:            Full sync (not incremental)
Typical sync time:        10-15 minutes for all 90 tables
```

### Connectivity Test

#### Test from Airflow Container

```bash
docker-compose exec airflow-scheduler bash
nc -zv devom.silog.co.id 5432  # Test connectivity
psql -h devom.silog.co.id -U om -d om -c "SELECT count(*) FROM customers;"
```

#### Using SQL to Verify

```sql
-- Count records in a sample table
SELECT COUNT(*) as total_customers FROM public.customers;

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
```

### Connection Issues & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "could not translate host name" | DNS resolution failure | Check network, try IP directly, verify VPN |
| "connection refused" | Host unreachable or port closed | Check firewall, verify port 5432, ping host |
| "password authentication failed" | Wrong credentials | Verify om/om username and password |
| "timeout waiting for connection" | Network latency | Check network speed, try with longer timeout |
| "SSL/TLS connection refused" | SSL mismatch | DEVOM uses standard protocol, not SSL |

---

## Data Source Reliability

### BMKG API Reliability

**Uptime SLA:** ~99%+ (public weather service)

**Known Issues:**

```
Maintenance window:     Occasional (typically announced on BMKG website)
Data update frequency:  Updated regularly (2-6 hour intervals)
Data lag:               0-30 minutes typical (forecast data)
Geographic coverage:    50+ Indonesian locations
```

**Monitoring:**

```sql
-- Check data freshness in warehouse
SELECT 
    location,
    MAX(data_timestamp) as latest_data,
    EXTRACT(EPOCH FROM (NOW() - MAX(data_timestamp)))/60 as age_minutes,
    CASE 
        WHEN EXTRACT(EPOCH FROM (NOW() - MAX(data_timestamp)))/60 <= 60 THEN 'FRESH'
        WHEN EXTRACT(EPOCH FROM (NOW() - MAX(data_timestamp)))/60 <= 180 THEN 'WARNING'
        ELSE 'STALE'
    END as freshness_status
FROM weather.fact_weather_hourly
GROUP BY location
ORDER BY age_minutes DESC;
```

### DEVOM Warehouse Reliability

**Uptime SLA:** ~99% (production database)

**Known Issues:**

```
Backup window:      Daily ~02:00-04:00 WIB (possible slowdown)
Peak hours:         08:00-11:00 WIB (higher load)
Max connections:    Limited (may need connection pooling)
```

**Health Check:**

```sql
-- Check DEVOM database status
SELECT 
    datname,
    numbackends as active_connections,
    xact_commit as transactions_committed,
    xact_rollback as transactions_rolled_back,
    tup_returned as tuples_returned,
    tup_fetched as tuples_fetched
FROM pg_stat_database
WHERE datname = 'om';
```

---

## Integration Best Practices

### Error Handling Pattern

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),           # Max 3 attempts
    wait=wait_exponential(multiplier=1, min=4, max=10)  # Exponential backoff
)
def fetch_from_api(url):
    """Fetch with automatic retry on failure"""
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()

try:
    data = fetch_from_api(url)
except Exception as e:
    logger.warning(f"Failed to fetch data: {e}")
    # Fallback strategy here
```

### Graceful Degradation

```python
# If external data unavailable, continue with cached data
try:
    new_data = fetch_from_source()
except Exception as e:
    logger.warning(f"Failed to fetch new data: {e}")
    # Try cache/fallback
    new_data = get_from_cache()
    if not new_data:
        logger.error("Cache also empty, cannot proceed")
        raise
```

### Connection Pooling (PostgreSQL)

```python
from sqlalchemy import create_engine

engine = create_engine(
    'postgresql://postgres:postgres123@localhost:5433/warehouse',
    pool_size=10,              # Connections to keep ready
    max_overflow=20,           # Additional connections if needed
    pool_recycle=3600,         # Recycle connections after 1 hour
    pool_pre_ping=True,        # Verify connection before using
)

# Use engine for queries
with engine.connect() as connection:
    result = connection.execute("SELECT * FROM table")
```

### Data Validation Pattern

```python
def validate_weather_record(record):
    """Validate BMKG weather data before storing"""
    
    # Check required fields
    required = ['adm4', 'lokasi', 'waktu', 'suhu_celsius', 'kelembapan']
    for field in required:
        if field not in record or record[field] is None:
            raise ValueError(f"Missing required field: {field}")
    
    # Check value ranges (sensible boundaries)
    assert -30 <= float(record['suhu_celsius']) <= 55, \
        f"Temperature out of range: {record['suhu_celsius']}"
    assert 0 <= int(record['kelembapan']) <= 100, \
        f"Humidity out of range: {record['kelembapan']}"
    
    # Check timestamp format
    from datetime import datetime
    datetime.fromisoformat(record['waktu'])  # Raises if invalid
    
    return True
```

### Monitoring & Alerting

**Key Metrics to Monitor:**

```
API Availability:       % of successful requests (target: 99%+)
Data Freshness:         % of FRESH records (target: 95%+)
Duplicate Rate:         % of duplicate records skipped (target: < 5%)
Task Success Rate:      % of DAG runs succeeding (target: 100%)
Average Response Time:  API response time (target: < 2sec)
```

**Alert Rules:**

```
IF API_AVAILABILITY < 95% AND duration > 1 hour
  THEN alert: "BMKG API down or very slow"

IF FRESHNESS < 50% (>50% STALE records)
  THEN alert: "Weather data not being updated"

IF DUPLICATE_RATE > 20%
  THEN alert: "High duplicate rate, check for clock skew"

IF TASK_FAILURES > 3 in 24h
  THEN alert: "Frequent sync failures"
```

### Batch Processing

```python
def batch_insert(data, batch_size=5000):
    """Insert data in batches for better performance"""
    
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        
        stmt = """
            INSERT INTO table (col1, col2) VALUES (%s, %s)
            ON CONFLICT(...) DO NOTHING
        """
        
        cursor.executemany(stmt, batch)
        conn.commit()
        
        print(f"Inserted batch {i//batch_size + 1}: {len(batch)} rows")
```

### Rate Limiting & Throttling

```python
from datetime import datetime, timedelta
from time import sleep

def rate_limited_api_call(url, max_calls_per_hour=1000):
    """Make API call with rate limiting"""
    
    call_times = []
    now = datetime.now()
    
    # Remove old calls outside 1-hour window
    call_times = [t for t in call_times if t > now - timedelta(hours=1)]
    
    if len(call_times) >= max_calls_per_hour:
        # Need to wait
        oldest = min(call_times)
        wait_seconds = (oldest + timedelta(hours=1) - now).total_seconds()
        print(f"Rate limit reached, waiting {wait_seconds}s")
        sleep(wait_seconds)
    
    # Make call
    response = requests.get(url)
    call_times.append(datetime.now())
    return response.json()
```

---

📖 **Next:** Review [Database Schema](DATABASE_SCHEMA.md) for data structure  
👈 **Back to:** [Main README](../README.md)
