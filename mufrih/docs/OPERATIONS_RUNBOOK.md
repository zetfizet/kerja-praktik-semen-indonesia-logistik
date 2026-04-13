# Operations Runbook

Runbook ini dipakai untuk operasional harian stack Airflow ELT.

## Lokasi Kerja

Semua command dijalankan dari folder project:

```bash
cd mufrih
```

## Command Operasional Dasar

Start stack:

```bash
podman-compose up -d
```

Stop stack:

```bash
podman-compose down
```

Lihat status service:

```bash
podman-compose ps
```

Restart webserver Airflow:

```bash
podman-compose restart airflow-webserver
```

Lihat log Airflow (100 baris terakhir):

```bash
podman-compose logs airflow-webserver --tail=100
```

Lihat log Postgres:

```bash
podman-compose logs postgres --tail=100
```

Jika menggunakan Docker Compose, ganti `podman-compose` dengan `docker compose -f compose.yml`.

## Checklist Harian

- Semua service status `Up` dan healthy.
- DAG utama muncul di Airflow UI.
- Tidak ada import error pada DAG.
- Run jadwal dini hari selesai tanpa failed task.

## Urutan Triage Jika Ada Incident

1. Cek status container (`podman-compose ps`).
2. Cek log service yang gagal (`airflow-webserver` atau `postgres`).
3. Cek DAG run detail di Airflow UI.
4. Verifikasi koneksi DB warehouse dari task logs.
5. Jika terkait routing, cek status GraphHopper dan mode fallback.

## Masalah Umum dan Solusi

### DAG tidak muncul di Airflow

- Pastikan mount `./dags:/opt/airflow/dags` aktif di compose.
- Cek error import pada log webserver.
- Restart webserver setelah update DAG.

### Airflow gagal start karena secret

- Periksa `AIRFLOW_SECRET_KEY` dan `AIRFLOW_FERNET_KEY` di `.env`.
- Pastikan nilainya bukan placeholder.
- Restart service setelah perbaikan `.env`.

### Task gagal koneksi ke Postgres

- Dari dalam container Airflow, host DB harus `postgres` dan port `5432`.
- Pastikan service Postgres healthy.
- Cek credential user `airflow` sesuai `POSTGRES_PASSWORD`.

### Routing enrichment lambat atau gagal

- Cek `GRAPHHOPPER_BASE_URL` dan `GRAPHHOPPER_API_KEY`.
- Jika outage eksternal, aktifkan fallback (`GRAPHHOPPER_ALLOW_FALLBACK=true`) sesuai kebijakan tim.

## Verifikasi Data Setelah Recovery

Jalankan query cepat pada database warehouse:

```sql
SELECT COUNT(*) FROM public.fact_weather_hourly;
SELECT COUNT(*) FROM public.fact_route_metrics;
SELECT table_name FROM information_schema.tables WHERE table_schema='analytics' ORDER BY table_name;
```

## Eskalasi

Eskalasi ke engineer pipeline jika terjadi kondisi berikut:

- Gagal start berulang setelah restart dan validasi environment.
- Kegagalan DAG beruntun lebih dari 2 siklus jadwal.
- Data quality mismatch signifikan pada output analytics.
- Kebutuhan hotfix kode DAG atau perubahan skema database.