# 📖 Database Schema Reference

**Warehouse database structure, tables, and relationships**

---

## 📑 Table of Contents

- [Database Overview](#database-overview)
- [Schemas](#schemas)
- [All 90 Tables](#all-90-tables)
- [Key Tables](#key-tables)

---

## Database Overview

### Warehouse Database Configuration

```
Database Name:      warehouse
Host:               localhost
Port:               5433
Owner:              postgres
Encoding:           UTF-8
Collate:            en_US.utf8
Ctype:              en_US.utf8
Size:               2-5GB (typical)
Tables:             90 (from DEVOM sync)
```

### User Access

```
User:               postgres
Password:           postgres123 (development)
Role:               Superuser
Connection limit:   Unlimited
```

---

## Schemas

### Schema 1: `public` - Business Data (90 Tables)

**Purpose:** Complete DEVOM company data synced daily  
**Owner:** postgres  
**Size:** 1-3GB  
**Update Frequency:** Daily @ 00:00 UTC (via daily_warehouse_sync DAG)  
**Sync Strategy:** Full sync (TRUNCATE + reload)

**Table Count:** 90 tables

```
┌─────────────────────────────────────────────────────────────┐
│ 90 TABLES SYNCED FROM DEVOM (devom.silog.co.id)            │
├─────────────────────────────────────────────────────────────┤
│ ADMINISTRATIVE & MASTER DATA (14 tables)                    │
│ ─────────────────────────────────────────────────────────── │
│ • atribut                    - Product attributes           │
│ • atribut_produk             - Product attributes mapping  │
│ • bank                       - Bank information            │
│ • categories_produk          - Product categories          │
│ • jenis_armada               - Vehicle type classification │
│ • jenis_file                 - File type classification    │
│ • jenis_insiden              - Incident type classes       │
│ • jenis_notifikasi           - Notification types          │
│ • jenis_order                - Order type classes          │
│ • jenis_satuan               - Unit of measure types       │
│ • jenis_transaksi            - Transaction type classes    │
│ • konversi                   - Unit conversion factors     │
│ • language                   - Supported languages         │
│ • language_text              - Language translations       │
│                                                             │
│ GEOGRAPHIC DATA (2 tables)                                 │
│ ─────────────────────────────────────────────────────────── │
│ • geofence                   - Geographic boundaries       │
│ • locations                  - Location coordinates        │
│                                                             │
│ PERSONNEL & SECURITY (4 tables)                            │
│ ─────────────────────────────────────────────────────────── │
│ • daftar_user                - User registry               │
│ • kontak_darurat             - Emergency contacts          │
│ • role                       - User role definitions       │
│ • status_user                - User status types           │
│                                                             │
│ VEHICLE & FLEET (9 tables)                                 │
│ ─────────────────────────────────────────────────────────── │
│ • armada_perangkat           - Vehicle device mapping     │
│ • armada_tms                 - TMS tracking data          │
│ • driver_armada              - Driver-vehicle assignment  │
│ • gudang                     - Warehouse/depot info       │
│ • parent_armada              - Vehicle hierarchy          │
│ • perangkat                  - GPS/IoT devices            │
│ • perangkat_gps_driver       - Driver GPS devices         │
│ • rute                       - Route definitions          │
│ • rute_perangkat             - Device route tracking      │
│                                                             │
│ DELIVERY & OPERATIONS (16 tables)                          │
│ ─────────────────────────────────────────────────────────── │
│ • delivery_order             - Delivery orders            │
│ • detail_do                  - Delivery order lines       │
│ • detail_po                  - Purchase order lines       │
│ • detail_qc                  - QC check details           │
│ • detail_sm                  - Service request details    │
│ • detail_so                  - Sales order lines          │
│ • notifikasi                 - Notifications              │
│ • orders                     - Sales orders               │
│ • order_tms                  - TMS orders                 │
│ • pengingat_pemeliharaan_armada - Vehicle maintenance   │
│ • pengembalian               - Returns/refunds            │
│ • purchase_order             - Purchase orders            │
│ • quality_control            - QC records                 │
│ • sales_order                - Sales orders               │
│ • status_order               - Order status types         │
│ • units                      - Unit definitions           │
│                                                             │
│ CHAT & NOTIFICATIONS (5 tables)                            │
│ ─────────────────────────────────────────────────────────── │
│ • chat_room                  - Chat rooms                  │
│ • room_last_read             - Chat read tracking         │
│ • room_members               - Chat room membership       │
│ • customers                  - Customer information       │
│ • rating                     - Customer ratings           │
│                                                             │
│ ATTACHMENT & DOCUMENTS (8 tables)                          │
│ ─────────────────────────────────────────────────────────── │
│ • attachment                 - Generic attachments        │
│ • attachment_armada          - Vehicle attachments        │
│ • attachment_chat            - Chat attachments           │
│ • attachment_driver          - Driver attachments         │
│ • attachment_gudang          - Warehouse attachments      │
│ • attachment_perangkat       - Device attachments         │
│ • attachment_pengembalian    - Return attachments         │
│ • attachment_qc              - QC attachments             │
│                                                             │
│ LOGGING & ACTIVITY (7 tables)                              │
│ ─────────────────────────────────────────────────────────── │
│ • log_aktifitas_driver       - Driver activity logs       │
│ • log_chat                   - Chat activity logs         │
│ • log_panggilan              - Call logs                  │
│ • log_perangkat              - Device logs                │
│ • log_perjalanan_armada      - Vehicle journey logs       │
│ • log_sensor                 - Sensor data logs           │
│ • log_service                - Service logs               │
│                                                             │
│ FINANCIAL & PAYMENT (5 tables)                             │
│ ─────────────────────────────────────────────────────────── │
│ • mata_uang                  - Currency definitions       │
│ • metode_pembayaran          - Payment methods            │
│ • pembayaran_fee             - Fee payments               │
│ • rekening_driver            - Driver bank accounts       │
│ • suppliers                  - Supplier information       │
│                                                             │
│ WAREHOUSE & INVENTORY (5 tables)                           │
│ ─────────────────────────────────────────────────────────── │
│ • lokasi_rak                 - Shelf/rack locations       │
│ • produk                     - Product master             │
│ • produk_gudang              - Warehouse stock            │
│ • satuan                     - Unit of measure            │
│ • stok                       - Stock levels               │
│ • stok_movement              - Stock transaction          │
│                                                             │
│ STATUS & CONFIGURATION (4 tables)                          │
│ ─────────────────────────────────────────────────────────── │
│ • status_armada              - Vehicle status types       │
│ • status_gudang              - Warehouse status           │
│ • status_qc                  - QC status types            │
│ • tenant                     - Multi-tenant config        │
│                                                             │
│ USER MANAGEMENT (2 tables)                                 │
│ ─────────────────────────────────────────────────────────── │
│ • user_role                  - User-role assignment       │
│ • user_tenant                - User-tenant assignment     │
│                                                             │
│ ALERTS & REPORTING (2 tables)                              │
│ ─────────────────────────────────────────────────────────── │
│ • alert_geofence             - Geofence alerts            │
│ • laporan_darurat            - Emergency reports          │
│ • laporan_pengemudi          - Driver reports             │
│                                                             │
│ MISCELLANEOUS (2 tables)                                   │
│ ─────────────────────────────────────────────────────────── │
│ • weather                    - Historical weather data    │
│ • z_test                     - Test/sandbox data          │
└─────────────────────────────────────────────────────────────┘
```

**To see all 90 tables:**

```sql
SELECT tablename FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename;

-- Expected output: 90 rows
```

---

### Schema 2: `weather` - BMKG API Data (3 Tables)

**Purpose:** Hourly weather data from BMKG API  
**Owner:** postgres  
**Size:** 100-500MB  
**Update Frequency:** Every hour (via weather_data_fetch DAG)  
**Retention:** 30-day rolling window (auto-cleanup)

#### Table 1: fact_weather_hourly

**Purpose:** Hourly weather snapshots  
**Grain:** One record per location per hour  
**Partitioning:** None (30-day window, manageable size)

```sql
CREATE TABLE weather.fact_weather_hourly (
    weather_id SERIAL PRIMARY KEY,
    adm4 VARCHAR(20) NOT NULL,              -- Administrative code
    lokasi VARCHAR(100) NOT NULL,           -- Location name  
    desa VARCHAR(100),                      -- Village
    kecamatan VARCHAR(100),                 -- Sub-district
    kabupaten VARCHAR(100),                 -- Regency/city
    provinsi VARCHAR(100),                  -- Province
    waktu TIMESTAMP NOT NULL,               -- Forecast time
    cuaca VARCHAR(200),                     -- Weather description
    suhu_celsius DECIMAL(5, 2),             -- Temperature (°C)
    kelembapan INT,                         -- Humidity (%)
    arah_angin VARCHAR(50),                 -- Wind direction  
    kecepatan_angin DECIMAL(5, 2),          -- Wind speed (km/h)
    freshness_status VARCHAR(20),           -- FRESH/WARNING/STALE
    created_at TIMESTAMP DEFAULT NOW(),     -- Record creation time
    updated_at TIMESTAMP DEFAULT NOW(),     -- Last update
    UNIQUE(adm4, waktu)
);

-- Performance indexes
CREATE INDEX ix_weather_location_time 
    ON weather.fact_weather_hourly (adm4, waktu DESC);
CREATE INDEX ix_weather_freshness 
    ON weather.fact_weather_hourly (freshness_status);
CREATE INDEX ix_weather_created 
    ON weather.fact_weather_hourly (created_at DESC);
```

**Sample Data:**

```
adm4           | lokasi      | suhu_celsius | kelembapan | waktu
───────────────┼─────────────┼──────────────┼────────────┼─────────────────────────
35.78.21.1004  | Jakarta     | 28.5         | 72         | 2026-04-13 10:00:00
35.78.21.1004  | Jakarta     | 29.2         | 70         | 2026-04-13 11:00:00
35.25.14.1010  | Bandung     | 24.8         | 65         | 2026-04-13 10:00:00
```

**Data Cleanup:**

```sql
-- Auto-cleanup in weather_data_fetch DAG
DELETE FROM weather.fact_weather_hourly 
WHERE created_at < NOW() - INTERVAL '30 days';
```

#### Table 2: dim_locations

**Purpose:** Weather location dimension  
**Grain:** One record per location

```sql
CREATE TABLE weather.dim_locations (
    location_id SERIAL PRIMARY KEY,
    adm4 VARCHAR(20) NOT NULL UNIQUE,       -- ADM4 code
    location_name VARCHAR(100) NOT NULL,    -- Display name
    province VARCHAR(100),                  -- Province name
    city_regency VARCHAR(100),              -- City/regency name
    latitude DECIMAL(10, 8),                -- Latitude coordinate
    longitude DECIMAL(11, 8),               -- Longitude coordinate
    elevation_m INT,                        -- Elevation (meters)
    timezone VARCHAR(50),                   -- Timezone (Asia/Jakarta)
    active BOOLEAN DEFAULT TRUE,             -- Is location active
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Table 3: daily_weather_summary

**Purpose:** Daily aggregated weather  
**Grain:** One record per location per day

```sql
CREATE TABLE weather.daily_weather_summary (
    summary_id SERIAL PRIMARY KEY,
    adm4 VARCHAR(20),                       -- Location code
    summary_date DATE NOT NULL,              -- Date
    temp_min DECIMAL(5, 2),                 -- Min temperature
    temp_max DECIMAL(5, 2),                 -- Max temperature
    temp_avg DECIMAL(5, 2),                 -- Avg temperature
    humidity_avg INT,                       -- Avg humidity
    wind_speed_avg DECIMAL(5, 2),           -- Avg wind speed
    total_precipitation DECIMAL(8, 3),      -- Total precipitation (mm)
    weather_description VARCHAR(200),       -- Dominant weather
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(adm4, summary_date)
);
```

---

### Schema 3: `analytics` - KPIs & Metrics (2 Tables)

**Purpose:** Business metrics and KPIs  
**Owner:** postgres  
**Size:** 50-200MB  
**Update Frequency:** Daily (if configured)

#### Table 1: kpi_daily_summary

```sql
CREATE TABLE analytics.kpi_daily_summary (
    kpi_date DATE PRIMARY KEY,
    total_deliveries INT,                   -- Delivery count
    total_distance_km DECIMAL(10, 2),       -- Total distance
    total_orders INT,                       -- Order count
    avg_delivery_time_hours DECIMAL(5, 2), -- Avg delivery time
    active_drivers INT,                     -- Active drivers
    active_vehicles INT,                    -- Active vehicles
    on_time_delivery_rate DECIMAL(5, 2),    -- On-time % 
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Table 2: driver_performance_metrics

```sql
CREATE TABLE analytics.driver_performance_metrics (
    metric_id SERIAL PRIMARY KEY,
    driver_id INT,                          -- Driver ID (FK)
    metric_month DATE,                      -- Month (first day)
    total_trips INT,                        -- Trip count
    total_distance_km DECIMAL(10, 2),       -- Distance driven
    on_time_rate DECIMAL(5, 2),             -- On-time %
    safety_score DECIMAL(5, 2),             -- Safety rating (0-100)
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(driver_id, metric_month)
);
```

---

## All 90 Tables

**Complete alphabetical list of all business tables:**

```
1.  alert_geofence
2.  armada_perangkat
3.  armada_tms
4.  atribut
5.  atribut_produk
6.  attachment
7.  attachment_armada
8.  attachment_chat
9.  attachment_driver
10. attachment_gudang
11. attachment_pengembalian
12. attachment_perangkat
13. attachment_qc
14. bank
15. chat_room
16. customers
17. daftar_user
18. delivery_order
19. detail_do
20. detail_po
21. detail_qc
22. detail_sm
23. detail_so
24. driver_armada
25. geofence
26. gudang
27. jenis_armada
28. jenis_file
29. jenis_insiden
30. jenis_notifikasi
31. jenis_order
32. jenis_satuan
33. jenis_transaksi
34. kategori_produk
35. kontak_darurat
36. konversi
37. kriteria_produk
38. language
39. language_text
40. laporan_darurat
41. laporan_pengemudi
42. locations
43. log_aktifitas_driver
44. log_chat
45. log_panggilan
46. log_perangkat
47. log_perjalanan_armada
48. log_sensor
49. log_service
50. lokasi_rak
51. mata_uang
52. metode_pembayaran
53. notifikasi
54. order_tms
55. orders
56. parent_armada
57. pembayaran_fee
58. pengembalian
59. pengingat_pemeliharaan_armada
60. perangkat
61. perangkat_gps_driver
62. produk
63. produk_gudang
64. purchase_order
65. quality_control
66. rating
67. rekening_driver
68. role
69. room_last_read
70. room_members
71. rute
72. rute_perangkat
73. sales_order
74. satuan
75. status_armada
76. status_gudang
77. status_order
78. status_qc
79. status_user
80. stok
81. stok_movement
82. suppliers
83. tempat_istirahat_driver
84. tenant
85. units
86. user_role
87. user_tenant
88. weather
89. z_test
```

**Total: 89 tables (z_test is test/sandbox data)**

---

## Key Tables

### Top 10 Most Important Tables

| # | Table | Rows | Purpose | Update |
|---|-------|------|---------|--------|
| 1 | orders | 50K-500K | Sales orders master | Daily |
| 2 | delivery_order | 50K-500K | Delivery assignments | Daily |
| 3 | detail_do | 100K-1M | Delivery order lines | Daily |
| 4 | log_perjalanan_armada | 100K-500K | Vehicle trip logs | Daily |
| 5 | log_aktifitas_driver | 100K-500K | Driver activity | Daily |
| 6 | customers | 1K-10K | Customer master | Daily |
| 7 | armada_perangkat | 100-1K | Vehicle equipment | Daily |
| 8 | perangkat | 100-1K | GPS/IoT devices | Daily |
| 9 | fact_weather_hourly | 50K-200K | Weather (30-day) | Hourly |
| 10 | stok | 10K-100K | Inventory levels | Daily |

---

## Data Growth & Maintenance

### Estimated Monthly Growth

```
orders                    +10K-50K rows
delivery_order            +10K-50K rows
log_* tables              +200K-500K rows
detail_do/po/so/qc/sm    +50K-200K rows
Chat/notification tables  +50K-200K rows
──────────────────────────────────────
TOTAL:                    ~500K-2M rows/month
Storage impact:           ~100-500MB/month
Yearly growth:            ~1.2-6GB/year
```

### Archive Strategy

#### Weather Data (30-day auto-cleanup)

```sql
-- Automatic in weather_data_fetch DAG
DELETE FROM weather.fact_weather_hourly
WHERE created_at < NOW() - INTERVAL '30 days';
```

#### Business Data (Keep 2-3 years)

```sql
-- Manual archive (not yet automated)
-- Consider archiving old log_* tables for performance
DELETE FROM log_perjalanan_armada 
WHERE YEAR(start_time) < 2024;
```

---

## Useful Queries

### Total Size by Schema

```sql
SELECT 
    schemaname,
    pg_size_pretty(SUM(pg_total_relation_size(schemaname||'.'||tablename))) as total_size
FROM pg_tables 
WHERE schemaname IN ('public', 'weather', 'analytics')
GROUP BY schemaname
ORDER BY SUM(pg_total_relation_size(schemaname||'.'||tablename)) DESC;
```

### Top 10 Largest Tables

```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    n_live_tup as row_count
FROM pg_tables
LEFT JOIN pg_stat_user_tables USING (tablename)
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
```

### List All Tables with Row Counts

```sql
SELECT 
    schemaname,
    tablename,
    n_live_tup as row_count,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_stat_user_tables
WHERE schemaname IN ('public', 'weather', 'analytics')
ORDER BY schemaname, tablename;
```

### Count Tables in Each Schema

```sql
SELECT 
    schemaname,
    COUNT(*) as table_count
FROM pg_tables 
WHERE schemaname IN ('public', 'weather', 'analytics')
GROUP BY schemaname;

-- Expected output:
-- schemaname | table_count
-- ────────────┼─────────────
-- public     | 89
-- weather    | 3
-- analytics  | 2
```

---

📖 **Next:** Read [Architecture Guide](ARCHITECTURE.md) for system design  
👈 **Back to:** [Main README](../README.md)
