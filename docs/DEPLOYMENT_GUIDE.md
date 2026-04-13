# Deployment Guide

Panduan ini untuk menjalankan stack Airflow ELT di environment lokal/server menggunakan Docker atau Podman.

## Scope

Pipeline yang dibahas:
- `weather_data_fetch`
- `warehouse_sync_optimized`
- `routing_enrichment`
- `warehouse_transform_simple`

Tidak mencakup MLflow.

## Prasyarat

- Docker Engine + `docker compose`, atau Podman + `podman-compose`
- Akses network ke source database
- Port yang tersedia:
  - `8080` untuk Airflow
  - `5433` untuk PostgreSQL host mapping
  - `3000` untuk Metabase (opsional)

## Langkah Deploy

1. Siapkan environment file.

```bash
cp .env.example .env
```

2. Isi nilai wajib di `.env`:
- `AIRFLOW_SECRET_KEY`
- `AIRFLOW_FERNET_KEY`
- `POSTGRES_PASSWORD`

3. Gunakan compose template aman sebagai acuan (`compose.example.yml`) untuk membuat `compose.yml` lokal.

4. Jalankan stack.

```bash
podman-compose up -d
```

atau

```bash
docker compose up -d
```

5. Validasi service:
- Airflow UI: `http://localhost:8080`
- Metabase UI (jika aktif): `http://localhost:3000`

## Post-Deploy Checklist

- Semua container `Up` dan healthy.
- DAG utama muncul di Airflow UI.
- Koneksi ke database warehouse berhasil.
- Log task tidak mengandung error import.

## Troubleshooting Singkat

- DAG tidak muncul: pastikan mount `./dags:/opt/airflow/dags` aktif.
- Error koneksi DB: cek host internal service (`postgres`) dan port internal (`5432`).
- Secret invalid: regenerate `AIRFLOW_SECRET_KEY` dan `AIRFLOW_FERNET_KEY` lalu restart service.
