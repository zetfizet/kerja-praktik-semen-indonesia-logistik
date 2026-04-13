#!/bin/bash

# SYNC TABLES FROM devom.silog.co.id TO LOCALHOST WAREHOUSE
# Tables: driver_armada, armada, rating, log_perjalanan_armada, log_aktifitas_driver, delivery_order

set -e

SOURCE_HOST="devom.silog.co.id"
SOURCE_USER="om"
SOURCE_DB="silog_oltp"
SOURCE_PASSWORD="om"

TARGET_HOST="localhost"
TARGET_USER="postgres"
TARGET_DB="warehouse"
TARGET_PASSWORD="postgres123"

# Tables to sync
TABLES=(
    "driver_armada"
    "armada"
    "rating"
    "log_perjalanan_armada"
    "log_aktifitas_driver"
    "delivery_order"
    "driver"
)

echo "📊 SYNCING TABLES FROM devom.silog.co.id TO localhost..."
echo ""

for TABLE in "${TABLES[@]}"; do
    echo "Syncing: $TABLE..."
    
    # Export from source
    PGPASSWORD="$SOURCE_PASSWORD" pg_dump -h "$SOURCE_HOST" -U "$SOURCE_USER" -d "$SOURCE_DB" -t "public.$TABLE" --data-only -f "/tmp/${TABLE}.sql" 2>/dev/null
    
    # Import to target
    PGPASSWORD="$TARGET_PASSWORD" psql -h "$TARGET_HOST" -U "$TARGET_USER" -d "$TARGET_DB" -f "/tmp/${TABLE}.sql" 2>/dev/null
    
    echo "  ✓ $TABLE synced"
done

echo ""
echo "✅ ALL TABLES SYNCED SUCCESSFULLY!"
echo ""
echo "Verify:"
echo "PGPASSWORD='postgres123' psql -h localhost -U postgres -d warehouse -c \"SELECT COUNT(*) FROM warehouse.driver_armada;\""
