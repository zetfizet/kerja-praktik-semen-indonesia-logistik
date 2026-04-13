# 📋 Troubleshooting & Common Issues

**Common problems in Airflow Stack and their solutions**

---

## 📑 Quick Index

- [Connection Issues](#connection-issues)
- [Database Problems](#database-problems)
- [DAG & Airflow Issues](#dag--airflow-issues)
- [Dashboard Tool Issues](#dashboard-tool-issues)
- [Data Quality Issues](#data-quality-issues)
- [Performance Issues](#performance-issues)
- [Getting Help](#getting-help)

---

## Connection Issues

### Cannot Connect to DEVOM (devom.silog.co.id)

**Symptoms:**
- daily_warehouse_sync fails at first task
- "Name or service not known" or "Connection timed out"

**Solutions:**

```bash
# 1. Test connectivity from localhost
ping devom.silog.co.id

# 2. If fails, check VPN/network (ask team)

# 3. Test PostgreSQL connection
psql -h devom.silog.co.id -U om -d om -p 5432

# 4. Check from inside Airflow container
docker-compose exec airflow-scheduler bash
ping devom.silog.co.id
psql -h devom.silog.co.id -U om -d om -p 5432
```

**Prevention:**
- Ensure VPN/network is set up before running DAGs
- Verify credentials (om/om) are correct
- Test connectivity before triggering sync

---

### Cannot Connect to Warehouse (localhost:5433)

**Symptoms:**
- DAG fails with "Could not connect to server"
- Metabase/Grafana can't reach database
- Poetry install fails psycopg2 connection

**Solutions:**

```bash
# 1. Check if PostgreSQL is running
docker ps | grep postgres

# 2. If not running, start it
bash scripts/utils/quick_start.sh

# 3. Test connection
psql -h localhost -U postgres -d warehouse -p 5433
# Password: postgres123

# 4. If connection timeout, check logs
docker-compose logs postgres | tail -20

# 5. Check if port is correct
grep -E 'ports:|5433' compose.yml
```

**Prevention:**
- Always start with `quick_start.sh` first
- Verify `docker ps` shows postgres running before running DAGs
- Use correct ports: 5433 (warehouse), 5432 (Airflow metadata)

---

### Connection Timeout After 30 Seconds

**Symptoms:**
- Tasks fail with timeout
- Works sometimes, fails other times
- Network becomes intermittent

**Solutions:**

```bash
# 1. Check network latency
ping -c 5 devom.silog.co.id
# If times > 100ms, network might be slow

# 2. Check if database is under heavy load
psql -h devom.silog.co.id -U om -d om
> SELECT count(*) FROM pg_stat_activity;

# 3. Increase timeout in DAG (not recommended for production)
# Edit: airflow/dags/daily_warehouse_sync.py
# Change: timeout=30 → timeout=60

# 4. Increase pool size in compose.yml
```

---

## Database Problems

### Tables Don't Exist After Setup

**Symptoms:**
- DAG fails: "relation 'public.drivers' does not exist"
- Tables visible in pgAdmin but not in queries
- Schema issues

**Solutions:**

```bash
# 1. Check if tables were created
psql -h localhost -U postgres -d warehouse -p 5433
psql> SELECT COUNT(*) FROM information_schema.tables 
      WHERE table_schema='public';

# 2. If 0 tables, run setup in order:
bash scripts/setup/setup_warehouse_db.sh
bash scripts/etl/copy_devom_structure.sh

# 3. Verify tables were created
psql> \dt  # List all tables in public schema

# 4. List all 90 tables
psql> SELECT tablename FROM information_schema.tables 
      WHERE table_schema='public' ORDER BY tablename;
```

**Prevention:**
- Always run scripts in order: quick_start → setup_warehouse_db → copy_devom_structure
- Verify tables before running DAGs: `SELECT COUNT(*) FROM public.drivers;`

---

### Unique Constraint Violation / Duplicate Data

**Symptoms:**
- INSERT fails with "duplicate key value violates"
- Second sync run fails
- Duplicate records in table

**Solutions:**

```bash
# 1. Check for duplicates
psql -h localhost -U postgres -d warehouse -p 5433
psql> SELECT column_name, COUNT(*) FROM public.table_name 
      GROUP BY column_name HAVING COUNT(*) > 1;

# 2. Find which records are duplicates
psql> SELECT id, COUNT(*) FROM public.table_name GROUP BY id HAVING COUNT(*) > 1;

# 3. Clean up duplicates (CAREFUL!)
psql> DELETE FROM public.table_name WHERE id IN (
      SELECT id FROM (
        SELECT id, ROW_NUMBER() OVER (PARTITION BY key_column ORDER BY id) as rn 
        FROM public.table_name) t 
      WHERE rn > 1);

# 4. Check DAG config (max_active_runs should be 1)
# In airflow/dags/daily_warehouse_sync.py:
# max_active_runs=1

# 5. Clear failed DAG run in Airflow UI
# DAG Runs → [failed run] → Clear → Confirm
```

---

### "Disk Space Full" / Out of Memory

**Symptoms:**
- DAG fails: "No space left on device"
- Performance suddenly degrades
- Docker stops responding

**Solutions:**

```bash
# 1. Check disk space
df -h

# 2. Check warehouse database size
psql -h localhost -U postgres -d warehouse -p 5433
psql> SELECT pg_size_pretty(pg_database_size('warehouse'));

# 3. Check Airflow logs size
du -sh airflow/logs/

# 4. Clean up old logs (BACKUP FIRST!)
rm -rf airflow/logs/*

# 5. Clean up weather data (keep last 30 days)
psql> DELETE FROM weather.fact_weather_hourly 
      WHERE created_at < NOW() - INTERVAL '30 days';

# 6. Run VACUUM to reclaim space
psql> VACUUM FULL ANALYZE warehouse;

# 7. Clean Docker resources
docker system prune -a --volumes  # WARNING: removes all unused resources
```

---

## DAG & Airflow Issues

### DAG Not Found / Doesn't Appear in Airflow UI

**Symptoms:**
- Airflow UI shows "No DAGs matched your filter"
- DAG was working before
- DAG list is empty

**Solutions:**

```bash
# 1. Check if DAG file exists
ls -la airflow/dags/daily_warehouse_sync.py

# 2. Check for Python syntax errors
python3 -m py_compile airflow/dags/daily_warehouse_sync.py

# 3. Verify DAG directory is correct
ls -la airflow/dags/

# 4. Restart Airflow scheduler (force DAG reload)
docker-compose restart airflow-scheduler

# 5. Wait 2-3 minutes for DAG parsing
docker-compose logs airflow-scheduler | grep -i "dag" | tail -10

# 6. Force DAG list update
docker-compose exec airflow-scheduler airflow dags list
```

---

### DAG Task Failed / Task Stuck

**Symptoms:**
- Task shows "failed" in Airflow UI
- Task stuck on "running" for hours
- No new logs

**Solutions:**

```bash
# 1. Check task logs in Airflow UI
# DAG → Grid → Task Instance → Logs

# 2. Or check in filesystem
cat airflow/logs/dag_id=daily_warehouse_sync/run_id=*/task_id=*/

# 3. Check if scheduler is running
docker ps | grep airflow-scheduler

# 4. Check if worker is running
docker ps | grep airflow-worker

# 5. Restart scheduler
docker-compose restart airflow-scheduler

# 6. Restart worker
docker-compose restart airflow-worker

# 7. Clear task instance and retry
# Airflow UI → DAG Runs → [failed run] → Task → Clear

# 8. Check for zombie processes
docker-compose exec airflow-worker ps aux | grep python
kill -9 <PID>  # Kill stuck process
```

---

### Out of Memory / Task Killed

**Symptoms:**
- Random task failures
- Worker crashes silently
- Logs show memory issues

**Solutions:**

```bash
# 1. Check memory usage
docker stats airflow-worker

# 2. Check system memory
free -h

# 3. Reduce batch size in DAG
# Edit: airflow/dags/daily_warehouse_sync.py
# Change: BATCH_SIZE = 5000 → BATCH_SIZE = 1000

# 4. Increase Docker memory allocation
# Edit: compose.yml
# services:
#   airflow-worker:
#     mem_limit: 4g  # Increase from 2g

# 5. Apply changes
docker-compose up -d airflow-worker --force-recreate
```

---

## Dashboard Tool Issues

### Metabase Can't Connect to Database

```bash
# 1. Verify connection parameters in Metabase UI
# Settings → Databases → Warehouse → Test connection
# Should use: postgres://postgres:postgres123@localhost:5433/warehouse

# 2. Test from command line
psql -h localhost -U postgres -d warehouse -p 5433

# 3. Check Metabase container logs
docker-compose logs metabase | tail -30

# 4. Verify warehouse container is running
docker ps | grep postgres
```

---

### Grafana / Superset Shows No Data

**Symptoms:**
- Dashboard loads but panels are empty
- "No data" message

**Solutions:**

```bash
# 1. Check data source connection in tool UI
# Settings → Data Sources → PostgreSQL → Test

# 2. Test query manually
psql -h localhost -U postgres -d warehouse -p 5433
psql> SELECT * FROM weather.fact_weather_hourly LIMIT 1;

# 3. Verify data exists
psql> SELECT COUNT(*) FROM weather.fact_weather_hourly;

# 4. Check if weather_data_fetch DAG has run
# Airflow UI → weather_data_fetch → see recent task runs
```

---

## Data Quality Issues

### Weather Data Not Updating

**Symptoms:**
- Weather data shows hours-old timestamp
- No new records in fact_weather_hourly
- Metrics show "STALE" status

**Solutions:**

```bash
# 1. Check if weather_data_fetch DAG is running
# Airflow UI → weather_data_fetch → check recent runs

# 2. Check latest weather data timestamp
psql -h localhost -U postgres -d warehouse -p 5433
psql> SELECT MAX(data_timestamp), MAX(created_at), COUNT(*) 
      FROM weather.fact_weather_hourly;

# 3. Check freshness status
psql> SELECT freshness_status, COUNT(*) FROM weather.fact_weather_hourly 
      GROUP BY freshness_status;

# 4. Manually trigger DAG in Airflow UI
# weather_data_fetch → Trigger DAG

# 5. Check if BMKG API is down
# Try: curl https://api.bmkg.go.id/publik/prakiraan-cuaca

# 6. Check DAG logs for API errors
# Airflow UI → weather_data_fetch → Logs
```

---

### Tables Missing After Sync

**Symptoms:**
- Some tables missing after daily_warehouse_sync
- Row counts different from source
- Random tables not syncing

**Solutions:**

```bash
# 1. Check sync logs
# Airflow UI → daily_warehouse_sync → Logs

# 2. Compare table counts
psql -h localhost -U postgres -d warehouse -p 5433
psql> SELECT COUNT(*) FROM information_schema.tables 
      WHERE table_schema='public';
# Should be 90+ tables

# 3. Re-run full sync
bash scripts/etl/sync_tables_from_devom.sh

# 4. If new tables added to source, run copy structure
bash scripts/etl/copy_devom_structure.sh
```

---

## Performance Issues

### DAG Running Slower Than Usual

**Symptoms:**
- daily_warehouse_sync taking 20+ minutes (vs normal 10 min)
- Queries respond slowly
- High CPU/memory usage

**Solutions:**

```bash
# 1. Check running queries
psql -h localhost -U postgres -d warehouse -p 5433
psql> SELECT * FROM pg_stat_activity WHERE state != 'idle';

# 2. Run VACUUM (cleanup)
psql> VACUUM ANALYZE warehouse;

# 3. Check table sizes
psql> SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
      FROM pg_tables ORDER BY pg_total_relation_size DESC LIMIT 10;

# 4. Enable slow query logging
psql> CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
psql> SELECT query, calls, total_time FROM pg_stat_statements 
      ORDER BY total_time DESC LIMIT 10;

# 5. Add missing indexes (if needed)
psql> CREATE INDEX idx_table_column ON table_name(column_name);
```

---

## Getting Help

### Diagnostic Commands

```bash
# System status
docker ps -a                    # All containers
docker-compose ps               # Compose services
df -h                          # Disk space
free -h                        # Memory

# Network connectivity
ping devom.silog.co.id         # Test DEVOM
nc -zv devom.silog.co.id 5432  # Port test

# Database connection
psql -h localhost -U postgres -d warehouse -p 5433

# View main logs
docker-compose logs airflow-scheduler | tail -50
docker-compose logs postgres | tail -30
docker-compose logs metabase | tail -20
```

### Check Logs

```bash
# Airflow webserver
docker-compose logs airflow-webserver | tail -50

# Airflow scheduler
docker-compose logs airflow-scheduler | tail -50

# Airflow worker
docker-compose logs airflow-worker | tail -50

# PostgreSQL
docker-compose logs postgres | tail -30

# In Airflow UI: DAG → Grid → Task → Logs
```

---

📖 **Related:** [DAGs Reference](DAGS.md) | [Database Schema](DATABASE_SCHEMA.md)  
👈 **Back to:** [Main README](../README.md) | [Documentation Index](INDEX.md)
