# 🚀 Airflow Stack - Platform Data Warehouse & Weather Analytics

> **Platform orchestration data production-ready dengan Apache Airflow, PostgreSQL warehouse, dan analytics dashboard terintegrasi**

![Airflow 3.1.3](https://img.shields.io/badge/Apache%20Airflow-3.1.3-blue)
![Python 3.13](https://img.shields.io/badge/Python-3.13-green)
![PostgreSQL 18](https://img.shields.io/badge/PostgreSQL-18-336791)
![Docker Compose](https://img.shields.io/badge/Docker%20Compose-Latest-2496ED)

## 📑 Table of Contents

- [About Project](#-about-project)
- [Quick Start](#-quick-start)
- [How It Works](#-how-it-works)
- [DAGs & Data Pipelines](#-dags--data-pipelines)
- [Documentation](#-documentation)

---

## About Project

**Airflow Stack** adalah platform data orchestration lengkap untuk sinkronisasi data warehouse dan weather analytics:

- **Apache Airflow 3.1.3** - Scheduler & task orchestration
- **PostgreSQL Warehouse** - Database central untuk semua data
- **BMKG Weather API** - Real-time data cuaca (update per 2 jam)
- **Multi-Dashboard** - Metabase, Grafana, Superset untuk analytics
- **ETL Automated** - Sinkronisasi 90+ tabel dari devom.silog.co.id (harian otomatis)

### 🎯 Use Cases

| Kebutuhan | DAG | Schedule |
|-----------|-----|----------|
| Sinkronisasi data harian | `daily_warehouse_sync` | **Daily 00:00 UTC** |
| Data cuaca real-time | `weather_data_fetch` | **Every 1 hour** |
| Sync app database | `sync_data_from_app` | **Manual trigger** |

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Bash shell
- Terminal

### Step 1: Start Stack

```bash
cd /home/rafie/airflow-stack
bash scripts/utils/quick_start.sh
```

Tunggu sampai melihat output "✅ Services ready" (~2-3 menit)

### Step 2: Access Airflow UI

Buka browser → `http://localhost:8080`

**Login:**
```
Username: admin
Password: (sesuai hasil generate json)
```

### Step 3: Setup Database (first time only)

```bash
bash scripts/setup/setup_warehouse_db.sh
bash scripts/etl/copy_devom_structure.sh
```

### Step 4: Trigger First DAG

Di Airflow UI:
1. Klik DAG `daily_warehouse_sync`
2. Klik tombol **Trigger DAG**
3. Monitor di **Graph View**

👉 **Dokumentasi lengkap:** [📖 Setup Guide](docs/INSTALLATION.md)

---

## How It Works

**Alur Data:**

1. **Data Sources** → DEVOM warehouse (90+ tabel) + BMKG API (cuaca)
2. **Airflow Scheduler** → Trigger DAG sesuai jadwal (harian & per jam)
3. **ETL Pipeline** → Fetch data dari source → Clean & Transform → Insert ke warehouse
4. **PostgreSQL Warehouse** → Central database dengan 3 schema: public, weather, analytics
5. **Analytics Dashboards** → Metabase, Grafana, Superset query data warehouse

**Komponen Utama:**
- **PostgreSQL (port 5433)** - Data warehouse production
- **PostgreSQL (port 5432)** - Airflow metadata database
- **Redis/Valkey** - Message broker untuk task queue
- **Airflow (port 8080)** - Scheduler & monitoring UI

👉 [📖 Detail arsitektur](docs/ARCHITECTURE.md)

---

## DAGs & Data Pipelines

### 1️⃣ **daily_warehouse_sync** - Daily Data Sync

| Property | Value |
|----------|-------|
| **Schedule** | Daily 00:00 UTC (07:00 WIB) |
| **Fungsi** | Sync 90+ tabel dari DEVOM ke warehouse |
| **Processing** | Batch 5,000 rows, auto-dedup |
| **Retry** | 2x jika gagal (delay 5 menit) |

**Pipeline:** Check weather → Sync tables → Verify data

---

### 2️⃣ **weather_data_fetch** - Real-time Weather Data

| Property | Value |
|----------|-------|
| **Schedule** | Every hour (00:00-23:00 UTC) |
| **Fungsi** | Fetch BMKG API → store dengan freshness tracking |
| **Data** | Multi-location Indonesia |
| **Retention** | 30 hari rolling window |

**Status Cuaca:**
- ✅ FRESH (≤ 60 min) | ⚠️ WARNING (60-180 min) | ❌ STALE (> 180 min)

---

### 3️⃣ **sync_data_from_app** - App Database Sync

| Property | Value |
|----------|-------|
| **Schedule** | Manual trigger (on-demand) |
| **Fungsi** | Bridge app DB → Airflow DB untuk ETL |

---

## Dashboard Tools

| Tool | Port | Function |
|------|------|--------|
| **Metabase** | 3000 | BI & exploratory analytics |
| **Grafana** | 3001 | Monitoring & real-time dashboards |
| **Superset** | 8088 | Advanced data exploration |

```bash
# Start tools
bash scripts/metabase/start_metabase.sh
bash scripts/grafana/start_grafana.sh
bash scripts/superset/start_superset.sh
```

👉 [📖 Detail dashboard setup](docs/DASHBOARDS.md)

---

## Documentation

| Document | Content |
|---------|-----|
| [📖 Installation Guide](docs/INSTALLATION.md) | Setup step-by-step |
| [📖 DAGs Reference](docs/DAGS.md) | Detail pipeline & task |
| [📖 Architecture](docs/ARCHITECTURE.md) | Diagram & flow data |
| [📖 Database Schema](docs/DATABASE_SCHEMA.md) | Struktur tabel & relasi |
| [📖 Dashboard Setup](docs/DASHBOARDS.md) | Config Metabase/Grafana/Superset |
| [📖 Scripts](docs/SCRIPTS.md) | Referensi shell scripts |
| [📖 API Integration](docs/API_INTEGRATION.md) | BMKG API & DEVOM connection |
| [📖 Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues & solusi |
| [📖 Index](docs/INDEX.md) | Navigasi dokumentasi lengkap |

👉 **Baca dokumentasi sesuai kebutuhan di [docs/INDEX.md](docs/INDEX.md)**

---

## 🔧 Helper Scripts

```bash
# Startup
bash scripts/utils/quick_start.sh                      # Start semua services
bash scripts/setup/setup_warehouse_db.sh               # Setup DB pertama kali
bash scripts/etl/copy_devom_structure.sh               # Copy tabel dari DEVOM

# Dashboard tools
bash scripts/metabase/start_metabase.sh                # Start Metabase
bash scripts/grafana/start_grafana.sh                  # Start Grafana
bash scripts/superset/start_superset.sh                # Start Superset
```

👉 [📖 Detail scripts reference](docs/SCRIPTS.md)

---

## 🗄️ Database Configuration

```
WAREHOUSE DATABASE
  Host: localhost:5433
  User: postgres | Password: postgres123
  Schemas: public (90+ tbl), weather, analytics

AIRFLOW METADATA
  Host: postgres:5432
  User: airflow | Password: airflow

SOURCE: DEVOM
  Host: devom.silog.co.id:5432
  User: om | Password: om
```

---

## System Requirements

| Component | Version |
|----------|---------|
| Docker | Latest |
| Docker Compose | Latest |
| Apache Airflow | 3.1.3 |
| PostgreSQL | 18 |
| Redis/Valkey | 9 |

---

## Next Steps

1. **✅ [Start stack](#-quick-start-5-minutes)** - Ikuti quick start
2. **📖 [Baca setup guide](docs/INSTALLATION.md)** - Pemahaman lebih lengkap
3. **📖 [Pelajari DAGs](docs/DAGS.md)** - Pahami pipeline data
4. **📖 [Setup dashboard](docs/DASHBOARDS.md)** - Buat analytics dashboard
5. **🎯 [Monitoring & troubleshooting](docs/TROUBLESHOOTING.md)** - Jika ada masalah

## Project Info

**Platform:** Airflow Stack Data Warehouse  
**Version:** 1.0.0  
**Built with:** Apache Airflow, PostgreSQL, Docker, Python  
**Data Sources:** BMKG API, devom.silog.co.id warehouse  
**Status:** ✅ Production Ready

---

**Last Updated:** April 2026
