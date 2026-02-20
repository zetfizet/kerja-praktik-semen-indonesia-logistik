FROM docker.io/apache/airflow:3.1.3-python3.13

# Install mlflow and other dependencies
USER root
USER airflow

# Install Python packages
RUN pip install --no-cache-dir \
    mlflow==2.19.0 \
    psycopg2-binary
