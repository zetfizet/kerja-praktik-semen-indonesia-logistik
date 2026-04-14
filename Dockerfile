FROM apache/airflow:3.1.3-python3.13

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && apt-get clean && rm -rf /var/lib/apt/lists/*

USER airflow
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --force-reinstall apache-airflow-providers-postgres

