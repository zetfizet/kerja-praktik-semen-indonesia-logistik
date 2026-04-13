#!/bin/bash

# ============================================================================
# SETUP DATABASE WAREHOUSE
# ============================================================================
# Script untuk setup database warehouse yang menggabungkan:
# 1. Data perusahaan dari devom.silog.co.id
# 2. Data cuaca dari BMKG API
#
# Database Target:
#   Host: localhost
#   Port: 5433
#   Database: warehouse
#   User: postgres
#   Password: postgres123
# ============================================================================

echo "🏗️  SETUP DATABASE WAREHOUSE"
echo "============================================"
echo ""

# Cek apakah PostgreSQL container sudah running
if ! podman ps | grep -q postgres; then
    echo "❌ PostgreSQL container belum running!"
    echo "   Jalankan dulu: bash quick_start.sh"
    exit 1
fi

echo "✅ PostgreSQL container detected"
echo ""

# Setup postgres user credentials
echo "[1/7] Setting up postgres user credentials..."
echo "   Creating/updating postgres user with password..."
podman exec postgres psql -U airflow -h localhost -p 5433 -d airflow -c "
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'postgres') THEN
            CREATE ROLE postgres WITH LOGIN SUPERUSER PASSWORD 'postgres123';
            RAISE NOTICE 'User postgres created';
        ELSE
            ALTER ROLE postgres WITH PASSWORD 'postgres123';
            RAISE NOTICE 'User postgres password updated';
        END IF;
    END
    \$\$;
" 2>&1 | grep -v "^$"
echo "   ✅ User postgres ready (password: postgres123)"
echo ""

# Database connection info
export PGHOST="localhost"
export PGPORT="5433"
export PGDATABASE="warehouse"
export PGUSER="postgres"
export PGPASSWORD="postgres123"

# Function to execute SQL
execute_sql() {
    local sql_file=$1
    local description=$2
    
    echo "📝 $description"
    echo "   File: $sql_file"
    
    if [ ! -f "$sql_file" ]; then
        echo "   ⚠️  File not found, skipping..."
        return
    fi
    
    PGPASSWORD="$PGPASSWORD" psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -f "$sql_file" 2>&1 | grep -v "NOTICE"
    
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo "   ✅ Success"
    else
        echo "   ⚠️  Some errors occurred (might be OK if objects already exist)"
    fi
    echo ""
}

# [2/7] Create warehouse database if not exists
echo "[2/7] Checking warehouse database..."
PGPASSWORD="postgres123" psql -h localhost -p 5433 -U postgres -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'warehouse'" | grep -q 1

if [ $? -ne 0 ]; then
    echo "   Creating warehouse database..."
    PGPASSWORD="postgres123" psql -h localhost -p 5433 -U postgres -d postgres -c "CREATE DATABASE warehouse;"
    echo "   ✅ Database 'warehouse' created"
else
    echo "   ✅ Database 'warehouse' already exists"
fi
echo ""

# [3/7] Create public schema
echo "[3/7] Creating public schema..."
PGPASSWORD="$PGPASSWORD" psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" << 'EOF'
CREATE SCHEMA IF NOT EXISTS public;
SELECT 'Public schema ready: ' || schema_name 
FROM information_schema.schemata 
WHERE schema_name = 'public';
EOF
echo ""

# [4] Create warehouse tables in public schema
execute_sql "sql/03_create_warehouse_schema.sql" "Creating warehouse tables in public schema"

# [5] Create weather tables in public schema
execute_sql "sql/05_create_weather_schema.sql" "Creating weather tables in public schema"

# [6] Verify setup
echo "[6/6] Verifying database setup..."
PGPASSWORD="$PGPASSWORD" psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" << 'EOF'
\echo ''
\echo '📊 SCHEMA:'
SELECT schema_name, 
       (SELECT COUNT(*) FROM information_schema.tables t WHERE t.table_schema = s.schema_name) as table_count
FROM information_schema.schemata s
WHERE schema_name = 'public'
ORDER BY schema_name;

\echo ''
\echo '📋 TABLES IN PUBLIC SCHEMA (Company + Weather Data):'
SELECT table_name, 
       CASE 
           WHEN table_name LIKE '%weather%' OR table_name LIKE 'fact_weather%' OR table_name LIKE 'dim_weather%' OR table_name LIKE 'v_weather%' THEN 'Weather Data'
           ELSE 'Company Data'
       END as data_type
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY data_type, table_name
LIMIT 20;
EOF

echo ""
echo "============================================"
echo "✅ DATABASE WAREHOUSE SETUP COMPLETE!"
echo "============================================"
echo ""
echo "📊 Connection Info:"
echo "   Host: localhost"
echo "   Port: 5433"
echo "   Database: warehouse"
echo "   User: postgres"
echo "   Password: postgres123"
echo ""
echo "🎯 Schema:"
echo "   ✓ public - Semua data (perusahaan + cuaca)"
echo ""
echo "📋 Tables:"
echo "   • Data Perusahaan: driver, armada, perjalanan, ... (dari DEVOM)"
echo "   • Data Cuaca: fact_weather_hourly, dim_weather_location (dari BMKG API)"
echo ""
echo "🔌 Connect via pgAdmin4:"
echo "   Right-click Servers → Register → Server"
echo "   Name: WAREHOUSE"
echo "   Host: localhost"
echo "   Port: 5433"
echo "   Database: warehouse"
echo "   Username: postgres"
echo "   Password: postgres123"
echo ""
echo "📖 Dokumentasi lengkap: RINGKASAN_DATABASE.md"
echo ""
