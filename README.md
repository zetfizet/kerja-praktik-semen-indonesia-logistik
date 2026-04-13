# Airflow ELT Pipeline

Project ini berisi pipeline Airflow untuk mengambil data dari source database, memuatnya ke warehouse PostgreSQL, lalu membangun tabel analitik untuk Metabase dan kebutuhan routing/weather enrichment (tanpa MLflow).

## Gambaran Arsitektur

```
Source DB
  ↓
weather_data_fetch / routing_enrichment / warehouse_sync_optimized
  ↓
PostgreSQL warehouse (public.*)
  ↓
warehouse_transform_simple
  ↓
analytics.* untuk dashboard Metabase
```

## DAG Aktif

Empat DAG yang saat ini dipakai sebagai alur utama:

- `weather_data_fetch` - ambil data cuaca BMKG dan simpan ke warehouse.
- `warehouse_sync_optimized` - sync tabel operasional ke schema `public` dengan incremental sync dan soft delete untuk tabel transaksional.
- `routing_enrichment` - hitung metric rute dan upsert ke `public.fact_route_metrics`.
- `warehouse_transform_simple` - transform data `public.*` menjadi agregasi harian di `analytics.*`.

Dokumen dan DAG yang digunakan untuk operasional harian ada di folder utama project ini.

## File Yang Perlu Dipush

Untuk repo kantor, yang aman dan memang perlu dipush adalah source code dan template-nya, bukan secret atau data runtime.

- `dags/` dan `plugins/`
- `compose.example.yml`
- `.env.example`
- `README.md`
- `docs/` dan skrip setup/utilitas yang memang dipakai
- file SQL yang dipakai untuk inisialisasi atau transformasi

Yang sebaiknya tidak dipush:

- `.env`
- `compose.yml` jika masih berisi password/secret hardcoded
- `logs/`
- cache, `__pycache__/`, dan file runtime lain

Kalau `compose.yml` sudah disanitasi penuh dan hanya memakai environment variable, file itu bisa ikut dipush. Dalam kondisi repo ini sekarang, gunakan `compose.example.yml` sebagai template yang aman.

## Requirement

- Docker atau Podman
- `docker compose` atau `podman-compose`
- PostgreSQL 16
- Akses jaringan ke source database
- Python 3.13+ jika ingin menjalankan skrip bantu di host

## Konfigurasi

1. Salin template environment.

```bash
cp .env.example .env
```

2. Isi nilai berikut di `.env`:

- `AIRFLOW_SECRET_KEY`
- `AIRFLOW_FERNET_KEY`
- `POSTGRES_PASSWORD`
- credential source database jika berbeda dari default

3. Jika perlu, sesuaikan `compose.example.yml` lalu gunakan itu sebagai acuan untuk `compose.yml` lokal.

## Menjalankan Project

1. Pastikan file environment sudah terisi.
2. Jalankan stack container.

```bash
podman-compose up -d
```

Kalau memakai Docker Compose, perintah setara juga bisa dipakai.

3. Buka Airflow di:

```text
http://localhost:8080
```

4. Ambil password awal dari log container jika memakai mode standalone.

## Output Utama

- Data raw tersinkron ke schema `public` di warehouse PostgreSQL.
- Tabel analitik harian dibuat di schema `analytics`.
- Hasil routing enrichment tersedia di `public.fact_route_metrics`.
- Metabase dapat query langsung ke `analytics.*`.

## Struktur Project

```
dags/              DAG utama dan utility
docs/              Dokumentasi tambahan
plugins/           Plugin Airflow
logs/              Log runtime lokal
*.sql              Script setup dan transformasi
compose.example.yml Template compose aman tanpa secret
.env.example       Template environment
```

## Dokumentasi Terkait

- [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)
- [docs/PIPELINE_SETUP.md](docs/PIPELINE_SETUP.md)
- [docs/SOFT_DELETE_IMPLEMENTATION.md](docs/SOFT_DELETE_IMPLEMENTATION.md)
- [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md)
