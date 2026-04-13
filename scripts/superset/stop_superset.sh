#!/bin/bash

##########################################################################
# Stop Apache Superset
##########################################################################

echo "🛑 Stopping Apache Superset..."

# Stop with docker-compose if available
if [ -f "/tmp/superset-compose.yml" ]; then
    if command -v docker-compose &> /dev/null; then
        docker-compose -f /tmp/superset-compose.yml down
    elif command -v docker &> /dev/null; then
        docker-compose -f /tmp/superset-compose.yml down
    elif command -v podman-compose &> /dev/null; then
        podman-compose -f /tmp/superset-compose.yml down
    fi
fi

# Also stop individual containers
podman stop superset superset-db superset-redis 2>/dev/null || true
podman rm superset superset-db superset-redis 2>/dev/null || true

echo "✅ Apache Superset stopped"
echo ""
echo "💡 To remove volumes (and data):"
echo "   podman volume rm superset-db superset-data"
echo ""
echo "To start again:"
echo "   bash start_superset.sh"
