#!/bin/bash
# Setup helper script untuk Airflow data import dan ETL

set -e

echo "🚀 AIRFLOW DATA IMPORT & ETL SETUP"
echo "======================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_DIR="/home/rafiez/airflow-stack"

print_menu() {
    echo -e "${BLUE}=== PILIH OPSI ===${NC}"
    echo "1. Import data dari CSV"
    echo "2. Jalankan ETL DAG"
    echo "3. Check data di database"
    echo "4. View logs Airflow"
    echo "5. Lihat panduan lengkap"
    echo "6. Exit"
    echo ""
}

import_csv() {
    echo -e "${YELLOW}📊 Starting CSV Import...${NC}"
    
    if [ ! -d "$PROJECT_DIR/data" ]; then
        echo -e "${RED}❌ Folder /data tidak ditemukan!${NC}"
        echo "Silakan export CSV dari database aplikasi ke: $PROJECT_DIR/data/"
        return
    fi
    
    csv_count=$(find "$PROJECT_DIR/data" -name "*.csv" 2>/dev/null | wc -l)
    if [ "$csv_count" -eq 0 ]; then
        echo -e "${RED}❌ Tidak ada CSV files di $PROJECT_DIR/data/${NC}"
        echo "Silakan export data sebagai CSV terlebih dahulu"
        return
    fi
    
    echo -e "${GREEN}✅ Found $csv_count CSV files${NC}"
    python3 "$PROJECT_DIR/import_csv.py"
}

run_etl() {
    echo -e "${YELLOW}🔄 Triggering ETL DAG...${NC}"
    
    echo "Trigger DAG melalui Airflow UI:"
    echo "  1. Buka: http://localhost:8080"
    echo "  2. Cari DAG: etl_driver_kpi"
    echo "  3. Klik play button (Run)"
    echo ""
    echo "Atau via CLI:"
    echo "  docker exec airflow-scheduler airflow dags trigger etl_driver_kpi"
    echo ""
    read -p "Jalankan via CLI? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker exec airflow-scheduler airflow dags trigger etl_driver_kpi
        echo -e "${GREEN}✅ DAG triggered!${NC}"
        echo "Check status di: http://localhost:8080"
    fi
}

check_data() {
    echo -e "${YELLOW}🔍 Checking database...${NC}"
    echo ""
    echo "Running queries..."
    
    PGPASSWORD=airflow psql -h localhost -U airflow -d airflow << SQL
SELECT 'jenis_armada' as table_name, COUNT(*) as rows FROM jenis_armada
UNION ALL
SELECT 'driver_armada', COUNT(*) FROM driver_armada
UNION ALL
SELECT 'rating', COUNT(*) FROM rating
UNION ALL
SELECT 'orders', COUNT(*) FROM orders
ORDER BY table_name;
SQL
}

view_logs() {
    echo -e "${YELLOW}📋 Airflow Logs${NC}"
    echo ""
    echo "1. Webserver logs"
    echo "2. Scheduler logs"
    echo "3. DAG processor logs"
    read -p "Pilih (1-3): " choice
    case $choice in
        1) docker logs airflow-webserver | tail -50 ;;
        2) docker logs airflow-scheduler | tail -50 ;;
        3) docker logs airflow-dag-processor | tail -50 ;;
        *) echo "Invalid choice" ;;
    esac
}

view_guide() {
    if [ -f "$PROJECT_DIR/PANDUAN_IMPORT_DATA.md" ]; then
        less "$PROJECT_DIR/PANDUAN_IMPORT_DATA.md"
    else
        echo "Panduan tidak ditemukan"
    fi
}

# Main loop
while true; do
    echo ""
    print_menu
    read -p "Input (1-6): " choice
    echo ""
    
    case $choice in
        1) import_csv ;;
        2) run_etl ;;
        3) check_data ;;
        4) view_logs ;;
        5) view_guide ;;
        6) echo -e "${GREEN}Goodbye!${NC}"; exit 0 ;;
        *) echo -e "${RED}Invalid option${NC}" ;;
    esac
done
