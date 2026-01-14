# ✅ SETUP CHECKLIST

## Pre-Setup Verification

- [ ] Docker running: `docker ps` shows containers
- [ ] Airflow UI accessible: http://localhost:8080 (admin/rafie123)
- [ ] pgAdmin4 accessible: http://localhost:5050
- [ ] PostgreSQL accessible: `docker exec postgres psql -U airflow -d airflow`

---

## Phase 1: Data Export

- [ ] Open pgAdmin4: http://localhost:5050
- [ ] Connect to database: devom.silog.co.id (user: om/om)
- [ ] Export driver_armada.csv
  - [ ] Query: `SELECT * FROM driver_armada;`
  - [ ] Download as CSV
  - [ ] Verify file size > 0
  
- [ ] Export rating.csv
  - [ ] Query: `SELECT * FROM rating;`
  - [ ] Download as CSV
  - [ ] Verify file size > 0

- [ ] Export delivery_order.csv
  - [ ] Query: `SELECT * FROM delivery_order;`
  - [ ] Download as CSV
  - [ ] Verify file size > 0

- [ ] Export perangkat_gps_driver.csv
  - [ ] Query: `SELECT * FROM perangkat_gps_driver;`
  - [ ] Download as CSV
  - [ ] Verify file size > 0

- [ ] Export rekening_driver.csv
  - [ ] Query: `SELECT * FROM rekening_driver;`
  - [ ] Download as CSV
  - [ ] Verify file size > 0

---

## Phase 2: File Management

- [ ] Create data folder: `mkdir -p /home/rafiez/airflow-stack/data/`
- [ ] Copy all CSV files to data folder
  - [ ] Command: `cp ~/Downloads/*.csv /home/rafiez/airflow-stack/data/`
  - [ ] Verify: `ls -lh /home/rafiez/airflow-stack/data/`
  - [ ] All 5 files present
  - [ ] File sizes reasonable (not empty)

---

## Phase 3: Data Import

- [ ] Run import script
  - [ ] Command: `bash /home/rafiez/airflow-stack/run_etl.sh`
  - [ ] OR: `docker exec airflow-webserver python3 /home/airflow/etl_workflow.py`
  - [ ] Wait for completion
  - [ ] Check output for "✅ Total: X rows imported"

- [ ] Verify import success
  ```bash
  docker exec postgres psql -U airflow -d airflow -c "
    SELECT tablename FROM pg_tables 
    WHERE schemaname = 'public' 
    ORDER BY tablename;
  "
  ```
  - [ ] All 5 tables visible:
    - [ ] driver_armada
    - [ ] rating
    - [ ] delivery_order
    - [ ] perangkat_gps_driver
    - [ ] rekening_driver

---

## Phase 4: ETL Execution

- [ ] Trigger ETL DAG
  - [ ] Option A: Airflow UI → DAGs → etl_driver_kpi → ▶️ Play
  - [ ] Option B: CLI → `docker exec airflow-scheduler airflow dags trigger etl_driver_kpi`
  - [ ] Verify: "DAG triggered" message

- [ ] Monitor execution
  - [ ] Open Airflow UI: http://localhost:8080
  - [ ] Navigate to: DAGs → etl_driver_kpi
  - [ ] Switch to: Graph View
  - [ ] Watch tasks:
    - [ ] Task 1: extract_oltp_data → 🟢 Success
    - [ ] Task 2: transform_load_analytics → 🟢 Success
    - [ ] Task 3: validate_data_quality → 🟢 Success

- [ ] Check Airflow logs (if any task fails)
  - [ ] Click on task → View Logs
  - [ ] Read error message
  - [ ] Troubleshoot accordingly

---

## Phase 5: Analytics Verification

- [ ] Check fact_driver_performance table created
  ```bash
  docker exec postgres psql -U airflow -d airflow -c \
    "SELECT COUNT(*) FROM analytics.fact_driver_performance;"
  ```
  - [ ] Result: "50" (or number of drivers)

- [ ] Verify data quality
  ```bash
  docker exec postgres psql -U airflow -d airflow -c \
    "SELECT * FROM analytics.fact_driver_performance LIMIT 5;"
  ```
  - [ ] Columns present:
    - [ ] uuid_user
    - [ ] id_armada
    - [ ] avg_rating
    - [ ] total_delivery
    - [ ] delivery_success_rate
    - [ ] gps_active_ratio
    - [ ] kpi_score
    - [ ] updated_at

- [ ] Check KPI calculations
  ```bash
  docker exec postgres psql -U airflow -d airflow -c \
    "SELECT uuid_user, avg_rating, kpi_score 
     FROM analytics.fact_driver_performance 
     ORDER BY kpi_score DESC LIMIT 5;"
  ```
  - [ ] KPI scores are between 0-5
  - [ ] Top performers have highest scores
  - [ ] Rating affects KPI score

---

## Phase 6: Automation Setup

- [ ] Verify DAG schedule
  - [ ] Airflow UI → DAGs → etl_driver_kpi → Details
  - [ ] Schedule: `@daily` (00:00 UTC)
  - [ ] Confirm: DAG will run automatically

- [ ] Check next scheduled run
  - [ ] Tree View in Airflow
  - [ ] Should show tomorrow's run scheduled

- [ ] Document completion
  - [ ] Update any local notes
  - [ ] Note the analytics table name & location

---

## Phase 7: Optional - Dashboard Setup

- [ ] Metabase setup (optional)
  - [ ] Open: http://localhost:3000
  - [ ] Create data source → PostgreSQL
  - [ ] Connection:
    - [ ] Host: postgres (Docker) or localhost (Host)
    - [ ] Port: 5432
    - [ ] Database: airflow
    - [ ] User: airflow
    - [ ] Password: airflow
  - [ ] Create dashboard
  - [ ] Add cards for KPI visualization

---

## ✨ Success Criteria

All items should be checked for successful setup:

- [ ] All 5 CSV files imported to Airflow
- [ ] ETL DAG executed successfully (3 tasks green)
- [ ] analytics.fact_driver_performance table created
- [ ] 50 driver records with KPI scores
- [ ] DAG scheduled to run automatically daily

---

## 🆘 Troubleshooting

### If import fails:
- [ ] Check CSV format (UTF-8, comma-separated)
- [ ] Verify file names match exactly
- [ ] Check column names match source database
- [ ] See: PANDUAN_KONEKSI_DATABASE.md

### If DAG fails:
- [ ] Check Airflow logs
- [ ] Verify table names in SQL queries
- [ ] Check column names in JOIN statements
- [ ] See: PENJELASAN_ETL_DAG.md

### If analytics table empty:
- [ ] Check if extract_oltp_data task succeeded
- [ ] Verify source tables have data
- [ ] Check transform task logs for SQL errors
- [ ] See: WORKFLOW_PRAKTIS.md

---

## 📝 Notes Section

```
Setup Date: _______________
Completed By: _____________
CSV Files Imported: _______
Total Rows: _______________
Issues Encountered: _______
Resolution: _______________
```

---

**Status:** ☐ NOT STARTED  ☐ IN PROGRESS  ☐ COMPLETE  ☐ FAILED

**Date Started:** _______________
**Date Completed:** _______________
