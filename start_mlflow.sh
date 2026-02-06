#!/bin/bash

# MLflow Setup and Start Script
# Starts MLflow tracking server on localhost:5000
# With PostgreSQL backend for experiment tracking

set -e

echo "🚀 Starting MLflow Tracking Server..."
echo "=================================="

# Create mlflow directory if not exists
mkdir -p /home/rafiez/airflow-stack/mlflow/artifacts
mkdir -p /home/rafiez/airflow-stack/mlflow/logs

# Check if PostgreSQL is running
echo "📊 Checking PostgreSQL connection..."
if ! psql -h localhost -U postgres -d postgres -c "SELECT 1" >/dev/null 2>&1; then
    echo "❌ PostgreSQL is not running. Please start PostgreSQL first."
    echo "   Command: podman-compose up -d postgres"
    exit 1
fi

# Create MLflow database if not exists
echo "📁 Setting up MLflow database..."
psql -h localhost -U postgres -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'mlflow'" >/dev/null 2>&1 || \
    psql -h localhost -U postgres -d postgres -c "CREATE DATABASE mlflow" || true

echo "✓ Database ready"

# Start MLflow tracking server
echo "🎯 Starting MLflow server on localhost:5000..."
echo "   Backend: postgresql://postgres:postgres123@localhost/mlflow"
echo "   Artifacts: /home/rafiez/airflow-stack/mlflow/artifacts"
echo ""

# Run MLflow in background
nohup mlflow server \
    --backend-store-uri postgresql://postgres:postgres123@localhost/mlflow \
    --default-artifact-root /home/rafiez/airflow-stack/mlflow/artifacts \
    --host 0.0.0.0 \
    --port 5000 \
    > /home/rafiez/airflow-stack/mlflow/logs/mlflow.log 2>&1 &

MLFLOW_PID=$!
echo $MLFLOW_PID > /home/rafiez/airflow-stack/mlflow/.mlflow.pid

# Wait for server to start
echo "⏳ Waiting for MLflow server to start..."
sleep 3

# Check if server is running
if curl -s http://localhost:5000 > /dev/null 2>&1; then
    echo ""
    echo "✅ MLflow Server Started Successfully!"
    echo ""
    echo "📊 Access MLflow UI:"
    echo "   URL: http://localhost:5000"
    echo ""
    echo "📝 Tracking URI for Python code:"
    echo "   mlflow.set_tracking_uri('http://localhost:5000')"
    echo ""
    echo "📂 Artifacts Location:"
    echo "   /home/rafiez/airflow-stack/mlflow/artifacts"
    echo ""
    echo "📋 Logs:"
    echo "   tail -f /home/rafiez/airflow-stack/mlflow/logs/mlflow.log"
else
    echo "❌ MLflow server failed to start"
    echo "Check logs: cat /home/rafiez/airflow-stack/mlflow/logs/mlflow.log"
    exit 1
fi
