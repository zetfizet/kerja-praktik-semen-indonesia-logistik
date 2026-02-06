#!/bin/bash

# Metabase Setup Script - Data Visualization Dashboard
# Metabase running on port 3000

cd /home/rafiez/airflow-stack

echo "🚀 STARTING METABASE DASHBOARD..."
echo ""

# Create metabase data volume
echo "[1/3] Creating Metabase data volume..."
podman volume create metabase-data 2>/dev/null || true

# Start Metabase
echo "[2/3] Starting Metabase container..."
podman run -d \
  --name metabase \
  --privileged \
  --network=host \
  -e MB_DB_TYPE=h2 \
  -e MB_DB_FILE=/metabase.db \
  -v metabase-data:/metabase.db:Z \
  docker.io/metabase/metabase:latest

echo "[3/3] Waiting for Metabase to start (30 detik)..."
sleep 30

echo ""
echo "=========================================="
echo "✅ METABASE STARTED!"
echo "=========================================="
echo ""
echo "🌐 Access Metabase Dashboard:"
echo "   http://localhost:3000"
echo ""
echo "📝 First Time Setup:"
echo "   1. Choose language & timezone"
echo "   2. Enter email & password"
echo "   3. Add database connection"
echo ""
echo "📊 Database Connection Details:"
echo "   Host: 127.0.0.1"
echo "   Port: 5433"
echo "   Database: airflow"
echo "   Username: airflow"
echo "   Password: airflow"
echo ""
echo "📋 Container Status:"
podman ps | grep metabase
echo ""
echo "🛑 Stop Metabase:"
echo "   bash stop_metabase.sh"
echo ""
