# 📖 DAGs Reference

**Complete documentation of all Apache Airflow DAGs and their specifications**

---

## 📑 Table of Contents

- [Overview](#overview)
- [daily_warehouse_sync](#1-daily_warehouse_sync)
- [weather_data_fetch](#2-weather_data_fetch)
- [sync_data_from_app](#3-sync_data_from_app)
- [DAG Configuration](#dag-configuration)
- [Error Handling & Retries](#error-handling--retries)

---

## Overview

The Airflow Stack includes **3 main DAGs** that handle different aspects of data orchestration:

| DAG | Purpose | Schedule | Status |
|-----|---------|----------|--------|
| `daily_warehouse_sync` | Daily warehouse data sync from DEVOM | Every day @ 00:00 UTC | ✅ Production |
| `weather_data_fetch` | Real-time weather data collection | Every 1 hour | ✅ Production |
| `sync_data_from_app` | Application database sync | On-demand | ✅ Development |

---

## 1. daily_warehouse_sync

**Primary ETL pipeline for warehouse synchronization**

### Basic Information

```
DAG ID:           daily_warehouse_sync
Owner:            data_team
Schedule:         0 0 * * *  (Daily @ 00:00 UTC = 7:00 AM WIB)
Retry Policy:     2 retries with 5-minute interval
Catchup:          Disabled
Tags:             warehouse, daily, sync
Start Date:       January 21, 2026
```

### Purpose

Automatic daily synchronization of all data from the source DEVOM warehouse (devom.silog.co.id) to the local PostgreSQL warehouse:

- **90 business tables** (complete list in [Database Schema](DATABASE_SCHEMA.md))
- **Full-table sync** strategy (TRUNCATE + reload)
- **Batch processing** for performance (5000 rows per batch)
- **Deduplication** of exact duplicate rows
- **Status logging** for each table operation

### Data Sources

#### Source Database: devom.silog.co.id

```
Host:       devom.silog.co.id
Port:       5432 (default PostgreSQL)
Database:   om
User:       om
Password:   om (stored in code)
Protocol:   Standard PostgreSQL TCP
```

#### Target Database: Warehouse (localhost:5433)

```
Host:       localhost
Port:       5433
Database:   warehouse
User:       postgres
Password:   postgres123 (development credential)
Schema:     public (all 90 tables)
```

### Task Flow

```
┌─────────────────────────────────────────────────┐
│ START - Scheduler triggers @ 00:00 UTC         │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│ Task 1: sync_warehouse_tables (5-15 min)       │
│                                                 │
│ For each of 90 tables:                          │
│  1. Connect to devom.silog.co.id                │
│  2. TRUNCATE table in warehouse                 │
│  3. SELECT * FROM source_table                  │
│  4. INSERT INTO warehouse (batch: 5000/iter)    │
│  5. Log: "✓ table_name: N rows synced"         │
│                                                 │
│ Return: success_count, failed_count             │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│ Task 2: verify_warehouse_data (1-2 min)        │
│                                                 │
│ SELECT tablename, pg_total_relation_size(...)   │
│ FROM pg_tables WHERE schemaname='public'        │
│ (Displays sample of synced tables)              │
│                                                 │
│ Validates:                                      │
│  ✓ Tables exist in warehouse                    │
│  ✓ Show table sizes                             │
│  ✓ Confirm public schema has data               │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│ Task 3: check_company_data (< 1 min)           │
│                                                 │
│ COUNT(*) FROM information_schema.tables         │
│ WHERE table_schema='public' AND                 │
│       table_type='BASE TABLE'                   │
│                                                 │
│ Result: Shows total tables in public schema     │
│ Expected: ~90 tables synced                     │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │ DAG RUN COMPLETE    │
         │ Status: Success     │
         │ Duration: ~7 min    │
         │ Next run: +24 hours │
         └─────────────────────┘
```

### Task Details

#### Task 1: sync_warehouse_tables

**Operator:** PythonOperator  
**Duration:** 5-15 minutes (varies with data volume)  
**Purpose:** Main ETL pipeline - sync all 90 company data tables

```python
def sync_all_tables():
    """Sync all tables - iterates through TABLE_MAPPINGS dictionary"""
    
    # 1. Connect to source (devom.silog.co.id:5432)
    source_conn = psycopg2.connect(**SOURCE_DB_CONFIG)  # om/om credentials
    
    # 2. Connect to target (localhost:5433)
    target_conn = psycopg2.connect(**TARGET_DB_CONFIG)  # postgres/postgres123
    
    results = {'success': [], 'failed': []}
    
    # 3. For each table in TABLE_MAPPINGS:
    for source_table, (target_schema, target_table) in TABLE_MAPPINGS.items():
        try:
            # Clear target table
            target_cursor.execute(f"TRUNCATE TABLE {target_schema}.{target_table}")
            
            # Fetch all rows from source
            source_cursor.execute(f"SELECT * FROM {source_table}")
            rows = source_cursor.fetchall()
            
            # Batch insert (5000 rows per iteration)
            batch_size = 5000
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                target_cursor.executemany(insert_query, batch)
            
            target_conn.commit()
            results['success'].append(f"{target_table}: {len(rows)} rows")
            print(f"✓ {target_table}: {len(rows)} rows synced")
        
        except Exception as e:
            results['failed'].append(f"{target_table}: {str(e)}")
            print(f"❌ {target_table}: Error - {str(e)}")
    
    # 4. Return summary
    return {
        'success_count': len(results['success']),
        'failed_count': len(results['failed']),
    }
```

**Processing Details:**
- **Batch size:** 5,000 rows per INSERT statement
- **Strategy:** Full sync (TRUNCATE + reload all data)
- **Logging:** Each table gets individual status line
- **Error handling:** Table-level errors don't stop other tables
- **Performance:** Network I/O bound, typical 10-15 minutes for 90 tables

**90 Tables Synced (from TABLE_MAPPINGS):**

```
alert_geofence, armada_perangkat, armada_tms, atribut, atribut_produk,
attachment, attachment_armada, attachment_chat, attachment_driver,
attachment_gudang, attachment_pengembalian, attachment_perangkat,
attachment_qc, bank, chat_room, customers, daftar_user, delivery_order,
detail_do, detail_po, detail_qc, detail_sm, detail_so, driver_armada,
geofence, gudang, jenis_armada, jenis_file, jenis_insiden, jenis_notifikasi,
jenis_order, jenis_satuan, jenis_transaksi, kategori_produk, kontak_darurat,
konversi, kriteria_produk, language, language_text, laporan_darurat,
laporan_pengemudi, locations, log_aktifitas_driver, log_chat, log_panggilan,
log_perangkat, log_perjalanan_armada, log_sensor, log_service, lokasi_rak,
mata_uang, metode_pembayaran, notifikasi, order_tms, orders, parent_armada,
pembayaran_fee, pengembalian, pengingat_pemeliharaan_armada, perangkat,
perangkat_gps_driver, produk, produk_gudang, purchase_order, quality_control,
rating, rekening_driver, role, room_last_read, room_members, rute,
rute_perangkat, sales_order, satuan, status_armada, status_gudang,
status_order, status_qc, status_user, stok, stok_movement, suppliers,
tempat_istirahat_driver, tenant, units, user_role, user_tenant, weather,
z_test
```

**Failure Handling:**
- Table-level failure: Skip that table, continue with others
- DAG-level failure: Automatic retry after 5 minutes (up to 2 retries)
- Transaction rollback: Each table is independent, partial success possible

#### Task 2: verify_warehouse_data

**Operator:** BashOperator  
**Duration:** 1-2 minutes  
**Purpose:** Validate sync results - show sample of synced tables

```bash
# List first 10 tables with their sizes
PGPASSWORD='postgres123' psql -h localhost -p 5433 -U postgres -d warehouse -c "
SELECT 
    tablename as table_name,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename != 'fact_weather_hourly'
ORDER BY tablename 
LIMIT 10;
"
```

**Validation Purpose:**
- Confirms tables were created/synced in warehouse
- Shows table sizes for monitoring
- Quick sanity check that data loaded successfully

**Output Example:**
```
 table_name         |  size
────────────────────┼───────────
 alert_geofence     | 1024 kB
 armada_perangkat   | 2048 kB
 atribut            | 512 kB
 bank               | 128 kB
 customers          | 4096 kB
 ... (10 rows total)
```

#### Task 3: check_company_data

**Operator:** BashOperator  
**Duration:** < 1 minute  
**Purpose:** Count total tables synced to verify all 90 tables exist

```bash
# Count tables in public schema
PGPASSWORD='postgres123' psql -h localhost -p 5433 -U postgres -d warehouse -c "
SELECT 
    COUNT(*) as total_tables,
    'public' as schema_name
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE';
"
```

**Success Criteria:**
- `total_tables` = 90 (or close to it)
- Indicates all company data tables were synced
- Expected: 90 tables, max variance +/- 2 (if some are optional)

### Performance Metrics

#### Typical Execution Times

```
Best case:      5-8 minutes   (fast network, small tables)
Average case:   10-12 minutes (typical production)
Worst case:     20-25 minutes (slow network, large tables)
```

#### Resource Usage

```
CPU:        Low-Medium (I/O bound, minimal CPU)
Memory:     Medium (~500MB-1GB for batch processing)
Network:    High (transferring 2-5GB of data)
Disk I/O:   High (database writes)
```

#### Data Volume

```
Tables synced:           90
Estimated total rows:    500K-2M (varies per table)
Average daily volume:    10-100MB (typical)
Total warehouse size:    2-5GB (cumulative with history)
```

### Configuration

#### Default Arguments

```python
default_args = {
    'owner': 'data_team',              # Responsible team
    'retries': 2,                      # Retry failed tasks 2x
    'retry_delay': timedelta(minutes=5),  # Wait 5 min between retries
    'start_date': datetime(2026, 1, 21),  # First run date
}
```

#### Scheduling

```
Schedule:       0 0 * * *       (Cron: daily at midnight UTC)
Timezone:       UTC (default)
When in WIB:    7:00 AM         (UTC+7)
When in WITA:   8:00 AM         (UTC+8)
When in WIT:    9:00 AM         (UTC+9)

Runs daily:     Every 24 hours
```

### Code Location

```
File:           airflow/dags/daily_warehouse_sync.py
Lines:          ~300+ lines (including TABLE_MAPPINGS)
Database:       PostgreSQL (psycopg2 library)
Imports:        DAG, PythonOperator, BashOperator, psycopg2
```

### Monitoring & Alerting

#### In Airflow UI

1. **DAGs view:** See last run status (Success/Failed/Running)
2. **DAG detail:** See task execution timeline and durations
3. **Task logs:** Click failed task → Log tab to see error details
4. **Tree view:** Historical run status for past 30 days

#### Metrics to Monitor

```
✅ DAG success rate         (target: 100%, alert if < 95%)
✅ Average duration         (target: < 15 minutes, anomaly if > 25 min)
✅ Task retry rate          (target: < 5%, indicates network issues)
✅ Table sync count         (target: 90 tables, alert if < 85)
```

#### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Network timeout during fetch | DEVOM unreachable or slow | Check VPN connection, ping devom.silog.co.id, check network |
| "permission denied" for tables | Missing read permissions on source | Verify om/om user has SELECT on all tables |
| Database disk full | Warehouse storage exceeded | Delete old data or expand storage, check with sys admin |
| Memory exceeded error | Too many rows in table | Reduce batch size in code (from 5000 to 1000) |
| Long duration (>25 min) | Slow network or large tables | Check network speed with `mtr` or `iperf`, optimize query |

---

## 2. weather_data_fetch

**Real-time weather data collection from BMKG API**

### Basic Information

```
DAG ID:           weather_data_fetch
Owner:            data_team
Schedule:         0 * * * *  (Every hour: 00:00, 01:00, 02:00, ..., 23:00 UTC)
Retry Policy:     2 retries with 5-minute interval
Catchup:          Disabled
Tags:             weather, bmkg, api, realtime
Start Date:       January 21, 2026
```

### Purpose

Collect real-time weather data from **BMKG API** (Indonesian Meteorological Agency) and:

- Fetch weather data every hour for multiple locations
- Store hourly snapshots in warehouse database (weather schema)
- Track data freshness (FRESH ≤60min, WARNING 60-180min, STALE >180min)
- Detect and skip duplicate records using location + timestamp key
- Maintain 30-day rolling window (auto-delete old data)
- Calculate deduplication metrics and freshness statistics

### Data Source: BMKG API

#### BMKG Weather API Endpoint

```
Provider:               BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)
Endpoint:               https://api.bmkg.go.id/publik/prakiraan-cuaca
Request method:         GET with query parameter: ?adm4=<ADM4_CODE>
Timeout:                10 seconds per request
Response format:        JSON
Response fields:        temperature, humidity, wind speed, weather description
Timezone handling:      Asia/Jakarta (automatic in code via os.environ['TZ'])
Retry mechanism:        2 retries with 5-minute backoff
```

#### Configured Locations (ADM4 Codes)

```
ADM4: 35.78.21.1004    (Location 1 - sample city)
ADM4: 35.25.14.1010    (Location 2 - sample city)

To add more locations:
  1. Edit airflow/dags/weather_data_fetch.py
  2. Add new entry to LOCATIONS array
  3. Restart Airflow scheduler
  
Note: ADM4 is Indonesian administrative division level 4 code
```

#### Database Storage

```
Target Database:        warehouse (localhost:5433)
Target Schema:          weather
Target Table:           fact_weather_hourly
Retention:              30-day rolling window
User:                   postgres / postgres123
```

### Task Flow

```
┌──────────────────────────────────────────────┐
│ START - Scheduler triggers every hour        │
│ (00:00, 01:00, 02:00, ..., 23:00 UTC)       │
└───────────────────┬──────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────┐
│ Task 1: fetch_weather_data (30-60 sec)      │
│                                              │
│ For each location in LOCATIONS array:        │
│   1. Build URL: https://api.bmkg.go.id/...   │
│       ?adm4={adm4_code}                      │
│   2. Make HTTPS GET request (timeout: 10s)   │
│   3. Parse JSON response                     │
│   4. Extract fields: temp, humidity, wind    │
│   5. Normalize timestamp to Asia/Jakarta TZ  │
│   6. Build record dict with all fields       │
│                                              │
│ Return: List of weather records              │
│ Error handling: Retry 2x, then log warning   │
└───────────────────┬──────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────┐
│ Task 2: deduplicate_data (20-30 sec)        │
│                                              │
│ For each new record:                         │
│   1. Query existing records:                 │
│      SELECT * WHERE location=X AND           │
│      timestamp_hour=Y                        │
│   2. Compare with new data:                  │
│      - Same temp? Same humidity?             │
│   3. If 100% match: SKIP (duplicate)         │
│   4. If different: INSERT (new record)       │
│                                              │
│ SQL: INSERT ... ON CONFLICT DO NOTHING       │
│                                              │
│ Return: inserted_count, skipped_count        │
└───────────────────┬──────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────┐
│ Task 3: track_freshness (10-20 sec)         │
│                                              │
│ For each location:                           │
│   1. Query latest_timestamp = MAX(data_ts)   │
│   2. Calculate age_minutes = (NOW - latest)  │
│   3. Classify freshness:                     │
│      ≤60 minutes   → FRESH ✓                 │
│      60-180 min    → WARNING ⚠               │
│      > 180 minutes → STALE ✗                 │
│   4. Store classification in metadata        │
│   5. Log metrics: "240 FRESH, 10 WARNING"    │
│                                              │
│ Return: freshness metrics                    │
└───────────────────┬──────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────┐
│ Task 4: cleanup_old_data (5-10 sec)         │
│                                              │
│ 1. DELETE FROM weather.fact_weather_hourly   │
│    WHERE created_at < NOW() - '30 days'      │
│                                              │
│ 2. VACUUM ANALYZE weather.fact_weather_...   │
│    (Reclaim disk space)                      │
│                                              │
│ 3. Log: "Deleted N rows, freed X MB"         │
│                                              │
│ Return: deleted_count, freed_mb              │
└───────────────────┬──────────────────────────┘
                    │
                    ▼
         ┌──────────────────────────┐
         │ DAG RUN COMPLETE         │
         │ Status: Success          │
         │ Duration: ~2 minutes     │
         │ Next run: Next hour      │
         │ Total runs: 24/day       │
         └──────────────────────────┘
```

### Task Details

#### Task 1: fetch_weather_data

**Operator:** PythonOperator  
**Duration:** 30-60 seconds  
**Purpose:** Fetch latest weather data from BMKG API

```python
def fetch_weather_data():
    """Fetch weather from BMKG API for configured locations"""
    
    import requests
    from datetime import datetime
    from pytz import timezone
    
    os.environ['TZ'] = 'Asia/Jakarta'
    
    BMKG_API_BASE = "https://api.bmkg.go.id/publik/prakiraan-cuaca"
    
    LOCATIONS = [
        {'adm4': '35.78.21.1004', 'location_name': 'Lokasi 1'},
        {'adm4': '35.25.14.1010', 'location_name': 'Lokasi 2'},
    ]
    
    records = []
    
    for location in LOCATIONS:
        try:
            url = f"{BMKG_API_BASE}?adm4={location['adm4']}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Raise exception on non-200
            api_data = response.json()
            
            # Parse and extract weather data
            # ... (parsing logic)
            records.extend(parsed_records)
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching {location['adm4']}: {e}")
            # Will retry via DAG retry mechanism
            raise
    
    return records
```

**API Response Format (from BMKG):**

```json
{
  "lokasi": {
    "adm4": "35.78.21.1004",
    "kotkab": "Jakarta",
    "desa": "Sample Desa",
    "kecamatan": "Sample Kec",
    "provinsi": "DKI Jakarta"
  },
  "data": [
    {
      "cuaca": [
        [
          {"datetime": "2026-04-13T10:00:00+07:00", "t": "28.5", "hu": "72", "weather_desc": "Partly Cloudy", "ws": "4.2", "wd": "Timur"}
        ]
      ]
    }
  ]
}
```

**Error Handling:**
- Timeout (>10s): Retry 2x, then raise (DAG-level retry)
- HTTP 4xx/5xx: Log and continue with next location
- Parse error: Log warning, skip record

#### Task 2: deduplicate_data

**Operator:** PythonOperator  
**Duration:** 20-30 seconds  
**Purpose:** Prevent duplicate weather records in database

```python
def deduplicate_data():
    """Insert new weather records, skip exact duplicates"""
    
    # For each new record, check if duplicate exists:
    # Query: SELECT COUNT(*) FROM fact_weather_hourly
    #        WHERE location = ? AND
    #              EXTRACT(HOUR FROM data_timestamp) = ?
    #              AND temperature = ? AND humidity = ? ...
    
    # If 100% match exists: SKIP (don't insert)
    # If new: INSERT with ON CONFLICT DO NOTHING
    
    inserted = 0
    skipped = 0
    
    for record in new_records:
        # Check for exact match
        cursor.execute("""
            SELECT 1 FROM weather.fact_weather_hourly
            WHERE location = %s
              AND EXTRACT(HOUR FROM data_timestamp) = %s
              AND temperature_celsius = %s
              AND humidity_percent = %s
        """, (record['location'], record['hour'], record['temp'], record['humidity']))
        
        if cursor.fetchone():
            skipped += 1
        else:
            # Insert new record
            cursor.execute("""INSERT INTO weather.fact_weather_hourly (...) 
                            VALUES (...) 
                            ON CONFLICT (location, data_timestamp) DO NOTHING""")
            inserted += 1
    
    return {'inserted': inserted, 'skipped': skipped}
```

**Deduplication Logic:**

```
Key for duplicate detection:
  - location (e.g., "Jakarta")
  - timestamp_hour (e.g., "2026-04-13 10:00 UTC")
  - Optionally: all numeric fields (temp, humidity, wind)

Actions:
  - Exact match: INSERT ... ON CONFLICT DO NOTHING
  - Different values: Insert as new record (updates)
  - No data for hour: Insert (new hour)
```

#### Task 3: track_freshness

**Operator:** PythonOperator  
**Duration:** 10-20 seconds  
**Purpose:** Monitor data freshness and age

```python
def track_freshness():
    """Calculate and track weather data freshness"""
    
    query = """
    SELECT 
        location,
        MAX(data_timestamp) as latest_data,
        EXTRACT(EPOCH FROM (NOW() - MAX(data_timestamp)))/60 as age_minutes,
        CASE 
            WHEN EXTRACT(EPOCH FROM (NOW() - MAX(data_timestamp)))/60 <= 60 
                THEN 'FRESH'
            WHEN EXTRACT(EPOCH FROM (NOW() - MAX(data_timestamp)))/60 <= 180 
                THEN 'WARNING'
            ELSE 'STALE'
        END as freshness_status
    FROM weather.fact_weather_hourly
    GROUP BY location
    ORDER BY age_minutes DESC
    """
    
    results = cursor.execute(query).fetchall()
    
    # Classify and log
    fresh_count = sum(1 for r in results if r['freshness_status'] == 'FRESH')
    warning_count = sum(1 for r in results if r['freshness_status'] == 'WARNING')
    stale_count = sum(1 for r in results if r['freshness_status'] == 'STALE')
    
    print(f"Freshness Report:")
    print(f"  ✓ FRESH (≤60 min):    {fresh_count}")
    print(f"  ⚠ WARNING (60-180):  {warning_count}")
    print(f"  ✗ STALE (>180 min):   {stale_count}")
```

**Freshness Classification:**

```
Data Age       | Status        | Color  | Interpretation
────────────────────────────────────────────────────────────
≤ 60 minutes   | FRESH ✓      | GREEN  | OK - use data immediately
60-180 minutes | WARNING ⚠     | YELLOW | Acceptable - slightly old
> 180 minutes  | STALE ✗      | RED    | Alert - may be outdated
```

**Sample Output:**

```
Freshness Report:
  ✓ FRESH (≤60 min):    12 locations (100%)
  ⚠ WARNING (60-180):   0 locations (0%)
  ✗ STALE (>180 min):   0 locations (0%)
```

#### Task 4: cleanup_old_data

**Operator:** PythonOperator  
**Duration:** 5-10 seconds  
**Purpose:** Maintain storage efficiency with 30-day retention

```python
def cleanup_old_data():
    """Delete weather records older than 30 days"""
    
    delete_query = """
    DELETE FROM weather.fact_weather_hourly
    WHERE created_at < NOW() - INTERVAL '30 days'
    """
    
    cursor.execute(delete_query)
    deleted_rows = cursor.rowcount
    
    # Reclaim disk space
    vacuum_query = "VACUUM ANALYZE weather.fact_weather_hourly"
    cursor.execute(vacuum_query)
    
    print(f"Cleanup complete:")
    print(f"  - Deleted: {deleted_rows} old records")
    print(f"  - Table vacuumed and analyzed")
    print(f"  - Disk space reclaimed")
    
    return {'deleted_rows': deleted_rows}
```

**Retention Policy:**

```
Keep data:           Last 30 days (rolling window)
Delete data:         > 30 days old
Cleanup frequency:   Every hour (every DAG run)
Expected deletion:   ~1-2% per run (~50-100 rows/day typically)
Space efficiency:    ~500MB-1GB typical storage usage
```

### Performance Metrics

#### Typical Execution Times

```
Best case:      1 minute      (fast API, 2 locations, no cleanup)
Average case:   2-3 minutes   (typical production run)
Worst case:     5 minutes     (slow API, timeout retries, large cleanup)
```

#### API Rate Limits

```
Requests/hour:  Unlimited (public API, no rate limit as of last check)
Timeout:        10 seconds per request
Retry policy:   2 retries with 5-minute exponential backoff
Backoff timing: 5s, then 25s, then 5-minute wait
```

#### Data Volume

```
Records/run:          2-4 records per location per hour
Records/hour:         4-8 total (2 locations × 2-4 each)
Daily records:        100-200 (24 hours)
Monthly records:      3K-6K
Annual storage:       ~50-100MB per year
30-day storage:       ~150-300MB typical
```

### Configuration

#### Default Arguments

```python
default_args = {
    'owner': 'data_team',
    'retries': 2,                          # 2 automatic retries
    'retry_delay': timedelta(minutes=5),   # 5 minutes between retries
    'start_date': datetime(2026, 1, 21),
}
```

#### Scheduling

```
Schedule:           0 * * * *       (Cron: every hour at :00)
Actual runs:        00:00, 01:00, 02:00, ..., 23:00 UTC
Timezone:           UTC (Airflow default)
Daily runs:         24 (every hour)
Monthly runs:       720 (~24 × 30)
```

### Monitoring & Alerting

#### Metrics to Monitor

```
✅ API availability          (target: 99%+ uptime)
✅ Data freshness            (target: 100% in FRESH status)
✅ Duplicate rate            (target: < 5% skipped)
✅ Task success rate         (target: 100%)
✅ Average response time     (target: 1-2 minutes)
✅ Storage efficiency        (target: < 500MB)
```

#### Alert Conditions

| Condition | Threshold | Action |
|-----------|-----------|--------|
| API unavailable | 2 consecutive failures | Alert ops team, check BMKG status |
| Data stale | >50% in STALE status | Investigate BMKG API, network |
| Task failure | 2+ failures in 24h | Investigate logs, check connectivity |
| Storage full | >80% disk used | Archive old data or expand storage |
| High duplicate rate | >20% skipped | Investigate for clock skew |

### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "Connection refused" | BMKG API unreachable | Check network, try manual curl test |
| "Timeout after 10s" | BMKG API slow | Retry (DAG has automatic retry), adjust timeout if persistent |
| High stale count | Data collection gap | Check BMKG API health, verify network connectivity |
| Storage growing too fast | Cleanup not running | Verify task 4 executes, check database permissions |

---

## 3. sync_data_from_app

**Application database synchronization (Manual trigger)**

### Basic Information

```
DAG ID:           sync_data_from_app
Owner:            data_team
Schedule:         None (Manual trigger only)
Retry Policy:     2 retries with 5-minute interval
Status:           Development stage
Tags:             app, etl, manual
Start Date:       January 21, 2026
```

### Purpose

Sync selected tables from application database to Airflow internal database for ETL processing:

- Bridge between app DB (devom.silog.co.id) and warehouse
- Prepare data for transformation and validation
- Support on-demand data operations
- Enable data validation before warehouse sync

### Source & Target

#### Source: Application Database

```
Host:           devom.silog.co.id
Port:           5432
Database:       om
User:           om
Password:       om
Selected tables: [Configured in DAG code]
```

#### Target: Airflow Metadata Database

```
Host:           postgres (container, internal)
Port:           5432
Database:       airflow
User:           airflow
Password:       airflow
Tables:         app_* (temporary staging tables)
```

### How to Trigger

#### Method 1: Airflow UI (Recommended)

1. Open Airflow UI: http://localhost:8080
2. Navigate to **DAGs** tab
3. Find `sync_data_from_app` in the list
4. Click the **Trigger DAG** button (play icon)
5. Leave config empty or add custom parameters
6. Click **Trigger**
7. Watch the DAG run in real-time

#### Method 2: Airflow CLI

```bash
# From airflow container
airflow dags trigger sync_data_from_app

# Or from Docker Compose
docker-compose exec airflow-scheduler airflow dags trigger sync_data_from_app
```

#### Method 3: Airflow REST API

```bash
curl -X POST http://localhost:8080/api/v1/dags/sync_data_from_app/dagRuns \
  -H "Content-Type: application/json" \
  -d '{
    "conf": {}
  }'
```

### Code Location

```
File:          airflow/dags/sync_data_from_app.py
Lines:         ~300+ lines
Implementation: Direct SQL with psycopg2
Purpose:       Manual data sync for testing/validation
```

---

## DAG Configuration

### Default Arguments (All DAGs)

Every DAG has these default arguments:

```python
default_args = {
    'owner': 'data_team',              # Team responsible for DAG
    'retries': 2,                      # Automatic retries on failure
    'retry_delay': timedelta(minutes=5),   # Wait 5 min between retries
    'start_date': datetime(2026, 1, 21),   # When DAG can first run
    'catchup': False,                  # Don't backfill past dates
}
```

### Execution Configuration

```python
DAG(
    'dag_id',
    default_args=default_args,
    description='Human-readable description',
    schedule='0 0 * * *',              # Cron schedule (or None for manual)
    catchup=False,                     # No backfilling
    tags=['tag1', 'tag2'],             # For filtering in UI
    max_active_runs=1,                 # Only one run at a time
)
```

### Database Connections

DAGs use psycopg2 direct connections (hardcoded in DAG code):

```
Connection              Host                    Database    Port
────────────────────────────────────────────────────────────────────
DEVOM Source            devom.silog.co.id       om          5432
Warehouse Target        localhost:5433          warehouse   5433
Airflow Metadata        postgres (container)    airflow     5432
```

---

## Error Handling & Retries

### Retry Mechanism

**Default retry behavior (all DAGs):**

```python
retries = 2                              # Total attempts: 3 (original + 2 retries)
retry_delay = timedelta(minutes=5)      # Wait 5 minutes between retries
```

**Timeline for failed task:**

```
Time 0:00    → Task fails (Attempt 1)
Time 0:05    → Wait 5 minutes
Time 0:05    → Retry (Attempt 2)
Time 0:10    → If fails, wait 5 minutes
Time 0:15    → Retry (Attempt 3)
Time 0:20    → If still fails, mark task as FAILED
```

### Failure Scenarios

#### Scenario 1: Network timeout (Retryable)

```
❌ Attempt 1: Connection timeout to devom.silog.co.id (after 30s)
   → Wait 5 minutes
✅ Attempt 2: Connection succeeds on retry
   → Task marked SUCCESS
```

#### Scenario 2: Database locked (Self-healing)

```
❌ Attempt 1: "database is locked" error on warehouse
   → Wait 5 minutes (lock released by other transaction)
✅ Attempt 2: Lock acquired, query succeeds
   → Task marked SUCCESS
```

#### Scenario 3: Invalid data (Not retryable)

```
❌ Attempt 1: "Invalid UTF-8 in column X" error
❌ Attempt 2: Same error (retry doesn't fix this)
❌ Attempt 3: Same error
   → Task marked FAILED, requires manual investigation
```

### Monitoring Task Failures

**In Airflow UI:**

1. Go to **DAGs** tab
2. Click DAG name to view runs
3. Click DAG Run ID (date-time)
4. Look for **red** or **orange** task boxes
5. Click failed task
6. Click **Log** tab to see error details

**Common Error Messages:**

```
"could not connect to server"     → Network issue (check VPN)
"permission denied for schema"    → Database access issue (check credentials)
"out of memory"                   → Data too large for batch (reduce batch size)
"unique constraint violation"     → Duplicate data in target
"timeout after X seconds"         → Slow query or network latency
```

### Manual Recovery

If a DAG fails and auto-retry doesn't help:

#### Option 1: Trigger DAG again

```bash
airflow dags trigger daily_warehouse_sync
```

#### Option 2: Clear and retry failed task

```bash
# In Airflow UI:
# DAGs → Click DAG → DAG Runs → Click run → Task → Clear

# Then retrigger:
airflow dags trigger daily_warehouse_sync
```

#### Option 3: Clear entire DAG run (Start over)

```bash
# Remove all task records for this DAG
airflow dags clear daily_warehouse_sync --confirm

# Retrigger
airflow dags trigger daily_warehouse_sync
```

---

📖 **Next:** Review [Architecture Guide](ARCHITECTURE.md) for system design  
📖 **Also see:** [Database Schema](DATABASE_SCHEMA.md) for table details  
👈 **Back to:** [Main README](../README.md)
