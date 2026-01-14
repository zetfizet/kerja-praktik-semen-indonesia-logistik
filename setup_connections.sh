#!/bin/bash
# Script untuk setup PostgreSQL connection di Airflow

docker exec airflow-webserver airflow connections add \
    --conn-type postgres \
    --conn-host postgres \
    --conn-login airflow \
    --conn-password airflow \
    --conn-port 5432 \
    --conn-schema airflow \
    postgres_default \
    2>&1 | grep -v "already exists" || echo "Connection ready"
