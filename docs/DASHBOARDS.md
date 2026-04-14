# 📊 Dashboards & Analytics Tools

**Connect Metabase, Grafana, and Superset to warehouse analytics**

---

## 📑 Table of Contents

- [Overview](#overview)
- [Metabase (Port 3000)](#metabase-port-3000)
- [Grafana (Port 3001)](#grafana-port-3001)  
- [Apache Superset (Port 8088)](#apache-superset-port-8088)
- [Tool Comparison](#tool-comparison)
- [Troubleshooting](#troubleshooting)

---

## Overview

Three analytics platforms connect to **warehouse database** (localhost:5433) containing 90+ DEVOM business tables + weather data:

| Tool | Port | Purpose | Best For |
|------|------|---------|----------|
| **Metabase** | 3000 | SQL + visual dashboards | Business users, quick reports |
| **Grafana** | 3001 | Real-time monitoring & alerts | System health, KPI tracking |
| **Superset** | 8088 | Advanced analytics & exploration | Data analysts, complex queries |

✅ **Connection:** `postgresql://postgres:postgres123@localhost:5433/warehouse`

---

## Metabase (Port 3000)

### Starting Metabase

```bash
bash scripts/metabase/start_metabase.sh
# Access: http://localhost:3000
```

### First-Time Setup

**Step 1: Create Admin Account**
- Email: `admin@warehouse.local`
- Password: Your choice (min 8 chars)
- Click "Let's get started"

**Step 2: Add Database Connection**
1. Settings (⚙️) → Admin Settings → Databases
2. Click "Add Database" → PostgreSQL
3. Configure:
   ```
   Display Name:    Warehouse
   Host:            localhost
   Port:            5433
   Database Name:   warehouse
   Username:        postgres
   Password:        postgres123
   ```
4. Test Connection → Save

**Step 3: Verify Tables**
1. **+ New** → **SQL Query**
2. Run:
   ```sql
   SELECT COUNT(*) as total_tables 
   FROM information_schema.tables 
   WHERE table_schema = 'public';
   ```
3. Should show 90+ tables

### Creating Dashboards

1. **+ New** → **Dashboard**
2. Name it (e.g., "Warehouse Health")
3. Click **Edit** → **Add a card**
4. Create from SQL query or existing table
5. **Save**

### Sample Queries

**Warehouse Health:**
```sql
SELECT
    tablename,
    n_live_tup as row_count,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_live_tup DESC
LIMIT 20;
```

**Weather Data Status:**
```sql
SELECT
    location,
    MAX(data_timestamp) as latest_data,
    NOW() - MAX(data_timestamp) as age,
    COUNT(*) as records,
    freshness_status
FROM weather.fact_weather_hourly
WHERE data_timestamp >= CURRENT_DATE - 7
GROUP BY location, freshness_status
ORDER BY location, latest_data DESC;
```

### Stopping Metabase

```bash
bash scripts/metabase/stop_metabase.sh
```

---

## Grafana (Port 3001)

### Starting Grafana

```bash
bash scripts/grafana/start_grafana.sh
# Access: http://localhost:3001
# Default: admin / admin
```

### First-Time Setup

**Step 1: Change Default Password**
- Login with admin/admin
- You'll be prompted to change password
- Set new password → Save

**Step 2: Add PostgreSQL Data Source**
1. Configuration (⚙️) → Data Sources
2. Add Data Source → PostgreSQL
3. Configure:
   ```
   Name:          Warehouse
   Host:          localhost:5433
   Database:      warehouse
   User:          postgres
   Password:      postgres123
   SSL Mode:      disable
   ```
4. Test Connection → Save

**Step 3: Create Dashboard**
1. **+ Dashboard**
2. **Add a new panel**
3. Write query → Choose visualization → Save

### Sample Panel Queries

**Dashboard: System Health (Gauge)**
```sql
SELECT
    COUNT(*) as total_tables,
    SUM(n_live_tup) as total_records
FROM pg_stat_user_tables
WHERE schemaname = 'public';
```

**Panel: Weather Data Freshness (Time Series)**
```sql
SELECT
    DATE(data_timestamp) as date,
    location,
    COUNT(*) as records
FROM weather.fact_weather_hourly
WHERE data_timestamp >= CURRENT_DATE - 30
GROUP BY DATE(data_timestamp), location
ORDER BY date DESC;
```

### Stopping Grafana

```bash
bash scripts/grafana/stop_grafana.sh
```

---

## Apache Superset (Port 8088)

### Starting Superset

```bash
bash scripts/superset/start_superset.sh
# Access: http://localhost:8088
# Default: admin / admin
```

### First-Time Setup

**Step 1: Change Password**
- Login with admin/admin
- Settings (👑) → Password
- Enter new password

**Step 2: Add Database**
1. Settings → Database Connections
2. Click **+ Database**
3. Enter:
   ```
   Database Name:   warehouse
   SQLAlchemy URI:  postgresql://postgres:postgres123@localhost:5433/warehouse
   ```
4. Test Connection → Save

**Step 3: Create Chart**
1. **+ Chart**
2. Select Database → Select Table
3. Choose Visualization Type
4. Configure columns & metrics
5. Save

### Using SQL Lab

1. **SQL** → **SQL Lab**
2. Write query:
   ```sql
   SELECT schemaname, tablename, n_live_tup, n_tup_ins, n_tup_upd, n_tup_del
   FROM pg_stat_user_tables
   WHERE schemaname = 'public'
   ORDER BY n_live_tup DESC
   LIMIT 20;
   ```
3. Execute → Visualize

### Stopping Superset

```bash
bash scripts/superset/stop_superset.sh
```

---

## Tool Comparison

| Feature | Metabase | Grafana | Superset |
|---------|----------|---------|----------|
| **Setup Time** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **User Friendly** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **SQL Queries** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Real-time Data** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Alerting** | Limited | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Visualizations** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### When to Use Each

**Use Metabase** if:
- ✅ Non-technical users need dashboards
- ✅ Want quick SQL queries
- ✅ Need simple visualizations
- ✅ Team size: small to medium

**Use Grafana** if:
- ✅ Need real-time monitoring
- ✅ Want advanced alerting
- ✅ Monitoring system metrics
- ✅ Team: DevOps/Infrastructure

**Use Superset** if:
- ✅ Need advanced analytics
- ✅ Complex queries & aggregations
- ✅ Want semantic layer
- ✅ Team: Data analysts

---

## Troubleshooting

### Metabase Connection Failed

```bash
# 1. Verify warehouse is running
docker ps | grep postgres

# 2. Test connection manually
psql -h localhost -U postgres -d warehouse -p 5433

# 3. Check logs
docker-compose logs metabase | tail -20
```

### No Tables Visible in Dashboard Tools

```bash
# 1. Verify tables exist
SELECT COUNT(*) FROM information_schema.tables 
WHERE table_schema = 'public';

# 2. If 0 tables, run setup
bash scripts/setup/setup_warehouse_db.sh
bash scripts/etl/copy_devom_structure.sh

# 3. Refresh data source connection in dashboard tool
```

### Queries Running Slowly

```bash
# Add indexes for common queries
CREATE INDEX idx_weather_timestamp ON weather.fact_weather_hourly(data_timestamp);
CREATE INDEX idx_weather_location ON weather.fact_weather_hourly(location);

# Run VACUUM to optimize
VACUUM ANALYZE warehouse;
```

---

📖 **Related:** [DAGs Reference](DAGS.md) | [Database Schema](DATABASE_SCHEMA.md) | [Architecture](ARCHITECTURE.md)  
👈 **Back to:** [Main README](../README.md) | [Documentation Index](INDEX.md)
