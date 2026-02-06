#!/bin/bash

cd /home/rafiez/airflow-stack

echo "🚀 STARTING AIRFLOW DENGAN PODMAN (HOST NETWORK)..."
echo ""

# Cleanup old containers
echo "[1/5] Cleanup containers lama..."
podman stop postgres valkey airflow-webserver airflow-scheduler airflow-init 2>/dev/null || true
podman rm postgres valkey airflow-webserver airflow-scheduler airflow-init 2>/dev/null || true
sleep 2

# Create volumes
echo "[2/5] Create volumes..."
podman volume create postgres-data 2>/dev/null || true
podman volume create valkey-data 2>/dev/null || true

# Start PostgreSQL on alternative port 5433
echo "[3/5] Start PostgreSQL on port 5433 (waiting 50 detik untuk init)..."
podman run -d \
  --name postgres \
  --network=host \
  -e POSTGRES_USER=airflow \
  -e POSTGRES_PASSWORD=airflow \
  -e POSTGRES_DB=airflow \
  -v postgres-data:/var/lib/postgresql \
  docker.io/library/postgres:18 \
  -c port=5433

echo "       Tunggu PostgreSQL siap..."
sleep 50

# Start Valkey/Redis
echo "[4/5] Start Valkey (Redis)..."
podman run -d \
  --name valkey \
  --network=host \
  -v valkey-data:/data \
  docker.io/valkey/valkey:9 \
  valkey-server --appendonly no

sleep 5

# Start Airflow Webserver (standalone)
echo "[5/5] Start Airflow Webserver..."
podman run -d \
  --name airflow-webserver \
  --network=host \
  -e AIRFLOW__DATABASE__SQL_ALCHEMY_CONN="postgresql+psycopg2://airflow:airflow@127.0.0.1:5433/airflow" \
  -e AIRFLOW__CELERY__BROKER_URL="redis://127.0.0.1:6379/0" \
  -e AIRFLOW__CELERY__RESULT_BACKEND="db+postgresql://airflow:airflow@127.0.0.1:5433/airflow" \
  -e AIRFLOW__CORE__FERNET_KEY="DKD39Cfp3KGT1pcFQXmhQbpQIgViC+6jf9UyMt0cIi4=" \
  -e AIRFLOW__API__SECRET_KEY="cV4qZVjpycYWE1ZTo2hYK25fUp5DCJXxH+4SHHsQ1hU=" \
  -e AIRFLOW__CORE__EXECUTOR=CeleryExecutor \
  -e AIRFLOW__CORE__LOAD_EXAMPLES=false \
  -e AIRFLOW_HOME=/opt/airflow \
  -v $(pwd)/airflow/dags:/opt/airflow/dags:Z \
  -v $(pwd)/airflow/logs:/opt/airflow/logs:Z \
  -v $(pwd)/airflow/plugins:/opt/airflow/plugins:Z \
  docker.io/apache/airflow:3.1.3-python3.13 \
  standalone

sleep 10

echo ""
echo "=========================================="
echo "✓ AIRFLOW STARTED!"
echo "=========================================="
echo ""
echo "📊 Status Containers:"
podman ps --format "table {{.Names}}\t{{.Status}}"
echo ""
echo "🌐 Access:"
echo "   http://localhost:8080"
echo ""
echo "🔐 Login:"
echo "   Username: admin"
echo "   Password: rafie123"
echo ""
echo "📊 Database: postgresql://airflow:airflow@127.0.0.1:5433/airflow"
echo "📨 Redis: 127.0.0.1:6379"
echo ""
echo "📋 View logs:"
echo "   podman logs -f airflow-webserver"
echo ""
echo "🛑 Stop:"
echo "   bash stop_airflow_podman.sh"
echo ""
