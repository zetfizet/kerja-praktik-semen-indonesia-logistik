#!/bin/bash
# 🔧 BACKUP - Export via PostgreSQL Command Line
# Jalankan dari server yang bisa reach database

# Jika punya SSH access ke server:
# ssh user@devom.silog.co.id "bash export_tables.sh"

# Atau jalankan commands ini di terminal yang bisa reach Postgres:

PGPASSWORD=om pg_dump -h devom.silog.co.id -U om -d devom.silog.co.id \
  --table=driver_armada --data-only --csv > driver_armada.csv

PGPASSWORD=om pg_dump -h devom.silog.co.id -U om -d devom.silog.co.id \
  --table=rating --data-only --csv > rating.csv

PGPASSWORD=om pg_dump -h devom.silog.co.id -U om -d devom.silog.co.id \
  --table=delivery_order --data-only --csv > delivery_order.csv

PGPASSWORD=om pg_dump -h devom.silog.co.id -U om -d devom.silog.co.id \
  --table=perangkat_gps_driver --data-only --csv > perangkat_gps_driver.csv

PGPASSWORD=om pg_dump -h devom.silog.co.id -U om -d devom.silog.co.id \
  --table=rekening_driver --data-only --csv > rekening_driver.csv

# Move to data folder
mv *.csv /home/rafiez/airflow-stack/data/

# Verify
ls -lh /home/rafiez/airflow-stack/data/
