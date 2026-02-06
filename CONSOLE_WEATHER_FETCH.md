# Console-based Weather Fetch DAG

**Tanggal Setup**: 30 Januari 2026  
**Status**: ✅ Working dan Tested  
**Purpose**: Alternative weather data fetch menggunakan console script (sebagai testing)

---

## 📋 Overview

Alternatif dari `weather_data_fetch.py` DAG yang menggunakan BMKG API langsung. DAG ini menjalankan `console_fetch_weather.py` sebagai console script, kemudian menyimpan hasilnya ke database yang sama.

**Kesamaan dengan API DAG:**
- ✅ Fetch data dari BMKG API (wrapper script)
- ✅ Output format JSON dengan struktur records sama
- ✅ Timezone conversion UTC → Asia/Jakarta
- ✅ Store ke `weather.fact_weather_hourly` table
- ✅ UPSERT deduplication (ON CONFLICT)
- ✅ Cleanup old/past records
- ✅ Freshness metrics (last_updated, data_age_minutes, freshness_status)

**Perbedaan:**
- Script dijalankan sebagai subprocess (simulasi console script)
- Data di-parse dari JSON output script
- XCom digunakan untuk pass data antar tasks

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│  console_weather_fetch.py (DAG)                         │
├─────────────────────────────────────────────────────────┤
│ Task 1: run_console_fetch                               │
│ ├─ Jalankan: python3 /opt/airflow/scripts/console_...  │
│ ├─ Input: None                                          │
│ ├─ Output: JSON dengan 42 weather records               │
│ └─ Push ke XCom: weather_data                           │
│                                                         │
│ Task 2: verify_console_data                             │
│ ├─ Pull dari XCom: weather_data                         │
│ ├─ Validate struktur records                            │
│ ├─ Count per lokasi: Surabaya (21), Gresik (21)        │
│ └─ Push count ke XCom                                   │
│                                                         │
│ Task 3: store_console_data                              │
│ ├─ Pull dari XCom: weather_data                         │
│ ├─ UPSERT ke weather.fact_weather_hourly                │
│ ├─ Deduplication: ON CONFLICT (adm4, waktu) DO UPDATE   │
│ ├─ Track: insert_count, update_count                    │
│ └─ Result: 29 inserts + 13 updates                      │
│                                                         │
│ Task 4: cleanup_old_data                                │
│ ├─ Delete waktu < NOW()                                 │
│ ├─ Keep hanya forecast masa depan                       │
│ └─ Result: 0 deletions (semua future forecasts)         │
└─────────────────────────────────────────────────────────┘
```

---

## 📂 File Locations

| File | Location | Purpose |
|------|----------|---------|
| **DAG** | `/home/rafiez/airflow-stack/dags/console_weather_fetch.py` | Airflow DAG definition |
| **Script** | `/home/rafiez/airflow-stack/scripts/console_fetch_weather.py` | Console script untuk fetch data |
| **Container DAG** | `/opt/airflow/dags/console_weather_fetch.py` | DAG dalam container |
| **Container Script** | `/opt/airflow/scripts/console_fetch_weather.py` | Script dalam container |

---

## 🔄 Data Flow

### Input
```
console_fetch_weather.py script
├─ Fetch dari BMKG API: 35.78.09.1001 (Surabaya) → 21 records
├─ Fetch dari BMKG API: 35.25.14.1010 (Gresik) → 21 records
└─ Total: 42 weather records dalam format JSON
```

### Processing
```json
{
  "status": "success",
  "timestamp_fetched": "2026-01-30T10:42:23.878709+07:00",
  "source": "console_script_bmkg_api",
  "records_count": 42,
  "records": [
    {
      "adm4": "35.78.09.1001",
      "lokasi": "Kota Surabaya",
      "desa": "Keputih",
      "kecamatan": "Sukolilo",
      "kabupaten": "Kota Surabaya",
      "provinsi": "Jawa Timur",
      "waktu": "2026-01-30 11:00:00",
      "cuaca": "Cerah",
      "suhu_celsius": 31,
      "kelembapan": 63,
      "arah_angin": "NW",
      "kecepatan_angin": 27.8,
      "timestamp_fetched": "2026-01-30T10:42:24.668057+07:00"
    },
    ...
  ]
}
```

### Output
```
weather.fact_weather_hourly table
├─ 29 new records inserted
├─ 13 existing records updated (deduplication)
├─ Timezone: Asia/Jakarta (WIB, UTC+7)
├─ Fields: adm4, lokasi, desa, kecamatan, kabupaten, provinsi, waktu, cuaca, suhu_celsius, kelembapan, arah_angin, kecepatan_angin, created_at, last_updated, data_age_minutes, freshness_status
└─ Freshness: All marked as FRESH (last_updated = NOW)
```

---

## ⏱️ Schedule

**Cron**: `0 * * * *`  
**Meaning**: Setiap jam (every 1 hour)  
**Frequency**: 24 kali sehari  
**Start**: 00:00 - 23:00 WIB

---

## 🔧 Console Script Details

### `console_fetch_weather.py`

**Location**: `/opt/airflow/scripts/console_fetch_weather.py`

**What it does:**
1. Fetches weather data dari BMKG API untuk 2 lokasi
2. Parses JSON response
3. Converts waktu dari UTC ke Asia/Jakarta timezone
4. Outputs formatted JSON dengan 42 records

**Locations:**
- `35.78.09.1001` - Keputih, Kota Surabaya, Jawa Timur
- `35.25.14.1010` - Kebomas, Kabupaten Gresik, Jawa Timur

**Data Format**:
```python
{
    'adm4': str,                    # Administrative code
    'lokasi': str,                  # Location name
    'desa': str,                    # Village
    'kecamatan': str,               # District
    'kabupaten': str,               # Regency
    'provinsi': str,                # Province
    'waktu': str,                   # Forecast time (YYYY-MM-DD HH:MM:SS)
    'cuaca': str,                   # Weather condition
    'suhu_celsius': int,            # Temperature
    'kelembapan': int,              # Humidity (%)
    'arah_angin': str,              # Wind direction
    'kecepatan_angin': float,       # Wind speed (km/h)
    'timestamp_fetched': str        # Fetch timestamp
}
```

**Run Command:**
```bash
# Manual execution
python3 /opt/airflow/scripts/console_fetch_weather.py

# Output: JSON to stdout
# Logs: stderr with progress info
```

---

## 📊 Task Details

### Task 1: `run_console_fetch`
- **Type**: PythonOperator
- **Callable**: `run_console_fetch(**context)`
- **Function**:
  1. Run subprocess: `python3 /opt/airflow/scripts/console_fetch_weather.py`
  2. Parse JSON dari stdout
  3. Validate status = "success"
  4. Push data ke XCom dengan key `weather_data`
- **Output**: dict dengan keys (status, timestamp_fetched, source, records_count, records)
- **Error Handling**: FileNotFoundError jika script tidak ada, RuntimeError jika script gagal

### Task 2: `verify_console_data`
- **Type**: PythonOperator
- **Callable**: `verify_console_data(**context)`
- **Function**:
  1. Pull data dari XCom (key: `weather_data`)
  2. Check required fields: adm4, lokasi, waktu, cuaca, suhu_celsius, kelembapan
  3. Count records per lokasi
  4. Show latest forecast waktu
  5. Raise ValueError jika struktur tidak valid
- **Output**: dict dengan verification results

### Task 3: `store_console_data`
- **Type**: PythonOperator
- **Callable**: `store_console_data(**context)`
- **Function**:
  1. Pull data dari XCom
  2. Connect ke PostgreSQL
  3. For each record:
     ```sql
     INSERT INTO weather.fact_weather_hourly (...)
     VALUES (...)
     ON CONFLICT (adm4, waktu) DO UPDATE SET (...)
     ```
  4. Count inserts vs updates
  5. Print attribution: "Data Source: BMKG"
- **Output**: Total records stored (insert_count + update_count)

### Task 4: `cleanup_old_data`
- **Type**: PythonOperator
- **Callable**: `cleanup_old_data(**context)`
- **Function**:
  1. Connect ke PostgreSQL
  2. DELETE records WHERE waktu < NOW()
  3. Log count deleted
- **Output**: Count deleted records

---

## ✅ Test Results (2026-01-30)

```
Console Weather Fetch DAG Test
================================

Task 1: run_console_fetch
✓ Script executed successfully
✓ Records fetched: 42
├─ Surabaya (35.78.09.1001): 21 records
└─ Gresik (35.25.14.1010): 21 records

Task 2: verify_console_data
✓ Total records verified: 42
✓ All required fields present
├─ Surabaya: 21 records
├─ Gresik: 21 records
✓ Sample record: waktu=2026-01-30 11:00:00, cuaca=Cerah, suhu=31°C

Task 3: store_console_data
✓ Database connection successful
✓ Inserted: 29 new records
✓ Updated: 13 existing records (deduplication)
✓ All records stored with freshness_status='FRESH'

Task 4: cleanup_old_data
✓ No expired records found
✓ All forecast records are in future
```

---

## 🔄 Comparison: API vs Console Script

| Aspect | `weather_data_fetch.py` (API) | `console_weather_fetch.py` (Script) |
|--------|------------------------------|-------------------------------------|
| **Source** | Direct API call | Console script wrapper |
| **Location** | `/opt/airflow/scripts/fetch_weather_bmkg.py` | `/opt/airflow/scripts/console_fetch_weather.py` |
| **Data retrieval** | `requests.get(BMKG_API_BASE)` | `subprocess.run(script)` |
| **Format** | API JSON response | JSON stdout |
| **Task count** | 4 (fetch, verify, freshness, cleanup) | 4 (fetch, verify, store, cleanup) |
| **Deduplication** | Yes (ON CONFLICT) | Yes (ON CONFLICT) |
| **Timezone** | UTC → Jakarta | UTC → Jakarta |
| **Database** | weather.fact_weather_hourly | weather.fact_weather_hourly (same) |
| **Schedule** | `0 * * * *` (hourly) | `0 * * * *` (hourly) |
| **Dependencies** | requests, psycopg2, pytz | requests, psycopg2, pytz |
| **Use Case** | Production (direct) | Testing (simulation) |

---

## 📝 Dependencies

**Python Packages:**
- `requests` - HTTP requests
- `psycopg2` - PostgreSQL connector
- `pytz` - Timezone handling
- `json` - JSON parsing

**External Services:**
- BMKG API: https://api.bmkg.go.id/publik/prakiraan-cuaca
- PostgreSQL: localhost:5432

**Airflow Components:**
- `PythonOperator` - Execute Python functions
- `XCom` - Inter-task communication
- DAG scheduler - Schedule setiap jam

---

## 🐛 Troubleshooting

### Error: Script not found
```
FileNotFoundError: Script not found at /opt/airflow/scripts/console_fetch_weather.py
```
**Solution:** Copy script ke container:
```bash
podman cp scripts/console_fetch_weather.py airflow-webserver:/opt/airflow/scripts/
```

### Error: ModuleNotFoundError (requests, psycopg2, pytz)
**Solution:** Modules sudah tersedia dalam Airflow container

### Error: Database connection failed
**Solution:** Check PostgreSQL:
```bash
PGPASSWORD=postgres123 psql -h localhost -U postgres -c "SELECT 1"
```

### Error: No records fetched
**Solution:** Check BMKG API availability:
```bash
curl -s "https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4=35.78.09.1001" | python3 -m json.tool
```

---

## 📚 Related Documentation

- [weather_data_fetch.py](./WEATHER_DAG_OPTIMIZATION.md) - API-based DAG
- [fetch_weather_bmkg.py](./scripts/fetch_weather_bmkg.py) - Original API script
- [Database Schema](./README.md) - Warehouse structure
- [Metabase Integration](./WEATHER_DASHBOARD_METABASE.md) - Visualization

---

## 🎯 Next Steps

1. ✅ Script created and tested
2. ✅ DAG created and tested
3. ✅ 42 records fetched successfully
4. ✅ Database storage working (29 inserts + 13 updates)
5. **Next**: Enable DAG in Airflow UI and set to active schedule

---

**Last Updated**: 30 Januari 2026, 10:42 WIB  
**Status**: ✅ Ready for deployment
