#!/bin/bash

# Stop MLflow Tracking Server

echo "🛑 Stopping MLflow Tracking Server..."

if [ -f /home/rafiez/airflow-stack/mlflow/.mlflow.pid ]; then
    PID=$(cat /home/rafiez/airflow-stack/mlflow/.mlflow.pid)
    if kill $PID 2>/dev/null; then
        echo "✓ MLflow process $PID stopped"
        rm /home/rafiez/airflow-stack/mlflow/.mlflow.pid
    else
        echo "⚠️ Process $PID not found"
    fi
else
    # Try to kill by port
    echo "Searching for MLflow process on port 5000..."
    PID=$(lsof -ti :5000 2>/dev/null | head -1)
    if [ -n "$PID" ]; then
        kill $PID 2>/dev/null && echo "✓ Stopped MLflow process $PID" || echo "❌ Failed to stop process"
    else
        echo "✓ No MLflow process running"
    fi
fi

echo "✓ MLflow stopped"
