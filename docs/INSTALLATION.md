# 📖 Installation & Setup Guide

**Panduan lengkap setup Airflow Stack dari nol**

---

## 📑 Table of Contents

- [Prerequisites](#prerequisites)
- [Step-by-Step Installation](#step-by-step-installation)
- [Verify Installation](#verify-installation)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **OS:** Linux, macOS, or Windows (with WSL2)
- **RAM:** Minimum 4GB (recommended 8GB)
- **Disk:** 20GB free space
- **Ports:** 5433, 6379, 8080 must be available

### Required Software

```bash
# Check Docker
docker --version      # Docker 24.0.0+

# Check Docker Compose
docker-compose --version   # 2.20.0+

# Verify connectivity to source
ping devom.silog.co.id
```

**Setup links:**
- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- [Docker Compose](https://docs.docker.com/compose/install/)

---

## Step-by-Step Installation

### Step 1: Clone or navigate to repository

```bash
cd /home/rafie/airflow-stack
pwd  # Verify you're in correct directory
```

**Expected output:**
```
/home/rafie/airflow-stack
```

### Step 2: Start the complete stack

```bash
bash scripts/utils/quick_start.sh
```

**What this does:**
1. Build and start PostgreSQL container
2. Build and start Redis/Valkey container
3. Initialize Airflow database
4. Start Airflow webserver and scheduler

**Expected output:**
```
✅ Starting PostgreSQL container...
✅ Starting Valkey (Redis) container...
✅ Initializing Airflow database...
✅ Starting Airflow webserver on http://localhost:8080
✅ Starting Airflow scheduler...

📊 Services status:
   - PostgreSQL: http://localhost:5433
   - Airflow UI: http://localhost:8080
   - Redis: localhost:6379

Press Ctrl+C to stop services
```

### Step 3: Wait for services to be ready

```bash
# Monitor container logs (in new terminal)
docker-compose logs -f airflow-webserver

# Wait until you see:
# [2026-04-13 10:00:00,000] {webserver.py} INFO - Starting Airflow Webserver...
```

**If containers are starting but not ready, wait 1-2 minutes for:**
- PostgreSQL to initialize
- Airflow migrations to complete
- Executor (Celery) to connect

### Step 4: Verify Airflow UI is accessible

Open browser and navigate to:
```
http://localhost:8080
```

**Login with default credentials:**
```
Username: admin
Password: rafie123
```

**Expected dashboard:**
- DAGs list is visible (3 DAGs: daily_warehouse_sync, weather_data_fetch, sync_data_from_app)
- "No DAGs matched your filter" message if search doesn't match anything
- Scheduler status showing "Active"

---

## Database Setup

### Step 5a: Create Warehouse Schemas

First time only - create database structure:

```bash
bash scripts/setup/setup_warehouse_db.sh
```

**What this does:**
1. Connects to warehouse database
2. Creates schema: `public`, `weather`, `analytics`
3. Creates initial tables (weather tracking tables)
4. Sets up user `postgres` with password `postgres123`

**Expected output:**
```
✅ Creating warehouse database...
✅ Creating schemas...
✅ Creating weather tables...
✅ Creating analytics tables...
✅ Done! Database ready.
```

### Step 5b: Copy table structure from DEVOM

Copy all 90+ tables from source warehouse:

```bash
bash scripts/etl/copy_devom_structure.sh
```

**What this does:**
1. Connects to devom.silog.co.id (om/om)
2. Lists all tables from source database
3. Generates DDL (CREATE TABLE statements)
4. Replicates table structures in warehouse.public schema
5. Saves DDL to `sql/06_devom_tables_ddl.sql`

**Expected output:**
```
✅ Connecting to DEVOM warehouse...
✅ Retrieving table list...
Found XX tables:
   - driver
   - armada
   - perjalanan
   - [... more tables ...]

✅ Generating DDL statements...
✅ Creating tables in warehouse.public...
✅ Tables created successfully!

💡 DDL statements saved to: sql/06_devom_tables_ddl.sql
```

**⏱️ Duration:** 5-15 minutes (depending on table count and network)

### Step 5c: Sync initial data (Optional)

Run first data sync (this will be automated daily):

```bash
# Trigger daily_warehouse_sync DAG from Airflow UI
# OR use Airflow CLI:
airflow dags trigger daily_warehouse_sync
```

---

## Verify Installation

### Step 6: Verify services are running

```bash
# Check all containers
docker ps --filter "label=com.docker.compose.project=airflow-stack"

# Expected output (4-6 containers running):
# - postgres
# - valkey
# - airflow-webserver
# - airflow-worker (if using CeleryExecutor)
# - airflow-scheduler
# - airflow-flower (monitoring, optional)
```

### Step 7: Verify database connections

#### Option A: Using pgAdmin4 (GUI)

1. Download & install pgAdmin4
2. Open pgAdmin4 UI
3. Right-click **Servers** → **Register** → **Server**
4. Fill in connection details:

```
General Tab:
  Name: WAREHOUSE

Connection Tab:
  Host name/address: localhost
  Port: 5433
  Database: warehouse
  Username: postgres
  Password: postgres123
  ✓ Save password?
```

5. Click **Save**
6. Verify connection by viewing schemas in left sidebar:
   - public (with 90+ tables)
   - weather
   - analytics

#### Option B: Using psql (CLI)

```bash
# Connect to warehouse database
psql -h localhost -U postgres -d warehouse -p 5433

# When prompted for password:
# Password: postgres123

# In psql, run verification queries:
\dt public.*              # List all tables in public schema
\dt weather.*             # List weather schema tables
\dn                       # List all schemas
\q                        # Quit psql
```

**Expected output:**
```
postgres=# \dn
   List of schemas
     Name     |  Owner
-----------+----------
 analytics |
 public    | postgres
 weather   | postgres

postgres=# \dt public.* | head -20
           List of relation "public" relations
   Schema |   Name    | Type  | Owner
-----------+-----------+-------+----------
 public   | driver    | table | postgres
 public   | armada    | table | postgres
 public   | perjalanan| table | postgres
 ...
```

### Step 8: Verify Airflow configuration

**In Airflow UI:**

1. Navigate to **Admin** → **Connections**
2. Verify connections exist:
   - `postgres_warehouse` (pointing to localhost:5433)
   - `postgres_app` (devom.silog.co.id)
   - Any API connections

**Or via CLI:**

```bash
airflow connections list

# Expected output:
# conn_id           | conn_type | host            | user | schema
# ---------------- + --------- + -------------- + ---- + --------
# postgres_warehouse| postgres  | localhost      | ... | warehouse
# postgres_app      | postgres  | devom.silog... | om  | om
```

### Step 9: Test DAG execution

**In Airflow UI:**

1. Go to **DAGs** tab
2. Click on `daily_warehouse_sync` DAG
3. Click **"Trigger DAG"** (play button)
4. Select **Graph** view to watch execution
5. Wait for all tasks to succeed (green)

**Expected task flow:**
```
check_weather_data (success) 
   ↓
sync_warehouse_tables (success)
   ↓
verify_warehouse_data (success)
```

**If tasks fail:**
- Click on failed task
- View logs in **Log** tab
- See [Troubleshooting](#troubleshooting) section below

---

## First DAG Run Checklist

Before running DAGs, verify:

- [ ] All 3 containers running (`docker ps`)
- [ ] Airflow UI accessible (http://localhost:8080)
- [ ] Database schemas created (`setup_warehouse_db.sh`)
- [ ] Table structure copied (`copy_devom_structure.sh`)
- [ ] Network connection to devom.silog.co.id (test with `ping devom.silog.co.id`)
- [ ] Airflow connections configured (Admin → Connections)

---

## Troubleshooting

### Issue: Docker containers won't start

**Symptom:** `docker-compose up` fails or containers crash

**Solution:**
```bash
# Check for port conflicts
netstat -tulpn | grep -E '5433|6379|8080'

# If ports are in use, stop conflicting services
docker stop <container_id>

# Verify Docker daemon is running
docker ps

# Restart Docker service
sudo systemctl restart docker  # Linux
# OR restart Docker Desktop app  # macOS/Windows
```

### Issue: Airflow webserver not accessible

**Symptom:** Can't reach `http://localhost:8080`

**Solution:**
```bash
# Check webserver logs
docker-compose logs airflow-webserver | tail -50

# Check if container is running
docker ps | grep airflow-webserver

# Restart webserver
docker-compose restart airflow-webserver

# Wait 1-2 minutes for it to start
# Then try accessing UI again
```

### Issue: Database connection failed

**Symptom:** DAG tasks fail with "could not connect to server"

**Solutions:**

1. **Check PostgreSQL container is running:**
   ```bash
   docker ps | grep postgres
   docker-compose logs postgres
   ```

2. **Check warehouse database exists:**
   ```bash
   docker-compose exec postgres psql -U airflow airflow -c "SELECT 1"
   ```

3. **Verify database credentials in DAG:**
   - Check `airflow/dags/daily_warehouse_sync.py`
   - Verify `TARGET_DB_CONFIG` matches database settings

4. **Re-run setup:**
   ```bash
   bash scripts/setup/setup_warehouse_db.sh
   ```

### Issue: Cannot connect to devom.silog.co.id

**Symptom:** DAG tasks fail with "could not connect to source"

**Solution:**
1. Check network connectivity:
   ```bash
   ping devom.silog.co.id
   ```

2. Verify credentials in DAG:
   - Username: `om`
   - Password: `om`
   - Database: `om` or `devom.silog.co.id`

3. Check if VPN/network access is required

4. Verify hostname resolution:
   ```bash
   nslookup devom.silog.co.id
   ```

### Issue: Out of memory errors

**Symptom:** Containers crash with OOMKilled

**Solution:**
```bash
# Increase Docker memory allocation
# Docker Desktop → Preferences → Resources → Memory
# Set to 6GB or higher

# OR limit Airflow/Celery memory in compose.yml
services:
  airflow-webserver:
    mem_limit: 2g
```

### Issue: DAG shows "No DAGs" in UI

**Symptom:** Airflow UI shows empty DAGs list

**Solution:**
1. Check DAG files exist:
   ```bash
   ls -la airflow/dags/*.py
   ```

2. Check DAG syntax (Python errors):
   ```bash
   python3 -m py_compile airflow/dags/daily_warehouse_sync.py
   ```

3. Restart scheduler:
   ```bash
   docker-compose restart airflow-scheduler
   ```

4. Wait 2-3 minutes for DAG parsing

### Issue: Scheduler not picking up DAG changes

**Symptom:** Modified DAG code doesn't reflect in UI

**Solution:**
```bash
# The DAG files are mounted as volumes, so changes should be picked up
# If not:

# 1. Restart scheduler
docker-compose restart airflow-scheduler

# 2. Give it time to parse (2-3 minutes)

# 3. Clear cache
docker-compose exec airflow-scheduler rm -rf /opt/airflow/.pytest_cache

# 4. If still not working, check DAG syntax:
python3 airflow/dags/daily_warehouse_sync.py
```

---

## Getting Help

If you encounter issues not covered above:

1. **Check logs:**
   ```bash
   docker-compose logs -f <service_name>
   # Examples: postgres, airflow-webserver, airflow-scheduler
   ```

2. **Check Airflow logs:**
   - In Airflow UI → DAG → Task → Log tab
   - Or in filesystem: `airflow/logs/dag_id=<dag_name>/`

3. **Check database:**
   ```bash
   psql -h localhost -U postgres -d warehouse -p 5433
   \dt  # List tables
   ```

4. **Consult documentation:**
   - [Apache Airflow Docs](https://airflow.apache.org/)
   - [PostgreSQL Docs](https://www.postgresql.org/docs/)
   - [Docker Docs](https://docs.docker.com/)

---

📖 **Next:** Read [DAGs Reference](DAGS.md) to understand data pipelines

👈 **Back to:** [Main README](../README.md)
