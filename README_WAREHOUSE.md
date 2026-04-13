# 📊 WAREHOUSE DATABASE SETUP - README

## 🎯 Tujuan
Setup database warehouse yang menggabungkan:
1. **Data perusahaan** dari devom.silog.co.id
2. **Data cuaca** dari BMKG API

Semua data terpusat di **1 database warehouse** untuk analytics.

---

## 📁 File-File Penting

### 📖 Dokumentasi
| File | Deskripsi |
|------|-----------|
| **[SETUP_GUIDE.txt](SETUP_GUIDE.txt)** | ⭐ **MULAI DI SINI!** Panduan step-by-step setup |
| **[CARA_CONNECT_PGADMIN4.txt](CARA_CONNECT_PGADMIN4.txt)** | Cara connect ke pgAdmin4 dengan detail |
| **[STRUKTUR_WAREHOUSE.txt](STRUKTUR_WAREHOUSE.txt)** | Struktur lengkap database & flow |
| **[RINGKASAN_DATABASE.md](RINGKASAN_DATABASE.md)** | Overview & credentials |
| **[CREDENTIALS.txt](CREDENTIALS.txt)** | Ringkasan credentials copy-paste |
| **[ERROR_FIXED.md](ERROR_FIXED.md)** | Troubleshooting error umum |

### 🛠️ Scripts Setup
| File | Perintah | Deskripsi |
|------|----------|-----------|
| **[quick_start.sh](quick_start.sh)** | `bash quick_start.sh` | Start PostgreSQL & Airflow containers |
| **[setup_warehouse_db.sh](setup_warehouse_db.sh)** | `bash setup_warehouse_db.sh` | Setup schemas, user, & tables weather |
| **[copy_devom_structure.sh](copy_devom_structure.sh)** | `bash copy_devom_structure.sh` | ⭐ Copy semua tables dari DEVOM |
| **[note.sh](note.sh)** | `bash note.sh` | Cleanup containers (reset) |

### 🐍 Python Scripts
| File | Deskripsi |
|------|-----------|
| **[scripts/copy_devom_structure.py](scripts/copy_devom_structure.py)** | Auto-copy structure tables dari DEVOM |

### 💾 SQL Files
| File | Deskripsi |
|------|-----------|
| **[sql/05_create_weather_schema.sql](sql/05_create_weather_schema.sql)** | DDL schema weather |
| **sql/06_devom_tables_ddl.sql** | DDL semua tables dari DEVOM (auto-generated) |

### ⚙️ Airflow DAGs
| File | Schedule | Deskripsi |
|------|----------|-----------|
| **[airflow/dags/weather_data_fetch.py](airflow/dags/weather_data_fetch.py)** | Per jam | Fetch cuaca dari BMKG API |
| **[airflow/dags/daily_warehouse_sync.py](airflow/dags/daily_warehouse_sync.py)** | Harian | Sync data dari DEVOM |

---

## 🚀 Quick Start (3 Perintah)

```bash
# 1. Start containers
bash quick_start.sh

# 2. Setup schemas & credentials  
bash setup_warehouse_db.sh

# 3. Copy structure dari DEVOM (⭐ PENTING!)
bash copy_devom_structure.sh
```

Setelah itu, connect ke pgAdmin4 (lihat [CARA_CONNECT_PGADMIN4.txt](CARA_CONNECT_PGADMIN4.txt))

---

## 🔐 Credentials Database Warehouse

```
Host     : localhost
Port     : 5433
Database : warehouse
Username : postgres          ⬅️ BUKAN postgres123!
Password : postgres123
```

**⚠️ JANGAN TERTUKAR!**
- Username adalah **postgres** (bukan postgres123)
- Password adalah **postgres123**

---

## 📊 Struktur Database Warehouse

```
warehouse (database)
├── Schemas
│   ├── public (data perusahaan dari DEVOM)
│   │   └── Tables
│   │       ├── driver (uuid_user, nama_driver, nomor_telepon, ...)
│   │       ├── armada (id_armada, nomor_plat, jenis_armada, ...)
│   │       ├── perjalanan (...)
│   │       └── ... (semua tables dari devom.silog.co.id)
│   │
│   ├── weather (data cuaca dari BMKG API)
│   │   └── Tables
│   │       ├── fact_weather_hourly (adm4, lokasi, waktu, suhu, ...)
│   │       └── dim_weather_location (...)
│   │
│   └── analytics (data analytics & KPI)
│       └── Tables
│           └── fact_driver_performance (...)
```

---

## 🔄 Auto-Update Mechanism

### ✅ Data Perusahaan (DEVOM → WAREHOUSE)
- **DAG:** `daily_warehouse_sync`
- **Schedule:** Harian jam 00:00 WIB
- **Action:** Sync semua data baru dari devom.silog.co.id ke warehouse.public

### ✅ Data Cuaca (BMKG API → WAREHOUSE)
- **DAG:** `weather_data_fetch`
- **Schedule:** Setiap jam (00:00, 01:00, ..., 23:00)
- **Action:** Fetch forecast cuaca dari BMKG API ke warehouse.weather

**Hasil:** Semua input baru otomatis ter-update di database warehouse!

---

## 🧪 Verify Setup

### Di pgAdmin4, jalankan:

```sql
-- List semua schemas
SELECT schema_name 
FROM information_schema.schemata 
WHERE schema_name IN ('public', 'weather', 'analytics');
-- Expected: 3 rows

-- List tables di schema public (data perusahaan)
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema='public' 
ORDER BY table_name;
-- Expected: banyak tables (driver, armada, perjalanan, dll)

-- List tables di schema weather (data cuaca)
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema='weather' 
ORDER BY table_name;
-- Expected: fact_weather_hourly, dim_weather_location, dll

-- Check data di table driver (contoh)
SELECT COUNT(*) as total_drivers FROM public.driver;

-- Check data cuaca
SELECT COUNT(*) as total_weather_records FROM weather.fact_weather_hourly;
```

---

## 🆘 Troubleshooting

| Error | Solusi |
|-------|--------|
| `role "postgres123" does not exist` | Username salah! Gunakan: **postgres** (bukan postgres123) |
| `connection refused` | Container belum running: `bash quick_start.sh` |
| `No tables in schema public` | Belum run: `bash copy_devom_structure.sh` |
| `Cannot connect to DEVOM` | Check network/VPN ke devom.silog.co.id |

Lihat detail: [ERROR_FIXED.md](ERROR_FIXED.md)

---

## 📖 Detail Dokumentasi

1. **Setup awal?** → Baca [SETUP_GUIDE.txt](SETUP_GUIDE.txt)
2. **Connect pgAdmin4?** → Baca [CARA_CONNECT_PGADMIN4.txt](CARA_CONNECT_PGADMIN4.txt)
3. **Struktur database?** → Baca [STRUKTUR_WAREHOUSE.txt](STRUKTUR_WAREHOUSE.txt)
4. **Error/masalah?** → Baca [ERROR_FIXED.md](ERROR_FIXED.md)

---

## 📞 Quick Reference

```bash
# Start containers
bash quick_start.sh

# Stop containers
bash note.sh

# Setup warehouse
bash setup_warehouse_db.sh

# Copy structure dari DEVOM
bash copy_devom_structure.sh

# View Airflow
http://localhost:8080

# Connect pgAdmin4
Host: localhost:5433
User: postgres
Pass: postgres123
```

---

## ✅ Checklist Setup

- [ ] Run `bash quick_start.sh` → Containers running
- [ ] Run `bash setup_warehouse_db.sh` → Schemas dibuat
- [ ] Run `bash copy_devom_structure.sh` → Tables DEVOM dibuat
- [ ] Connect pgAdmin4 → Bisa lihat schemas & tables
- [ ] Trigger DAG `daily_warehouse_sync` → Data DEVOM ter-sync
- [ ] Trigger DAG `weather_data_fetch` → Data cuaca masuk
- [ ] Verify data → Query di pgAdmin4 berhasil

**Setelah semua checklist ✅, database warehouse siap digunakan! 🎉**

---

**📝 Note:** Untuk update/pertanyaan, lihat dokumentasi lengkap di folder ini.
