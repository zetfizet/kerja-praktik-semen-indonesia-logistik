#!/bin/bash

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"

if ! command -v podman >/dev/null 2>&1; then
  echo "ERROR: podman not found. Install podman or update the script to use docker." >&2
  exit 1
fi

echo "🚀 STARTING AIRFLOW DENGAN PODMAN (HOST NETWORK)..."
echo ""

# Cleanup old containers
echo "[1/5] Cleanup containers lama..."
podman stop postgres valkey airflow-webserver airflow-scheduler airflow-init 2>/dev/null || true
podman rm postgres valkey airflow-webserver airflow-scheduler airflow-init 2>/dev/null || true
sleep 2

# Create volumes and directories
echo "[2/5] Create volumes and directories..."
podman volume create postgres-data 2>/dev/null || true
podman volume create valkey-data 2>/dev/null || true
mkdir -p airflow/plugins airflow/dags airflow/logs
echo "       Fixing permissions for Airflow logs..."
sudo chmod -R 777 airflow/logs 2>/dev/null || chmod -R 777 airflow/logs
# Keep dags and plugins owned by current user for editing
chmod -R 755 airflow/dags airflow/plugins 2>/dev/null || true

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

# Start Airflow Webserver (standalone with LocalExecutor)
echo "[5/5] Start Airflow Webserver..."
podman run -d \
  --name airflow-webserver \
  --network=host \
  -e AIRFLOW__DATABASE__SQL_ALCHEMY_CONN="postgresql+psycopg2://airflow:airflow@127.0.0.1:5433/airflow" \
  -e AIRFLOW__CORE__EXECUTOR=LocalExecutor \
  -e AIRFLOW__CORE__LOAD_EXAMPLES=false \
  -e AIRFLOW__CORE__FERNET_KEY="DKD39Cfp3KGT1pcFQXmhQbpQIgViC+6jf9UyMt0cIi4=" \
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
echo "   Password: (cek dengan: podman exec airflow-webserver cat /opt/airflow/simple_auth_manager_passwords.json.generated)"
echo ""
echo "📊 Database: postgresql://airflow:airflow@127.0.0.1:5433/airflow"
echo "� Warehouse DB: postgresql://postgres:postgres123@127.0.0.1:5433/warehouse"
echo ""
echo "📋 View logs:"
echo "   podman logs -f airflow-webserver"
echo ""
echo "🛑 Stop:"
echo "   bash stop_airflow_podman.sh"
echo ""
