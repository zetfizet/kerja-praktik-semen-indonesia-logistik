"""
Metabase Dashboard Setup Guide & Pre-built Queries
Save these queries to Metabase for instant dashboards
"""

-- ============================================
-- QUERY 1: DAG Execution Summary
-- ============================================
-- Shows DAG runs, execution times, and success rates
SELECT 
    d.dag_id,
    COUNT(dr.id) as total_runs,
    SUM(CASE WHEN dr.state = 'success' THEN 1 ELSE 0 END) as successful_runs,
    SUM(CASE WHEN dr.state = 'failed' THEN 1 ELSE 0 END) as failed_runs,
    ROUND(100.0 * SUM(CASE WHEN dr.state = 'success' THEN 1 ELSE 0 END) / COUNT(dr.id), 2) as success_rate,
    AVG(EXTRACT(EPOCH FROM (dr.end_date - dr.start_date))) as avg_duration_seconds
FROM dag d
LEFT JOIN dag_run dr ON d.dag_id = dr.dag_id
WHERE d.dag_id NOT LIKE 'system_%'
GROUP BY d.dag_id
ORDER BY total_runs DESC;

-- ============================================
-- QUERY 2: Task Instance Performance
-- ============================================
-- Shows task execution performance by DAG
SELECT 
    ti.dag_id,
    ti.task_id,
    COUNT(*) as total_executions,
    SUM(CASE WHEN ti.state = 'success' THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN ti.state = 'failed' THEN 1 ELSE 0 END) as failed,
    AVG(EXTRACT(EPOCH FROM (ti.end_date - ti.start_date))) as avg_duration_seconds,
    MAX(ti.try_number) as max_retries
FROM task_instance ti
GROUP BY ti.dag_id, ti.task_id
ORDER BY ti.dag_id, total_executions DESC;

-- ============================================
-- QUERY 3: Daily Execution Timeline
-- ============================================
-- Shows DAG executions over time
SELECT 
    DATE(dr.start_date) as execution_date,
    d.dag_id,
    COUNT(*) as run_count,
    SUM(CASE WHEN dr.state = 'success' THEN 1 ELSE 0 END) as success_count,
    SUM(CASE WHEN dr.state = 'failed' THEN 1 ELSE 0 END) as fail_count
FROM dag_run dr
JOIN dag d ON dr.dag_id = d.dag_id
WHERE d.dag_id NOT LIKE 'system_%'
GROUP BY DATE(dr.start_date), d.dag_id
ORDER BY execution_date DESC, d.dag_id;

-- ============================================
-- QUERY 4: Database Health Metrics
-- ============================================
-- Shows database usage and growth
SELECT 
    DATE(dr.start_date) as date,
    COUNT(DISTINCT dr.dag_id) as active_dags,
    COUNT(DISTINCT ti.task_id) as unique_tasks,
    COUNT(ti.id) as total_task_runs,
    COUNT(DISTINCT dr.id) as total_dag_runs
FROM dag_run dr
LEFT JOIN task_instance ti ON dr.id = ti.dag_run_id
GROUP BY DATE(dr.start_date)
ORDER BY date DESC;

-- ============================================
-- QUERY 5: Log Analysis
-- ============================================
-- Shows error and warning patterns
SELECT 
    DATE(dttm) as log_date,
    level,
    COUNT(*) as log_count,
    COUNT(DISTINCT task_id) as affected_tasks
FROM log
WHERE level IN ('ERROR', 'WARNING')
GROUP BY DATE(dttm), level
ORDER BY log_date DESC, log_count DESC;

-- ============================================
-- QUERY 6: XCom Data Values
-- ============================================
-- Shows data passed between tasks
SELECT 
    dag_id,
    task_id,
    key,
    COUNT(*) as value_count,
    MAX(timestamp) as last_updated
FROM xcom
GROUP BY dag_id, task_id, key
ORDER BY last_updated DESC
LIMIT 20;

-- ============================================
-- SETUP STEPS:
-- ============================================
-- 1. Open http://localhost:3000
-- 2. Create admin account
-- 3. Add Database Connection:
--    - Name: Airflow Database
--    - Type: PostgreSQL
--    - Host: 127.0.0.1
--    - Port: 5433
--    - Database: airflow
--    - Username: airflow
--    - Password: airflow
-- 4. Click "Browse Data"
-- 5. Create new cards/questions using above queries
-- 6. Combine cards into dashboards
-- 7. Share dashboards with team
-- ============================================
