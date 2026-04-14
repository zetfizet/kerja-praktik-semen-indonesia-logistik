#!/bin/bash

# ============================================================================
# MIGRATE TO SINGLE SCHEMA STRUCTURE
# ============================================================================
# Script untuk migrate database warehouse ke struktur single schema
# Semua data (perusahaan + cuaca) akan ada di public schema
# ============================================================================

echo "🔄 MIGRATE TO SINGLE SCHEMA STRUCTURE"
echo "============================================"
echo ""

# Check container
if ! podman ps | grep -q postgres; then
    echo "❌ PostgreSQL container belum running!"
    echo "   Jalankan: bash quick_start.sh"
    exit 1
fi

echo "✅ PostgreSQL container detected"
echo ""

echo "⚠️  WARNING: Script ini akan:"
echo "   1. Drop schema 'weather' (jika ada)"
echo "   2. Drop schema 'analytics' (jika ada)"  
echo "   3. Migrate semua tables ke public schema"
echo ""

read -p "Continue? (y/n): " answer
if [ "$answer" != "y" ] && [ "$answer" != "Y" ]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "[1/3] Dropping old schemas..."

podman exec postgres psql -U postgres -h localhost -p 5433 -d warehouse << 'EOF'
-- Drop old schemas if exist
DROP SCHEMA IF EXISTS weather CASCADE;
DROP SCHEMA IF EXISTS analytics CASCADE;
SELECT 'Old schemas dropped';
EOF

echo "   ✅ Old schemas dropped"
echo ""

echo "[2/3] Re-creating weather tables in public schema..."
bash setup_warehouse_db.sh

echo ""
echo "[3/3] Verifying structure..."

podman exec postgres psql -U postgres -h localhost -p 5433 -d warehouse << 'EOF'
-- List schemas
SELECT schema_name, 
       (SELECT COUNT(*) FROM information_schema.tables t WHERE t.table_schema = s.schema_name) as table_count
FROM information_schema.schemata s
WHERE schema_name = 'public';

-- List tables with type
SELECT table_name,
       CASE 
           WHEN table_name LIKE '%weather%' OR table_name LIKE 'fact_weather%' OR table_name LIKE 'dim_weather%' THEN 'Weather Data'
           ELSE 'Company Data'
       END as data_type
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY data_type, table_name;
EOF

echo ""
echo "============================================"
echo "✅ MIGRATION COMPLETE!"
echo "============================================"
echo ""
echo "📊 Structure:"
echo "   warehouse (database)"
echo "     └── public (schema)"
echo "          ├── driver, armada, ... (company data)"
echo "          └── fact_weather_hourly (weather data)"
echo ""
echo "📖 Dokumentasi: SINGLE_SCHEMA_SETUP.md"
echo ""
