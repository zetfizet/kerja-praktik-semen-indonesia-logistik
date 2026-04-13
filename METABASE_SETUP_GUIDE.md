# Metabase Setup Guide - Warehouse Analytics Dashboard

**Tanggal**: 13 Februari 2026  
**Status**: Ready for Setup  
**Database**: warehouse (postgres/postgres123)

---

## 📋 Overview

Metabase adalah open-source business intelligence tool untuk visualisasi data warehouse yang menggabungkan:
- **Data Perusahaan**: 88 tables dari DEVOM (devom.silog.co.id)
- **Data Cuaca**: 1 table (fact_weather_hourly) dari BMKG API

**Keunggulan:**
- ✅ SQL query builder visual (no coding)
- ✅ Interactive dashboards dengan real-time data
- ✅ Auto-refresh untuk monitoring
- ✅ Export ke PDF, Excel, CSV
- ✅ Multi-user dengan role-based access

---

## 🚀 Quick Start

### Step 1: Start Metabase Container

```bash
cd /home/rafie/airflow-stack

# Start Metabase
bash start_metabase.sh

# Wait 30-60 seconds for startup
# Access: http://localhost:3000
```

### Step 2: Initial Setup (First Time)

1. **Open Browser**: http://localhost:3000
2. **Choose Language**: English / Indonesian
3. **Create Admin Account**:
   - Email: `admin@warehouse.local`
   - Password: `metabase123`
   - First Name: Admin
   - Last Name: Warehouse
4. **Skip "Add your data" for now**

### Step 3: Add Database Connection

1. Click **Settings** (⚙️) → **Admin** → **Databases**
2. Click **Add database**
3. Fill in the form:

```
Database type: PostgreSQL
Display name: Warehouse Database
Host: 127.0.0.1
Port: 5433
Database name: warehouse
Username: postgres
Password: postgres123
```

4. **Advanced options** (optional):
   - Use SSL: No
   - Schema: public
5. Click **Save**

**Test Connection**:
- Metabase will test automatically
- Should show "Successfully connected to Warehouse  Database" ✅

---

## 📊 Sample Queries & Dashboards

### Query 1: Total Records Per Table

```sql
SELECT 
    table_name,
    CASE 
        WHEN table_name = 'fact_weather_hourly' THEN 'Weather Data'
        ELSE 'Company Data'
    END as category,
    (SELECT COUNT(*) FROM information_schema.columns 
     WHERE columns.table_name = tables.table_name 
     AND table_schema='public') as column_count
FROM information_schema.tables
WHERE table_schema='public' 
  AND table_type='BASE TABLE'
ORDER BY table_name;
```

**Visualization**: Table or Bar Chart  
**Purpose**: Overview of warehouse structure

---

### Query 2: Weather Forecast Summary

```sql
SELECT 
    lokasi,
    COUNT(*) as total_forecasts,
    MIN(waktu) as earliest_forecast,
    MAX(waktu) as latest_forecast,
    ROUND(AVG(suhu_celsius), 1) as avg_temperature,
    ROUND(AVG(kelembapan), 1) as avg_humidity
FROM public.fact_weather_hourly
GROUP BY lokasi
ORDER BY lokasi;
```

**Visualization**: Table  
**Purpose**: Weather data overview by location

---

### Query 3: Hourly Temperature Trends

```sql
SELECT 
    lokasi,
    waktu,
    suhu_celsius,
    kelembapan,
    cuaca
FROM public.fact_weather_hourly
WHERE waktu >= CURRENT_DATE
ORDER BY lokasi, waktu;
```

**Visualization**: Line Chart  
- X axis: waktu
- Y axis: suhu_celsius
- Group by: lokasi
**Purpose**: Temperature trends over time

---

### Query 4: Weather by Condition

```sql
SELECT 
    cuaca as weather_condition,
    COUNT(*) as forecast_count,
    ROUND(AVG(suhu_celsius), 1) as avg_temp,
    ROUND(AVG(kelembapan), 1) as avg_humidity
FROM public.fact_weather_hourly
GROUP BY cuaca
ORDER BY forecast_count DESC;
```

**Visualization**: Pie Chart or Bar Chart  
**Purpose**: Distribution of weather conditions

---

### Query 5: Data Freshness Status

```sql
SELECT 
    'Weather Data' as data_source,
    COUNT(*) as total_records,
    COUNT(DISTINCT adm4) as locations,
    MAX(last_updated) as last_data_update,
    EXTRACT(EPOCH FROM (NOW() - MAX(last_updated)))/60 as minutes_since_update
FROM public.fact_weather_hourly;
```

**Visualization**: Metric or Table  
**Purpose**: Monitor data freshness for alerts

---

### Query 6: 7-Day Forecast by Location

```sql
SELECT 
    lokasi,
    desa,
    kecamatan,
    kabupaten,
    DATE(waktu) as forecast_date,
    MIN(suhu_celsius) as min_temp,
    MAX(suhu_celsius) as max_temp,
    ROUND(AVG(suhu_celsius), 1) as avg_temp,
    MAX(cuaca) as weather_condition
FROM public.fact_weather_hourly
WHERE waktu >= CURRENT_DATE 
  AND waktu < CURRENT_DATE + INTERVAL '7 days'
GROUP BY lokasi, desa, kecamatan, kabupaten, DATE(waktu)
ORDER BY lokasi, forecast_date;
```

**Visualization**: Table or Line Chart  
**Purpose**: Weekly forecast summary

---

## 🎨 Creating a Dashboard

### Dashboard: "Weather Monitoring"

1. **Create New Dashboard**:
   - Click **Dashboards** → **New dashboard**
   - Name: "Weather Monitoring"
   - Description: "Real-time weather data from BMKG API"

2. **Add Cards** (queries as visualizations):
   - **Card 1**: Weather Forecast Summary (Table)
   - **Card 2**: Hourly Temperature Trends (Line Chart)
   - **Card 3**: Weather by Condition (Pie Chart)
   - **Card 4**: Data Freshness Status (Metric)

3. **Configure Auto-Refresh**:
   - Click ⚙️ (Dashboard settings)
   - Set refresh: Every hour (to match DAG schedule)

4. **Add Filters** (optional):
   - Add filter: Date range (waktu)
   - Add filter: Location (lokasi)

---

## 🏗️ Creating Queries in Metabase

### Method 1: Visual Query Builder (No SQL)

1. Click **New** → **Question**
2. Select **Warehouse Database**
3. Choose table: `fact_weather_hourly`
4. Click columns to select
5. Add filters, grouping, ordering
6. Choose visualization type
7. Save question

### Method 2: Native SQL Query

1. Click **New** → **Question**
2. Select **Warehouse Database**
3. Click **Native query**
4. Enter SQL (see sample queries above)
5. Click **Visualize**
6. Choose chart type
7. Save question

---

## 📈 Visualization Types

| Chart Type | Best For | Example Use |
|------------|----------|-------------|
| **Table** | Raw data, lists | Forecast details, location lists |
| **Line Chart** | Trends over time | Temperature trends, humidity over time |
| **Bar Chart** | Comparisons | Temp by location, records per day |
| **Pie Chart** | Proportions | Weather condition distribution |
| **Metric** | Single KPI | Total forecasts, latest update time |
| **Map** | Geographic data | Locations with lat/long (future enhancement) |

---

## 🔄 Connecting to Company Data

### Sample Query: Warehouse Armada Table

```sql
-- Check if table exists and has data
SELECT COUNT(*) as total_armada
FROM public.armada_tms
LIMIT 1;
```

### Cross-Referencing Weather & Company Data

```sql
-- Example: Weather conditions during delivery routes
-- (Requires location matching - future enhancement)
SELECT 
    w.lokasi,
    w.kabupaten,
    w.waktu,
    w.cuaca,
    w.suhu_celsius,
    COUNT(*) as delivery_count
FROM public.fact_weather_hourly w
LEFT JOIN public.delivery_order d 
    ON DATE(d.created_at) = DATE(w.waktu)
    -- Add location matching logic here
WHERE w.waktu >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY w.lokasi, w.kabupaten, w.waktu, w.cuaca, w.suhu_celsius
ORDER BY w.waktu DESC;
```

---

## 🛠️ Advanced Configuration

### Email Alerts

1. **Settings** → **Admin** → **Email**
2. Configure SMTP settings
3. Create email subscriptions for dashboards
4. Set schedule: Daily, Weekly, or Custom

### Dashboard Embedding

```html
<!-- Embed dashboard in web page -->
<iframe 
  src="http://localhost:3000/embed/dashboard/TOKEN"
  frameborder="0" 
  width="800" 
  height="600">
</iframe>
```

**Enable Embedding**:
1. **Settings** → **Admin** → **Embedding**
2. Enable embedding
3. Copy embed code

### API Access

```bash
# Get API session token
curl -X POST http://localhost:3000/api/session \
  -H "Content-Type: application/json" \
  -d '{"username": "admin@warehouse.local", "password": "metabase123"}'

# Query data via API
curl -X POST http://localhost:3000/api/dataset \
  -H "Content-Type: application/json" \
  -H "X-Metabase-Session: YOUR_SESSION_TOKEN" \
  -d '{"database": 1, "type": "native", "native": {"query": "SELECT * FROM public.fact_weather_hourly LIMIT 10"}}'
```

---

## 🐛 Troubleshooting

### Issue: Cannot connect to database

**Error**: `Connection error: Connection refused`

**Solutions**:
1. Check PostgreSQL is running:
   ```bash
   podman ps | grep postgres
   ```
2. Test connection manually:
   ```bash
   PGPASSWORD=postgres123 psql -h localhost -p 5433 -U postgres -d warehouse -c "SELECT 1"
   ```
3. Verify port 5433 is correct (not 5432)
4. Use 127.0.0.1 instead of localhost if connection fails

---

### Issue: Metabase won't start

**Error**: Port 3000 already in use

**Solutions**:
```bash
# Check what's using port 3000
ss -tulnp | grep 3000

# Stop existing Metabase
podman stop metabase
podman rm metabase

# Restart
bash start_metabase.sh
```

---

### Issue: Slow query performance

**Optimization**:
1. Add indexes on frequently queried columns:
   ```sql
   CREATE INDEX idx_weather_waktu ON public.fact_weather_hourly(waktu);
   CREATE INDEX idx_weather_lokasi ON public.fact_weather_hourly(lokasi);
   ```
2. Limit date ranges in queries
3. Use aggregations instead of raw data

---

## 📚 Resources

**Metabase Documentation**:
- Official Docs: https://www.metabase.com/docs/latest/
- SQL Reference: https://www.metabase.com/learn/sql-questions
- Visualization Guide: https://www.metabase.com/learn/visualization

**Database Schema**:
- [Database Config](./DATABASE_CONFIG.md)
- [Weather DAG](./WEATHER_DAG_OPTIMIZATION.md)
- [SQL Files](./sql/)

**Related Tools**:
- Airflow UI: http://localhost:8080
- PostgreSQL: localhost:5433

---

## 🔐 Security Notes

**Production Recommendations**:
1. **Change default credentials**:
   - Admin user: Use strong password
   - Database user: Create read-only user for Metabase
2. **Enable SSL** for database connection
3. **Set up authentication**: LDAP, SAML, or Google OAuth
4. **Restrict IP access** to Metabase port 3000
5. **Regular backups** of Metabase H2 database

**Read-Only Database User** (recommended):
```sql
-- Create read-only user for Metabase
CREATE USER metabase_readonly WITH PASSWORD 'metabase_secure_password';
GRANT CONNECT ON DATABASE warehouse TO metabase_readonly;
GRANT USAGE ON SCHEMA public TO metabase_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO metabase_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO metabase_readonly;
```

---

## 🎯 Next Steps

1. ✅ Start Metabase container
2. ✅ Complete initial setup
3. ✅ Add warehouse database connection
4. ✅ Create sample queries from this guide
5. ✅ Build "Weather Monitoring" dashboard
6. ⏭️ Share dashboard with team
7. ⏭️ Set up email alerts
8. ⏭️ Create company data dashboards (orders, deliveries, armada)

---

**Commands Summary**:
```bash
# Start Metabase
bash start_metabase.sh

# Stop Metabase
bash stop_metabase.sh

# Check status
podman ps | grep metabase

# View logs
podman logs -f metabase

# Access URL
http://localhost:3000
```

---

**Last Updated**: 13 Februari 2026  
**Status**: ✅ Ready for setup (waiting for image download)  
**Next**: Start container and create dashboards
