# Weather Data Fetch DAG - Optimization Update
**Date:** January 30, 2026  
**Status:** ✅ Deployed and Active

---

## 🎯 Overview

The `weather_data_fetch` DAG has been optimized with intelligent data management, deduplication, and freshness tracking to ensure clean, current weather forecasts in the database.

---

## 📋 Key Features

### 1. **Automatic Deduplication with UPSERT** ✅
**Problem:** Duplicate weather records for same location & timestamp  
**Solution:** Implemented PostgreSQL `ON CONFLICT ... DO UPDATE` logic

**How it Works:**
- When fetching weather data, if a record with same `(adm4, waktu)` already exists
- Instead of ignoring it, the system **overwrites** with the newest data
- All columns get updated: cuaca, suhu_celsius, kelembapan, arah_angin, kecepatan_angin
- `last_updated` timestamp is refreshed to current fetch time

**SQL Pattern:**
```sql
INSERT INTO weather.fact_weather_hourly (...) VALUES (...)
ON CONFLICT (adm4, waktu) DO UPDATE SET
    cuaca = EXCLUDED.cuaca,
    suhu_celsius = EXCLUDED.suhu_celsius,
    ... [all columns]
    last_updated = EXCLUDED.last_updated,
    freshness_status = 'FRESH'
```

**Benefit:** No duplicate cleanup needed; data is always overwritten with latest version

---

### 2. **Data Freshness Tracking** ✅
**Problem:** Users can't tell how old weather forecast data is  
**Solution:** Added 3 new columns to track data age and freshness status

**New Columns:**
```
- last_updated (TIMESTAMP)
    → Tracks when this record was last fetched/updated
    → Updated every time data is refreshed
    → Format: 2026-01-30 08:09:14

- data_age_minutes (INTEGER)
    → Age of data in minutes since last_updated
    → Calculated as: EXTRACT(EPOCH FROM (NOW() - last_updated)) / 60
    → Example: 45, 120, 250

- freshness_status (VARCHAR(20))
    → Status indicator: FRESH, WARNING, or STALE
    → Rules applied:
        • 0-60 mins   → ✅ FRESH    (data is current)
        • 60-180 mins → ⚠️  WARNING (3 hours, getting old)
        • 180+ mins   → ❌ STALE    (>3 hours, data is stale)
```

**Example Data:**
```
lokasi    | waktu              | data_age_minutes | freshness_status
----------|-----------------------|-----|------------------------
Surabaya  | 2026-01-30 08:00:00 | 12  | FRESH
Surabaya  | 2026-01-30 07:00:00 | 72  | WARNING
Gresik    | 2026-01-29 20:00:00 | 240 | STALE
```

---

### 3. **Automatic Cleanup of Old Data** ✅
**Problem:** Database fills with old forecast data  
**Solution:** Automatic deletion of past weather records

**How it Works:**
- DAG task: `cleanup_old_weather_data`
- Deletes all records where `waktu < NOW()` (before current time)
- Keeps only future forecasts
- Runs after every fetch cycle

**SQL Logic:**
```sql
DELETE FROM weather.fact_weather_hourly 
WHERE waktu < NOW() AT TIME ZONE 'Asia/Jakarta'
```

**Example Output:**
```
🗑️ Weather data cleanup completed:
  Deleted 5 old/past weather records
```

---

### 4. **Increased Fetch Frequency** ✅
**Before:** Every 6 hours (00:00, 06:00, 12:00, 18:00)  
**After:** Every 2 hours (00:00, 02:00, 04:00, ... 22:00)

**Schedule Cron:**
```
0 */2 * * *
```

**Benefit:** More frequent, fresher forecasts throughout the day

---

## 🔄 DAG Task Flow

```
┌─────────────────────────┐
│ 1. fetch_bmkg_weather   │  ← Fetch from BMKG API (Surabaya + Gresik)
│    (44 records)         │     Apply UPSERT deduplication
└────────────┬────────────┘
             │
             ↓
┌─────────────────────────┐
│ 2. verify_weather_data  │  ← Verify data inserted (count, latest records)
└────────────┬────────────┘
             │
             ↓
┌─────────────────────────┐
│ 3. update_freshness...  │  ← Update data_age_minutes & freshness_status
│    _metrics             │     Classify as FRESH/WARNING/STALE
└────────────┬────────────┘
             │
             ↓
┌─────────────────────────┐
│ 4. cleanup_old_...      │  ← Delete past weather records
│    weather_data         │     Keep only future forecasts
└─────────────────────────┘
```

**Total Runtime:** ~3-5 seconds per cycle

---

## 📊 Database Schema Changes

### New Columns Added:
```sql
ALTER TABLE weather.fact_weather_hourly
ADD COLUMN last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ADD COLUMN data_age_minutes INTEGER DEFAULT 0;
ADD COLUMN freshness_status VARCHAR(20) DEFAULT 'FRESH';
```

### Data Sample (After Optimization):
```
adm4          | lokasi   | waktu              | cuaca         | suhu_c | freshness_status
---------------|----------|--------------------|-|------|--
35.78.21.1004  | Surabaya | 2026-01-30 08:00:00 | Hujan Ringan  | 27.0 | FRESH
35.78.21.1004  | Surabaya | 2026-01-30 10:00:00 | Berawan       | 28.5 | FRESH
35.25.14.1010  | Gresik   | 2026-01-30 08:00:00 | Cerah Berawan | 29.0 | FRESH
35.25.14.1010  | Gresik   | 2026-02-02 18:00:00 | Berawan       | 26.0 | FRESH
```

---

## 🧪 Testing Results

### Test Run: January 30, 2026 @ 08:09:14 WIB

**Task 1: Fetch BMKG Weather**
```
✅ Deleted 5 expired weather records (from previous runs)
✅ Inserted 22 new records (Surabaya)
✅ Inserted 22 new records (Gresik)
✅ Total: 44 records processed with UPSERT
```

**Task 2: Verify Data**
```
✓ Weather data verification:
  Total records in database: 78
  Latest records:
    - Gresik | 2026-01-30 07:00:00 | Hujan Ringan | 29.0°C
    - Gresik | 2026-01-30 04:00:00 | Cerah Berawan | 32.0°C
    - Gresik | 2026-01-30 01:00:00 | Cerah | 28.0°C
    - Gresik | 2026-02-01 16:00:00 | Berawan | 24.0°C
    - Gresik | 2026-02-01 13:00:00 | Berawan | 25.0°C
```

**Task 3: Cleanup Old Data**
```
✅ Deleted 3 old/past weather records
  (waktu < 2026-01-30 08:09:14)
```

---

## 📈 Benefits Summary

| Feature | Before | After | Benefit |
|---------|--------|-------|---------|
| **Duplicates** | Manual cleanup needed | Automatic UPSERT | No duplicates, clean data |
| **Data Freshness** | Unknown age | Tracked (FRESH/WARNING/STALE) | User knows data age |
| **Fetch Frequency** | 4x/day (6hr) | 12x/day (2hr) | 3x more forecasts |
| **Old Data** | Accumulated | Auto-cleaned | Smaller DB footprint |
| **Data Quality** | Mixed old/new | Only future forecasts | Better relevance |

---

## 🚀 Using Freshness Data in Metabase

### Query to Show Only Fresh Data:
```sql
SELECT 
  lokasi,
  waktu,
  cuaca,
  suhu_celsius,
  data_age_minutes,
  freshness_status,
  CASE 
    WHEN freshness_status = 'FRESH' THEN '✅'
    WHEN freshness_status = 'WARNING' THEN '⚠️'
    ELSE '❌'
  END as indicator
FROM weather.fact_weather_hourly
WHERE freshness_status != 'STALE'
  AND waktu >= CURRENT_DATE AT TIME ZONE 'Asia/Jakarta'
ORDER BY waktu DESC, lokasi;
```

### Color-Coded Visualization:
```
freshness_status = 'FRESH'   → Green background
freshness_status = 'WARNING' → Yellow background
freshness_status = 'STALE'   → Red background / Hidden
```

---

## 📅 Scheduled Execution

### Automatic Runs (Every 2 Hours):
```
00:00 → Fetch + Verify + Freshness + Cleanup
02:00 → Fetch + Verify + Freshness + Cleanup
04:00 → Fetch + Verify + Freshness + Cleanup
...
22:00 → Fetch + Verify + Freshness + Cleanup
```

### Manual Trigger (If Needed):
```bash
# Via CLI
podman exec airflow-webserver airflow dags trigger weather_data_fetch

# Or in Airflow UI: http://localhost:8080
# → Find "weather_data_fetch" DAG
# → Click ▶ (play/trigger button)
```

---

## 🔧 Configuration Files

### Modified Files:
1. **`/home/rafiez/airflow-stack/scripts/fetch_weather_bmkg.py`**
   - Added UPSERT logic to insert_weather_data()
   - Now tracks insert_count vs update_count

2. **`/home/rafiez/airflow-stack/dags/weather_data_fetch.py`**
   - Changed schedule: `0 */6 * * *` → `0 */2 * * *`
   - Added task: `update_freshness_metrics`
   - Updated dependencies: fetch → verify → freshness → cleanup

### Database Changes:
- Added 3 columns to `weather.fact_weather_hourly`
- Created index for faster freshness queries

---

## 📝 Monitoring & Alerts

### Check Freshness Distribution:
```sql
SELECT 
  freshness_status, 
  COUNT(*) as count,
  ROUND(AVG(data_age_minutes)::NUMERIC, 1) as avg_age_mins
FROM weather.fact_weather_hourly
WHERE waktu >= CURRENT_DATE AT TIME ZONE 'Asia/Jakarta'
GROUP BY freshness_status
ORDER BY CASE 
  WHEN freshness_status='FRESH' THEN 1
  WHEN freshness_status='WARNING' THEN 2
  ELSE 3
END;
```

### Alert Thresholds (Recommend):
```
⚠️ WARNING: If > 50% data is WARNING status
❌ CRITICAL: If any data is STALE (>3 hours)
```

---

## 🎓 Summary for Dashboard

**For Metabase Dashboard:**
1. Add freshness_status column to weather tables
2. Filter out STALE data in most visualizations
3. Show `data_age_minutes` as metadata
4. Color-code rows based on freshness_status
5. Add tooltip showing last_updated timestamp

**Example Dashboard Card:**
```
🌦️ Latest Weather (Gresik)
Temperature: 29.0°C
Humidity: 85%
Condition: Hujan Ringan
Last Updated: 12 minutes ago ✅ FRESH
(Shows in green background)
```

---

## 📞 Troubleshooting

### Issue: Tasks not appearing in Airflow UI
**Solution:**
```bash
# Restart webserver
podman restart airflow-webserver
# Wait 30 seconds
# Refresh browser
```

### Issue: Freshness not updating
**Solution:** Check if DAG schedule is enabled (toggle on in UI)

### Issue: Too many STALE records
**Solution:** Check BMKG API availability
```bash
# Test API directly
curl https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4=35.78.21.1004
```

---

**Last Updated:** 2026-01-30 08:09 WIB  
**Version:** 2.0 (Optimized with Deduplication & Freshness)
