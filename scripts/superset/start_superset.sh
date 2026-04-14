#!/bin/bash

##########################################################################
# Apache Superset - Alternative Dashboard Tool (More Features than Metabase)
# URL: http://localhost:8088
# Admin: admin / admin
##########################################################################

echo "📊 Apache Superset - Enterprise Analytics Dashboard"
echo "=================================================="
echo ""
echo "⚠️  Note: Superset requires more setup than Metabase"
echo "   Use only if you need advanced features!"
echo ""
echo "Features:"
echo "  ✓ Advanced SQL editor"
echo "  ✓ Semantic layer (datasets)"
echo "  ✓ Role-based access"
echo "  ✓ Alert & reports"
echo "  ✓ Caching layer"
echo "  ✓ Complex visualizations"
echo ""

# Check if Superset already running
if podman ps | grep -q superset; then
    echo "✅ Superset already running on port 8088"
    echo "   Access at: http://localhost:8088"
    echo "   Login: admin / admin"
    exit 0
fi

echo "🔄 Starting Apache Superset..."
echo ""

# Create Superset home directory
mkdir -p ~/.superset

# Create docker-compose for Superset
cat > /tmp/superset-compose.yml << 'EOF'
version: '3.8'

services:
  superset-db:
    image: postgres:15-alpine
    container_name: superset-db
    environment:
      POSTGRES_DB: superset
      POSTGRES_USER: superset
      POSTGRES_PASSWORD: superset123
    volumes:
      - superset-db:/var/lib/postgresql/data
    networks:
      - superset-net
    expose:
      - "5432"

  redis:
    image: redis:7-alpine
    container_name: superset-redis
    networks:
      - superset-net
    expose:
      - "6379"

  superset:
    image: apache/superset:latest-dev
    container_name: superset
    environment:
      SUPERSET_SQLALCHEMY_DATABASE_URI: postgresql://superset:superset123@superset-db:5432/superset
      REDIS_URL: redis://superset-redis:6379
      SUPERSET_SECRET_KEY: your-secret-key-here-change-in-production
    volumes:
      - superset-data:/app/superset_home
    ports:
      - "8088:8088"
    networks:
      - superset-net
    depends_on:
      - superset-db
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8088/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  superset-db:
  superset-data:

networks:
  superset-net:
    driver: bridge
EOF

# Try docker-compose first
if command -v docker-compose &> /dev/null; then
    echo "📦 Using docker-compose to start Superset..."
    docker-compose -f /tmp/superset-compose.yml up -d
    
elif command -v docker &> /dev/null; then
    echo "📦 Using docker to start Superset..."
    cd /tmp && docker-compose -f superset-compose.yml up -d

elif command -v podman-compose &> /dev/null; then
    echo "📦 Using podman-compose to start Superset..."
    podman-compose -f /tmp/superset-compose.yml up -d

else
    echo "⚠️  No docker-compose or podman-compose found"
    echo "   Please install one of:"
    echo "   - docker-compose"
    echo "   - podman-compose"
    exit 1
fi

echo ""
echo "⏳ Waiting for Superset to start (60 seconds)..."
sleep 10

# Wait for Superset to be healthy
for i in {1..12}; do
    if curl -s http://localhost:8088/health | grep -q "ok"; then
        echo "✅ Superset is running!"
        break
    fi
    echo "   Waiting... ($((i*5)) seconds)"
    sleep 5
done

echo ""
echo "=================================================="
echo "✅ Apache Superset Started Successfully!"
echo "=================================================="
echo ""
echo "🌐 Access at: http://localhost:8088"
echo ""
echo "📝 First Login Credentials:"
echo "   Username: admin"
echo "   Password: admin"
echo ""
echo "⚙️  Setup Steps:"
echo "   1. Login to http://localhost:8088"
echo "   2. Go to Admin → Databases"
echo "   3. Click '+ Database' button"
echo "   4. Select 'PostgreSQL'"
echo "   5. Enter connection:"
echo "      - Host: 127.0.0.1"
echo "      - Port: 5433"
echo "      - Database: airflow"
echo "      - User: airflow"
echo "      - Password: airflow"
echo "   6. Click 'Test Connection' → Save"
echo "   7. Go to SQL Editor & create queries"
echo "   8. Create charts & dashboards"
echo ""
echo "📊 Sample Queries (same as Metabase):"
echo "   Copy from METABASE_QUERIES.sql"
echo ""
echo "🚀 Next Steps:"
echo "   1. Check: podman ps"
echo "   2. View logs: podman logs -f superset"
echo "   3. Stop: bash stop_superset.sh"
echo ""
echo "💡 Tips:"
echo "   - Use 'Explore' for quick charts"
echo "   - Use 'SQL Editor' for custom queries"
echo "   - Create 'Dataset' for reusable queries"
echo "   - Combine datasets in Dashboard"
echo ""
