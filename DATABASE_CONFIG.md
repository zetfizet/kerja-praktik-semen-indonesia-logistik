# 📊 KONFIGURASI DATABASE WAREHOUSE

## Overview Arsitektur
```
┌─────────────────────────────────────────────────────────────┐
│                    DATABASE WAREHOUSE                        │
│               (localhost:5433/warehouse)                     │
│                                                              │
│  ┌───────────────────────┐  ┌──────────────────────────┐  │
│  │   Schema: public       │  │   Schema: weather        │  │
│  │   (data perusahaan)    │  │   (data cuaca)           │  │
│  │                        │  │                          │  │
│  │   - driver             │  │   - fact_weather_hourly  │  │
│  │   - armada             │  │   - forecast_summary     │  │
│  │   - perjalanan         │  │   - temperature_trend    │  │
│  │   - gps_tracking       │  │                          │  │
│  └───────────────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         ▲                              ▲
         │                              │
         │ Sync via Airflow DAG         │ Fetch via API
         │                              │
┌────────┴────────────┐       ┌─────────┴──────────┐
│  DATABASE SOURCE 1  │       │  BMKG WEATHER API  │
│  devom.silog.co.id  │       │  api.bmkg.go.id    │
│                     │       └────────────────────┘
│  Database: om       │
│  User: om           │
│  Password: om       │
└─────────────────────┘
```

---

## 🔐 KREDENSIAL DATABASE

### 1️⃣ DATABASE SOURCE (Perusahaan - DEVOM)
```
Server/Host : devom.silog.co.id
Port        : 5432
Database    : om
Username    : om
Password    : om
Schema      : public
```

**Di pgAdmin4:**
- Right-click Servers → Register → Server
- Name: `DEVOM - Source Database`
- Host: `devom.silog.co.id`
- Port: `5432`
- Database: `om`
- Username: `om`
- Password: `om`

---

### 2️⃣ DATABASE WAREHOUSE (Target - Gabungan Data)
```
Server/Host : localhost
Port        : 5433
Database    : warehouse
Username    : postgres
Password    : postgres123
Schema      : public, weather, analytics
```

**Di pgAdmin4:**
- Right-click Servers → Register → Server
- Name: `WAREHOUSE - Data Analytics`
- Host: `localhost`
- Port: `5433`
- Database: `warehouse`
- Username: `postgres`
- Password: `postgres123`

---

## 📋 SCHEMA DI DATABASE WAREHOUSE

### Schema: `public`
Data perusahaan dari DEVOM (driver, armada, perjalanan, dll)

**Tables:**
- `driver` - Master data driver
- `armada` - Master data kendaraan
- `driver_armada` - Relasi driver-armada
- `perjalanan` - Data perjalanan
- `gps_tracking` - Tracking GPS
- `order_delivery` - Data order/pengiriman
- dll (auto-sync dari devom.silog.co.id)

### Schema: `weather`
Data cuaca dari BMKG API

**Tables:**
- `fact_weather_hourly` - Data cuaca per jam (forecast + historical)
- `weather_location` - Master lokasi cuaca
- `forecast_summary` - Ringkasan forecast 7 hari

### Schema: `analytics`
Data analytics & KPI

**Tables:**
- `fact_driver_performance` - KPI driver
- `driver_weather_correlation` - Korelasi performa driver & cuaca
- `delivery_weather_impact` - Dampak cuaca terhadap delivery

---

## 🔄 MEKANISME AUTO-UPDATE

### 1. Sync Data Perusahaan (DEVOM → WAREHOUSE)
**Airflow DAG:** `daily_warehouse_sync`
- **Schedule:** Harian jam 00:00 WIB (midnight)
- **Mechanism:** Pull dari devom.silog.co.id
- **Action:** INSERT/UPDATE ke warehouse.public

```python
# Connection config di DAG
SOURCE = {
    'host': 'devom.silog.co.id',
    'database': 'om',
    'user': 'om',
    'password': 'om'
}

TARGET = {
    'host': 'localhost',
    'port': 5433,
    'database': 'warehouse',
    'user': 'postgres',
    'password': 'postgres123'
}
```

### 2. Fetch Data Cuaca (BMKG API → WAREHOUSE)
**Airflow DAG:** `weather_data_fetch`
- **Schedule:** Setiap jam (00:00, 01:00, 02:00, ..., 23:00)
- **Mechanism:** Fetch dari BMKG API
- **Action:** INSERT/UPDATE ke warehouse.weather

```python
# Connection config di DAG
TARGET = {
    'host': 'localhost',
    'database': 'warehouse',
    'user': 'postgres',
    'password': 'postgres123'
}
```

---

## 🚀 CARA SETUP DI pgAdmin4

### Step 1: Register Server Warehouse
1. Buka pgAdmin4
2. Right-click **Servers** → **Register** → **Server**
3. Tab **General:**
   - Name: `WAREHOUSE`
4. Tab **Connection:**
   - Host: `localhost`
   - Port: `5433`
   - Database: `warehouse`
   - Username: `postgres`
   - Password: `postgres123`
5. Klik **Save**

### Step 2: Register Server DEVOM (Source)
1. Right-click **Servers** → **Register** → **Server**
2. Tab **General:**
   - Name: `DEVOM-SOURCE`
3. Tab **Connection:**
   - Host: `devom.silog.co.id`
   - Port: `5432`
   - Database: `om`
   - Username: `om`
   - Password: `om`
4. Klik **Save**

### Step 3: Verify Schemas
Di server **WAREHOUSE**, pastikan ada schemas:
- ✅ `public` - untuk data perusahaan
- ✅ `weather` - untuk data cuaca
- ✅ `analytics` - untuk data analitik

---

## 📊 QUERY TEST CONNECTION

### Test WAREHOUSE Database
```sql
-- Check schemas
SELECT schema_name 
FROM information_schema.schemata 
WHERE schema_name IN ('public', 'weather', 'analytics');

-- Check weather data
SELECT COUNT(*) as total_weather_records
FROM weather.fact_weather_hourly;

-- Check company data  
SELECT COUNT(*) as total_drivers
FROM public.driver;
```

### Test DEVOM Source
```sql
-- List all tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```

---

## 🎯 KESIMPULAN

**1 Database Warehouse** yang berisi:
- Data perusahaan (dari devom.silog.co.id)
- Data cuaca (dari BMKG API)
- Data analytics (hasil olahan)

**Auto-update:**
- ✅ Data perusahaan sync otomatis via DAG harian
- ✅ Data cuaca fetch otomatis via DAG per jam
- ✅ Semua data terpusat di warehouse

**Kredensial untuk pgAdmin4:**
```
Host: localhost
Port: 5433
Database: warehouse
User: postgres
Password: postgres123
```
