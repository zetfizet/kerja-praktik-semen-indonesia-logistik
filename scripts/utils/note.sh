#!/bin/bash

echo "🧹 CLEANUP AIRFLOW CONTAINERS & VOLUMES"
echo "========================================"
echo ""

# Stop all related containers
echo "[1/4] Stopping containers..."
podman stop postgres valkey airflow-webserver airflow-scheduler airflow-init 2>/dev/null || true
echo "       ✓ Containers stopped"

# Remove all related containers (force remove if needed)
echo "[2/4] Removing containers..."
podman rm -f postgres valkey airflow-webserver airflow-scheduler airflow-init 2>/dev/null || true
echo "       ✓ Containers removed"

# Optional: Remove volumes (UNCOMMENT jika ingin hapus data)
echo "[3/4] Volumes (data tetap ada, uncomment di script untuk hapus)..."
# podman volume rm postgres-data valkey-data 2>/dev/null || true
echo "       ℹ️  Volumes tidak dihapus (data aman)"

# Clean up logs
echo "[4/4] Cleaning up logs..."
sudo rm -rf airflow/logs/* 2>/dev/null || rm -rf airflow/logs/* 2>/dev/null || true
echo "       ✓ Logs cleaned"

echo ""
echo "=========================================="
echo "✅ CLEANUP SELESAI!"
echo "=========================================="
echo ""
echo "📊 Container yang masih berjalan:"
podman ps --format "table {{.Names}}\t{{.Status}}" || echo "   (tidak ada)"
echo ""
echo "💾 Volumes yang tersisa:"
podman volume ls | grep -E "postgres-data|valkey-data" || echo "   (tidak ada)"
echo ""
echo "▶️  Sekarang bisa run:"
echo "   bash quick_start.sh"
echo ""
