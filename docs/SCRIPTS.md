# 📖 Scripts Reference

**Utility scripts for setup, maintenance, and data operations**

---

## 📑 Table of Contents

- [Quick Start](#quick-start)
- [Setup Scripts](#setup-scripts)
- [ETL Scripts](#etl-scripts)
- [Service Management](#service-management)
- [Python Utilities](#python-utilities)

---

## Quick Start

**Fastest way to start the entire system:**

```bash
cd /home/rafie/airflow-stack

# Option 1: Use quick_start.sh
bash scripts/utils/quick_start.sh

# Option 2: Manual
docker-compose up -d
```

---

## Setup Scripts

### scripts/setup/setup_warehouse_db.sh

**Initialize PostgreSQL warehouse (localhost:5433)**

```bash
bash scripts/setup/setup_warehouse_db.sh
```

Creates: `warehouse` database with `public`, `weather`, `analytics` schemas

### scripts/setup/setup_metabase_db.sh

**Configure Metabase BI tool**

```bash
bash scripts/setup/setup_metabase_db.sh
```

---

## ETL Scripts

### scripts/etl/sync_tables_from_devom.sh

**Manual sync of 90 DEVOM tables**

```bash
bash scripts/etl/sync_tables_from_devom.sh
```

### scripts/etl/copy_devom_structure.sh

**Copy schema structure only (no data)**

```bash
bash scripts/etl/copy_devom_structure.sh
```

### scripts/etl/migrate_to_single_schema.sh

**Migrate to single-schema architecture**

```bash
bash scripts/etl/migrate_to_single_schema.sh
```

---

## Service Management

### Airflow
- **Stop:** `bash scripts/airflow/stop_airflow_podman.sh`

### Metabase (Port 3000)
- **Start:** `bash scripts/metabase/start_metabase.sh`
- **Stop:** `bash scripts/metabase/stop_metabase.sh`

### Grafana (Port 3001)
- **Start:** `bash scripts/grafana/start_grafana.sh`
- **Stop:** `bash scripts/grafana/stop_grafana.sh`

### Superset (Port 8088)
- **Start:** `bash scripts/superset/start_superset.sh`
- **Stop:** `bash scripts/superset/stop_superset.sh`

---

## Python Utilities

| Script | Purpose |
|--------|---------|
| `fetch_weather_bmkg.py` | Fetch weather from BMKG API |
| `sync_data_from_app.py` | Sync app data to Airflow DB |
| `sync_all_devom_tables.py` | Full 90-table sync |
| `list_source_tables.py` | List DEVOM tables |
| `copy_devom_structure.py` | Copy schema (Python) |
| `console_fetch_weather.py` | Interactive weather fetch |

---

## Utilities

- **quick_start.sh** - One-command startup
- **dashboard_options.sh** - Menu-driven dashboard launcher
- **panduan_database.sh** - Database management utilities
- **note.sh** - Quick notes

---

📖 **See Also:** [Dashboards](DASHBOARDS.md) | [Installation](INSTALLATION.md)  
👈 **Back:** [Main README](../README.md)
