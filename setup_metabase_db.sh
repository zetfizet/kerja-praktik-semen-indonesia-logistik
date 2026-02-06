#!/bin/bash

# Script untuk auto-setup database connection di Metabase
# Menggunakan Metabase API untuk menghubungkan database PostgreSQL

echo "🔧 Setting up Metabase database connection..."
echo ""

# Wait for Metabase to be ready
echo "Waiting for Metabase API to be ready (60 detik)..."
for i in {1..60}; do
  if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "✅ Metabase API ready!"
    break
  fi
  sleep 1
done

# Get or create user session
echo "Creating admin user and session..."
curl -s -X POST http://localhost:3000/api/setup \
  -H "Content-Type: application/json" \
  -d '{
    "user": {
      "first_name": "Admin",
      "last_name": "User",
      "email": "admin@airflow.local",
      "password": "metabase123"
    },
    "database": null,
    "token": null
  }' > /dev/null 2>&1

# Get session token
echo "Getting session token..."
SESSION=$(curl -s -X POST http://localhost:3000/api/session \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin@airflow.local",
    "password": "metabase123"
  }' | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$SESSION" ]; then
  echo "⚠️  Could not get session token. Manual setup required."
  echo ""
  echo "📝 Manual Setup Steps:"
  echo "1. Open http://localhost:3000"
  echo "2. Create admin account (email: admin@airflow.local, password: metabase123)"
  echo "3. Add database:"
  echo "   - Type: PostgreSQL"
  echo "   - Host: 127.0.0.1"
  echo "   - Port: 5433"
  echo "   - Database: airflow"
  echo "   - Username: airflow"
  echo "   - Password: airflow"
  exit 0
fi

echo "✅ Session created: $SESSION"

# Create database connection
echo "Creating PostgreSQL database connection..."
curl -s -X POST http://localhost:3000/api/database \
  -H "Content-Type: application/json" \
  -H "X-Metabase-Session: $SESSION" \
  -d '{
    "name": "Airflow Database",
    "engine": "postgres",
    "details": {
      "host": "127.0.0.1",
      "port": 5433,
      "database": "airflow",
      "user": "airflow",
      "password": "airflow",
      "ssl": false
    },
    "auto_run_queries": true,
    "is_sample": false
  }' > /dev/null 2>&1

echo "✅ Database connection created!"
echo ""
echo "=========================================="
echo "✅ SETUP COMPLETED!"
echo "=========================================="
echo ""
echo "🌐 Access Metabase:"
echo "   http://localhost:3000"
echo ""
echo "🔐 Login:"
echo "   Email: admin@airflow.local"
echo "   Password: metabase123"
echo ""
echo "📊 Create Visualizations:"
echo "   1. Click 'Browse data'"
echo "   2. Select 'Airflow Database'"
echo "   3. Choose a table to visualize"
echo "   4. Build charts & dashboards"
echo ""
