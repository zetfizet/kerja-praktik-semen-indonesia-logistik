# Airflow ELT Pipeline

Project ini berisi pipeline Airflow untuk mengambil data dari source database, memuatnya ke warehouse PostgreSQL, lalu membangun tabel analitik untuk Metabase plus enrichment routing dan cuaca.

## Gambaran Arsitektur

```
Source DB + BMKG API + GraphHopper
  ↓
weather_data_fetch / warehouse_sync_optimized / routing_enrichment
  ↓
PostgreSQL warehouse (public.*)
  ↓
warehouse_transform_simple
  ↓
analytics.* untuk dashboard Metabase
```

## Quick Start

1. Masuk ke folder project.

```bash
cd mufrih
```

2. Salin template environment.

```bash
cp .env.example .env
```

3. Isi minimal variabel ini di `.env`:
- `AIRFLOW_SECRET_KEY`
- `AIRFLOW_FERNET_KEY`
- `POSTGRES_PASSWORD`

4. Buat file compose lokal dari template aman.

```bash
cp compose.example.yml compose.yml
```

5. Jalankan stack.

```bash
podman-compose up -d
```

Alternatif Docker:

```bash
docker compose -f compose.yml up -d
```

6. Akses service:
- Airflow: http://localhost:8080
- Metabase: http://localhost:3000
- Postgres host port: 5433

7. Jalankan DAG pertama kali secara manual (di Airflow UI):
- `weather_data_fetch`
- `warehouse_sync_optimized`
- `routing_enrichment`
- `warehouse_transform_simple`

## DAG Aktif dan Schedule

- `weather_data_fetch` (`0 * * * *`)
  - Ambil data BMKG per jam dan simpan ke `public.fact_weather_hourly`.
- `warehouse_sync_optimized` (`0 2 * * *`)
  - Sinkronisasi data source ke `public.*` dengan incremental + soft delete untuk tabel transaksional.
- `routing_enrichment` (`30 2 * * *`)
  - Hitung metrik rute dan upsert ke `public.fact_route_metrics`.
- `warehouse_transform_simple` (`0 3 * * *`)
  - Transformasi data `public.*` menjadi agregasi harian di `analytics.*`.

## Validasi Cepat Setelah Deploy

Jalankan query ini pada database warehouse:

```sql
SELECT COUNT(*) FROM public.fact_weather_hourly;
SELECT COUNT(*) FROM public.fact_route_metrics;
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'analytics'
ORDER BY table_name;
```

## Konfigurasi Environment

Lihat detail lengkap di dokumen:
- `docs/ENVIRONMENT_VARIABLES.md`

Variabel penting:
- `AIRFLOW_SECRET_KEY`
- `AIRFLOW_FERNET_KEY`
- `POSTGRES_PASSWORD`
- `GRAPHHOPPER_API_KEY`
- `GRAPHHOPPER_BASE_URL`
- `GRAPHHOPPER_ALLOW_FALLBACK`

## Operasional Harian

Lihat runbook operasional:
- `docs/OPERATIONS_RUNBOOK.md`

Contoh command yang paling sering dipakai:

```bash
podman-compose ps
podman-compose logs airflow-webserver --tail=100
podman-compose restart airflow-webserver
```

## Batasan Saat Ini

- Beberapa kredensial database masih hardcoded di DAG dan belum sepenuhnya berbasis environment variable.
- Untuk deployment production, disarankan migrasi kredensial ke secret manager atau Airflow Connection.


## Struktur Project

```
dags/                DAG utama dan utility
docs/                Dokumentasi tambahan
logs/                Log runtime lokal
compose.example.yml  Template compose aman
.env.example         Template environment
README.md            Ringkasan project
```

## Dokumentasi Terkait

- [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md)
- [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)
- [docs/PIPELINE_SETUP.md](docs/PIPELINE_SETUP.md)
- [docs/SOFT_DELETE_IMPLEMENTATION.md](docs/SOFT_DELETE_IMPLEMENTATION.md)
- [docs/ENVIRONMENT_VARIABLES.md](docs/ENVIRONMENT_VARIABLES.md)
- [docs/OPERATIONS_RUNBOOK.md](docs/OPERATIONS_RUNBOOK.md)
