#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping Airflow containers...${NC}"

# Stop containers
podman stop airflow-webserver airflow-scheduler airflow-worker airflow-triggerer postgres valkey 2>/dev/null

# Remove containers
echo -e "${YELLOW}Removing containers...${NC}"
podman rm airflow-webserver airflow-scheduler airflow-worker airflow-triggerer postgres valkey 2>/dev/null

# Remove volumes
echo -e "${YELLOW}Removing volumes...${NC}"
podman volume rm postgres-data valkey-data 2>/dev/null

echo -e "${GREEN}✓ Airflow containers stopped and cleaned up${NC}"

# Show status
echo -e "${YELLOW}Current containers:${NC}"
podman ps -a
