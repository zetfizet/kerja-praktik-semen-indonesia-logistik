#!/bin/bash
# Script untuk run data sync via Docker

echo "🚀 Starting data sync..."
echo "=================================================="

cd /home/rafiez/airflow-stack

# Run script di Airflow scheduler container (punya akses ke both databases)
docker exec airflow-scheduler python /home/rafiez/airflow-stack/scripts/sync_data_from_app.py

echo "=================================================="
echo "✅ Data sync completed!"
