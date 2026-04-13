# Environment Variables Reference

Dokumen ini merangkum variabel environment yang dipakai oleh stack Airflow di project ini.

## Cara Pakai

1. Salin template:

```bash
cp .env.example .env
```

2. Isi variabel wajib.
3. Jalankan compose menggunakan `compose.yml` lokal.

## Variabel Wajib

| Variable | Dipakai di | Default | Wajib | Keterangan |
|---|---|---|---|---|
| `AIRFLOW_SECRET_KEY` | Airflow API/webserver | none | Ya | Secret key untuk komponen API/web Airflow. |
| `AIRFLOW_FERNET_KEY` | Airflow core | none | Ya | Kunci enkripsi untuk metadata sensitif Airflow. |
| `POSTGRES_PASSWORD` | Postgres + Airflow DB conn + Metabase DB conn | `airflow` (fallback compose) | Ya | Password user `airflow` pada service Postgres lokal. |

## Variabel Integrasi Routing

| Variable | Dipakai di | Default | Wajib | Keterangan |
|---|---|---|---|---|
| `GRAPHHOPPER_API_KEY` | `utils/graphhopper_client.py` | kosong | Direkomendasikan | API key GraphHopper cloud, wajib untuk mode VRP optimize. |
| `GRAPHHOPPER_BASE_URL` | `utils/graphhopper_client.py` | `https://graphhopper.com/api/1` | Tidak | Endpoint GraphHopper (cloud/self-hosted). |
| `GRAPHHOPPER_ALLOW_FALLBACK` | `utils/graphhopper_client.py` | `false` di compose | Tidak | Jika `true`, gunakan estimasi fallback saat API routing gagal. |

## Variabel Opsional Source DB

Variabel berikut tersedia di template sebagai override, namun implementasi DAG saat ini belum sepenuhnya membaca semua variabel ini secara konsisten.

| Variable | Tujuan |
|---|---|
| `SOURCE_DB_HOST` | Host database sumber |
| `SOURCE_DB_PORT` | Port database sumber |
| `SOURCE_DB_USER` | Username database sumber |
| `SOURCE_DB_PASSWORD` | Password database sumber |
| `SOURCE_DB_NAME` | Nama database sumber |

## Catatan Keamanan

- Jangan commit file `.env`.
- Jangan hardcode credential nyata ke `compose.yml`.
- Untuk production, simpan secret di secret manager atau Airflow Connections.
- Putar (rotate) `AIRFLOW_SECRET_KEY` dan `AIRFLOW_FERNET_KEY` jika pernah terekspos.

## Checklist Validasi

- Airflow service bisa start tanpa error secret.
- Postgres healthcheck status healthy.
- DAG dapat konek ke warehouse (`postgres:5432`) dari container Airflow.
- Integrasi routing berjalan sesuai mode (`GraphHopper` langsung atau fallback).