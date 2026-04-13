# 📊 DATABASE WAREHOUSE - SINGLE SCHEMA

## 🎯 Struktur Database (Simplified)

```
warehouse (database)
└── public (schema) ← SEMUA DATA DI SINI
    ├── driver, armada, perjalanan, ... (data perusahaan dari DEVOM)
    └── fact_weather_hourly, dim_weather_location (data cuaca dari BMKG)
```

**1 Database, 1 Schema, Semua Tables**

---

## 🔐 Credentials

```
Host     : localhost
Port     : 5433
Database : warehouse
Username : postgres
Password : postgres123
Schema   : public (hanya 1 schema!)
```

---

## 🚀 Quick Setup (3 Perintah)

```bash
# 1. Start containers
bash quick_start.sh

# 2. Setup schema & weather tables
bash setup_warehouse_db.sh

# 3. Copy tables dari DEVOM
bash copy_devom_structure.sh
```

Setelah itu, semua tables (perusahaan + cuaca) ada di **public schema**!

---

## 📋 Tables di Public Schema

### Data Perusahaan (dari DEVOM)
- `driver` - Master data driver
- `armada` - Master data kendaraan
- `perjalanan` - Data perjalanan
- `gps_tracking` - Data GPS
- `order_delivery` - Data order
- ... (semua tables dari devom.silog.co.id)

### Data Cuaca (dari BMKG API)
- `fact_weather_hourly` - Forecast cuaca per jam
- `dim_weather_location` - Master lokasi cuaca
- `v_weather_forecast_7days` - View forecast 7 hari

---

## ✅ Keuntungan Single Schema

### 1. Query Lebih Sederhana
```sql
-- Dulu (multi-schema):
SELECT * FROM public.driver;
SELECT * FROM weather.fact_weather_hourly;

-- Sekarang (single schema):
SELECT * FROM driver;
SELECT * FROM fact_weather_hourly;
```

### 2. JOIN Lebih Mudah
```sql
-- Join data perjalanan + cuaca (no schema prefix needed!)
SELECT 
    d.nama_driver,
    p.lokasi_asal,
    w.cuaca,
    w.suhu_celsius
FROM perjalanan p
JOIN driver d ON p.uuid_user = d.uuid_user
LEFT JOIN fact_weather_hourly w 
    ON w.lokasi = p.lokasi_asal 
    AND DATE(w.waktu) = DATE(p.tanggal_berangkat);
```

### 3. Manajemen Lebih Mudah
- ✅ Tidak perlu switch schema
- ✅ Permission management lebih simple
- ✅ Backup/restore straightforward

---

## 🔄 Auto-Update

### Data Perusahaan
- **Source:** devom.silog.co.id
- **DAG:** `daily_warehouse_sync`
- **Schedule:** Harian jam 00:00 WIB
- **Target:** `public.driver`, `public.armada`, dll

### Data Cuaca
- **Source:** BMKG API
- **DAG:** `weather_data_fetch`
- **Schedule:** Per jam (00:00, 01:00, ..., 23:00)
- **Target:** `public.fact_weather_hourly`

**Hasil:** Semua input baru otomatis masuk ke **public schema**!

---

## 🧪 Verify di pgAdmin4

```sql
-- List semua tables
SELECT table_name,
       CASE 
           WHEN table_name LIKE '%weather%' THEN 'Weather'
           ELSE 'Company'
       END as data_type
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY data_type, table_name;

-- Check data
SELECT COUNT(*) FROM driver;
SELECT COUNT(*) FROM fact_weather_hourly;

-- Query cuaca terkini
SELECT lokasi, waktu, cuaca, suhu_celsius 
FROM fact_weather_hourly 
WHERE waktu >= NOW() 
ORDER BY waktu LIMIT 10;
```

---

## 📖 Dokumentasi Lengkap

- **[STRUKTUR_WAREHOUSE_SINGLE_SCHEMA.txt](STRUKTUR_WAREHOUSE_SINGLE_SCHEMA.txt)** - Detail struktur single schema
- **[SETUP_GUIDE.txt](SETUP_GUIDE.txt)** - Panduan setup step-by-step
- **[CARA_CONNECT_PGADMIN4.txt](CARA_CONNECT_PGADMIN4.txt)** - Cara connect pgAdmin4

---

## ✅ Checklist Setup

- [ ] `bash quick_start.sh` → Containers running
- [ ] `bash setup_warehouse_db.sh` → Weather tables dibuat di public
- [ ] `bash copy_devom_structure.sh` → Tables DEVOM dibuat di public
- [ ] Connect pgAdmin4 → Lihat: Schemas → public → Tables
- [ ] Trigger DAG `daily_warehouse_sync` → Data DEVOM masuk
- [ ] Trigger DAG `weather_data_fetch` → Data cuaca masuk
- [ ] **Verify:** Semua tables dalam 1 schema (public) ✅

---

**🎉 Selesai! Semua data perusahaan + cuaca dalam 1 schema (public)!**
