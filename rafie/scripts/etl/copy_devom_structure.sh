#!/bin/bash

# ============================================================================
# COPY STRUCTURE DATABASE DEVOM → WAREHOUSE
# ============================================================================
# Script untuk meng-copy semua struktur tables dari DEVOM ke Warehouse
# Semua tables dari devom.silog.co.id akan dibuat di warehouse.public
# ============================================================================

echo "🔄 COPY STRUCTURE DEVOM → WAREHOUSE"
echo "============================================"
echo ""

# Check if PostgreSQL container is running
if ! podman ps | grep -q postgres; then
    echo "❌ PostgreSQL container belum running!"
    echo "   Jalankan dulu: bash quick_start.sh"
    exit 1
fi

echo "✅ PostgreSQL container detected"
echo ""

# Check Python3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found!"
    echo "   Install: sudo apt install python3 python3-pip"
    exit 1
fi

# Check psycopg2
if ! python3 -c "import psycopg2" 2>/dev/null; then
    echo "⚠️  psycopg2 not installed, installing..."
    pip3 install psycopg2-binary --user
    echo ""
fi

# Run Python script
echo "🚀 Running structure copy script..."
echo ""
python3 scripts/copy_devom_structure.py

echo ""
echo "============================================"
echo "✅ STRUCTURE COPY COMPLETE!"
echo "============================================"
echo ""
echo "📋 Review generated DDL:"
echo "   cat sql/06_devom_tables_ddl.sql"
echo ""
echo "📊 Verify in pgAdmin4:"
echo "   SELECT table_name FROM information_schema.tables"
echo "   WHERE table_schema='public' ORDER BY table_name;"
echo ""
echo "🔄 Next: Sync data dari DEVOM"
echo "   Run Airflow DAG: daily_warehouse_sync"
echo ""
