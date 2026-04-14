#!/bin/bash

# ============================================================================
# QUICK GUIDE: DATABASE WAREHOUSE SETUP
# ============================================================================

cat << 'EOF'

╔════════════════════════════════════════════════════════════════════════╗
║                   🎯 DATABASE WAREHOUSE GUIDE                          ║
╚════════════════════════════════════════════════════════════════════════╝

┌────────────────────────────────────────────────────────────────────────┐
│ 📊 ARSITEKTUR DATA WAREHOUSE                                           │
└────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────┐
    │  BMKG Weather API   │
    │  api.bmkg.go.id     │
    └──────────┬──────────┘
               │ Fetch (per jam)
               │ Airflow DAG: weather_data_fetch
               ▼
    ┌──────────────────────────────────────────┐
    │     DATABASE WAREHOUSE                   │
    │     localhost:5433/warehouse             │
    │                                          │
    │  ┌────────────┐    ┌────────────────┐  │
    │  │  weather   │    │  public        │  │
    │  │  (cuaca)   │    │  (perusahaan)  │  │
    │  └────────────┘    └────────────────┘  │
    │                                          │
    └──────────────────────────────────────────┘
               ▲
               │ Sync (harian)
               │ Airflow DAG: daily_warehouse_sync
    ┌──────────┴──────────┐
    │  DEVOM Source DB    │
    │  devom.silog.co.id  │
    └─────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│ 🔐 KREDENSIAL UNTUK pgAdmin4                                           │
└────────────────────────────────────────────────────────────────────────┘

📍 SERVER 1: WAREHOUSE (Database Utama - Target Analytics)
   ┌──────────────────────────────────────────────┐
   │ Name     : WAREHOUSE                         │
   │ Host     : localhost                         │
   │ Port     : 5433                              │
   │ Database : warehouse                         │
   │ Username : postgres                          │
   │ Password : postgres123                       │
   └──────────────────────────────────────────────┘

📍 SERVER 2: DEVOM-SOURCE (Database Source - Perusahaan)
   ┌──────────────────────────────────────────────┐
   │ Name     : DEVOM-SOURCE                      │
   │ Host     : devom.silog.co.id                 │
   │ Port     : 5432                              │
   │ Database : om                                │
   │ Username : om                                │
   │ Password : om                                │
   └──────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│ 🚀 CARA SETUP (3 LANGKAH)                                              │
└────────────────────────────────────────────────────────────────────────┘

STEP 1: Setup Database Warehouse
   $ bash setup_warehouse_db.sh

STEP 2: Register Server di pgAdmin4
   1. Buka pgAdmin4
   2. Right-click Servers → Register → Server
   3. Tab General:
      - Name: WAREHOUSE
   4. Tab Connection:
      - Host: localhost
      - Port: 5433
      - Database: warehouse
      - Username: postgres
      - Password: postgres123
   5. Save

STEP 3: Verify Connection
   Connect ke WAREHOUSE di pgAdmin4, jalankan:
   
   SELECT schema_name 
   FROM information_schema.schemata 
   WHERE schema_name IN ('public', 'weather', 'analytics');
   
   Expected result: 3 schemas (public, weather, analytics)

┌────────────────────────────────────────────────────────────────────────┐
│ 📋 ISI DATABASE WAREHOUSE                                              │
└────────────────────────────────────────────────────────────────────────┘

Schema: weather (Data Cuaca BMKG)
   ├── fact_weather_hourly        ← Forecast cuaca per jam
   ├── dim_weather_location       ← Master lokasi cuaca
   ├── v_forecast_7days           ← View: forecast 7 hari
   └── v_current_weather          ← View: cuaca terkini

Schema: public (Data Perusahaan dari DEVOM)
   ├── driver                     ← Master data driver
   ├── armada                     ← Master data kendaraan
   ├── perjalanan                 ← Data perjalanan
   ├── gps_tracking               ← Data GPS tracking
   └── ... (semua tabel dari devom.silog.co.id)

Schema: analytics (Data Analytics & KPI)
   ├── fact_driver_performance    ← KPI driver
   └── driver_weather_correlation ← Korelasi driver & cuaca

┌────────────────────────────────────────────────────────────────────────┐
│ 🔄 AUTO-UPDATE MECHANISM                                               │
└────────────────────────────────────────────────────────────────────────┘

✅ Data Perusahaan (DEVOM → WAREHOUSE)
   DAG     : daily_warehouse_sync
   Schedule: Harian jam 00:00 WIB
   Action  : Sync semua tabel dari devom ke warehouse.public

✅ Data Cuaca (BMKG API → WAREHOUSE)
   DAG     : weather_data_fetch
   Schedule: Setiap jam (00:00, 01:00, ..., 23:00)
   Action  : Fetch forecast dari BMKG ke warehouse.weather

📊 HASIL: Semua data terpusat di database WAREHOUSE
   - Input baru di DEVOM → sync otomatis ke WAREHOUSE (harian)
   - Data cuaca baru → fetch otomatis ke WAREHOUSE (per jam)

┌────────────────────────────────────────────────────────────────────────┐
│ 📖 DOKUMENTASI LENGKAP                                                 │
└────────────────────────────────────────────────────────────────────────┘

📄 RINGKASAN_DATABASE.md         → Panduan singkat
📄 DATABASE_CONFIG.md            → Dokumentasi lengkap arsitektur
📄 sql/05_create_weather_schema.sql → DDL schema weather
📄 airflow/dags/weather_data_fetch.py → DAG fetch cuaca

┌────────────────────────────────────────────────────────────────────────┐
│ 🎯 KESIMPULAN                                                          │
└────────────────────────────────────────────────────────────────────────┘

Anda punya 1 DATABASE WAREHOUSE yang berisi:
   ✅ Data perusahaan dari devom.silog.co.id
   ✅ Data cuaca dari BMKG API
   ✅ Data analytics hasil olahan
   ✅ Semua auto-update via Airflow DAG

Credentials pgAdmin4:
   Host: localhost:5433
   Database: warehouse
   User: postgres
   Password: postgres123

EOF

# Tanyakan apakah user ingin setup sekarang
echo ""
read -p "🤔 Ingin setup database warehouse sekarang? (y/n): " answer

if [ "$answer" == "y" ] || [ "$answer" == "Y" ]; then
    echo ""
    echo "🚀 Menjalankan setup..."
    bash setup_warehouse_db.sh
else
    echo ""
    echo "📌 Untuk setup nanti, jalankan:"
    echo "   bash setup_warehouse_db.sh"
    echo ""
fi
