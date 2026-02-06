#!/bin/bash

# Grafana Setup Script - Real-time Monitoring & Alerting Dashboard
# Grafana running on port 3001

cd /home/rafiez/airflow-stack

echo "🚀 STARTING GRAFANA MONITORING DASHBOARD..."
echo ""

# Create Grafana data volume
echo "[1/4] Creating Grafana data volume..."
podman volume create grafana-data 2>/dev/null || true

# Start Grafana
echo "[2/4] Starting Grafana container..."
podman run -d \
  --name grafana \
  --privileged \
  --network=host \
  -e GF_SECURITY_ADMIN_PASSWORD=grafana123 \
  -e GF_SECURITY_ADMIN_USER=admin \
  -e GF_INSTALL_PLUGINS=grafana-piechart-panel \
  -v grafana-data:/var/lib/grafana:Z \
  docker.io/grafana/grafana:latest

echo "[3/4] Waiting for Grafana to start (20 detik)..."
sleep 20

# Test Grafana API
echo "[4/4] Testing Grafana API..."
if curl -s http://localhost:3001/api/health > /dev/null; then
  echo "✅ Grafana API ready"
else
  echo "⏳ Grafana masih initializing..."
fi

echo ""
echo "=========================================="
echo "✅ GRAFANA STARTED!"
echo "=========================================="
echo ""
echo "🌐 Access Grafana:"
echo "   http://localhost:3001"
echo ""
echo "🔐 Login:"
echo "   Username: admin"
echo "   Password: grafana123"
echo ""
echo "📊 Setup Database Connection:"
echo "   1. Login to Grafana"
echo "   2. Go to 'Configuration' → 'Data Sources'"
echo "   3. Click 'Add data source'"
echo "   4. Choose 'PostgreSQL'"
echo "   5. Fill details:"
echo "      - Host: 127.0.0.1:5433"
echo "      - Database: airflow"
echo "      - User: airflow"
echo "      - Password: airflow"
echo "      - SSL Mode: disable"
echo "   6. Test & Save"
echo ""
echo "📈 Create Dashboard:"
echo "   1. Click '+' → 'Dashboard'"
echo "   2. Click 'Add panel'"
echo "   3. Choose visualization type"
echo "   4. Write SQL query"
echo "   5. Configure metrics & labels"
echo "   6. Save dashboard"
echo ""
echo "🔔 Setup Alerts:"
echo "   1. On panel → Click 'Alert' tab"
echo "   2. Define alert conditions"
echo "   3. Add notification channels"
echo "   4. Save"
echo ""
echo "📋 Container Status:"
podman ps | grep grafana
echo ""
echo "🛑 Stop Grafana:"
echo "   bash stop_grafana.sh"
echo ""
