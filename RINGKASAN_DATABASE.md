# 📝 RINGKASAN: DATABASE & KREDENSIAL

## 🔐 KREDENSIAL UNTUK pgAdmin4

### 1️⃣ Database WAREHOUSE (Gabungan Data Perusahaan + Cuaca)
```
Name     : WAREHOUSE
Host     : localhost
Port     : 5433
Database : warehouse
Username : postgres
Password : postgres123
```

**Isi database ini:**
- ✅ Data perusahaan (driver, armada, perjalanan) - schema: `public`
- ✅ Data cuaca BMKG (forecast per jam) - schema: `weather`
- ✅ Data analytics & KPI - schema: `analytics`

---

### 2️⃣ Database DEVOM (Source - Data Perusahaan)
```
Name     : DEVOM-SOURCE
Host     : devom.silog.co.id
Port     : 5432
Database : om
Username : om
Password : om
```

**Isi database ini:**
- Data source perusahaan (master data)
- Akan di-sync otomatis ke WAREHOUSE setiap hari

---

## 🚀 CARA SETUP

### Step 1: Setup Database Warehouse
```bash
# Jalankan script setup (sekali saja)
bash setup_warehouse_db.sh
```

### Step 2: Register di pgAdmin4

**A. Register WAREHOUSE:**
1. Buka pgAdmin4
2. Right-click **Servers** → **Register** → **Server**
3. Tab **General:** Name = `WAREHOUSE`
4. Tab **Connection:**
   - Host: `localhost`
   - Port: `5433`
   - Database: `warehouse`
   - Username: `postgres`
   - Password: `postgres123`
5. Klik **Save**

**B. Register DEVOM (opsional):**
1. Right-click **Servers** → **Register** → **Server**
2. Tab **General:** Name = `DEVOM-SOURCE`
3. Tab **Connection:**
   - Host: `devom.silog.co.id`
   - Database: `om`
   - Username: `om`
   - Password: `om`
4. Klik **Save**

---

## 🔄 AUTO-UPDATE MECHANISM

### ✅ Data Perusahaan (DEVOM → WAREHOUSE)
- **Airflow DAG:** `daily_warehouse_sync`
- **Schedule:** Harian jam 00:00 WIB
- **Sync:** Semua tabel dari devom.silog.co.id ke warehouse.public

### ✅ Data Cuaca (BMKG API → WAREHOUSE)
- **Airflow DAG:** `weather_data_fetch`
- **Schedule:** Setiap jam (00:00, 01:00, 02:00, ..., 23:00)
- **Fetch:** Forecast cuaca dari BMKG API ke warehouse.weather

### 📊 Hasil:
Semua input baru dari:
- ✅ Database DEVOM → otomatis sync ke WAREHOUSE (harian)
- ✅ BMKG API → otomatis fetch ke WAREHOUSE (per jam)

---

## 📋 SCHEMA DI DATABASE WAREHOUSE

```
warehouse
├── public (data perusahaan)
│   ├── driver
│   ├── armada
│   ├── perjalanan
│   ├── gps_tracking
│   └── ... (semua tabel dari devom)
│
├── weather (data cuaca)
│   ├── fact_weather_hourly (forecast per jam)
│   ├── dim_weather_location (master lokasi)
│   └── Views (v_forecast_7days, v_current_weather)
│
└── analytics (data analytics)
    ├── fact_driver_performance
    └── driver_weather_correlation
```

---

## 🧪 TEST CONNECTION

### Test di pgAdmin4:
1. Connect ke server **WAREHOUSE**
2. Klik kanan database `warehouse` → **Query Tool**
3. Jalankan query test:

```sql
-- Check schemas
SELECT schema_name 
FROM information_schema.schemata 
WHERE schema_name IN ('public', 'weather', 'analytics');

-- Check weather data
SELECT COUNT(*) as total_weather, 
       MIN(waktu) as earliest, 
       MAX(waktu) as latest
FROM weather.fact_weather_hourly;

-- Check lokasi cuaca
SELECT * FROM weather.dim_weather_location;
```

---

## 📖 Dokumentasi Lengkap

- **DATABASE_CONFIG.md** - Dokumentasi lengkap arsitektur
- **sql/05_create_weather_schema.sql** - DDL schema weather
- **airflow/dags/weather_data_fetch.py** - DAG fetch cuaca
- **airflow/dags/daily_warehouse_sync.py** - DAG sync perusahaan

---

## 🎯 KESIMPULAN

**Anda punya 1 database warehouse** yang berisi:
1. ✅ Data perusahaan dari devom.silog.co.id (auto-sync harian)
2. ✅ Data cuaca dari BMKG API (auto-fetch per jam)
3. ✅ Semua terpusat di satu tempat untuk analytics

**Kredensial pgAdmin4:**
```
Host: localhost | Port: 5433
Database: warehouse
User: postgres | Pass: postgres123
```
