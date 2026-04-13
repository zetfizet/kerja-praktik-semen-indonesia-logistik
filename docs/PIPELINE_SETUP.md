# Pipeline Setup

Dokumen ini menjelaskan setup pipeline end-to-end dari ingestion sampai analytics.

## Alur Data

1. `weather_data_fetch` mengambil prakiraan cuaca dari BMKG ke `public.fact_weather_hourly`.
2. `warehouse_sync_optimized` sinkronisasi data operasional source ke schema `public`.
3. `routing_enrichment` hitung metrik rute dan upsert ke `public.fact_route_metrics`.
4. `warehouse_transform_simple` membuat agregasi harian di schema `analytics`.

## Konfigurasi Wajib

- `.env` dari `.env.example`
- `compose.yml` lokal dari template `compose.example.yml`
- Secret Airflow terisi valid

## Urutan Inisialisasi Disarankan

1. Start semua service.
2. Pastikan database `warehouse` tersedia.
3. Jalankan DAG ini sekali secara manual:
- `weather_data_fetch`
- `warehouse_sync_optimized`
- `routing_enrichment`
- `warehouse_transform_simple`

4. Validasi output:
- `public.fact_weather_hourly` terisi
- tabel operasional di `public` terisi
- `public.fact_route_metrics` terisi
- tabel agregasi di `analytics` terisi

## Schedule Operasional

Schedule default saat ini:
- `weather_data_fetch`: per jam (`0 * * * *`)
- `warehouse_sync_optimized`: harian 02:00
- `routing_enrichment`: harian 02:30
- `warehouse_transform_simple`: harian 03:00

## Validasi Cepat SQL

```sql
SELECT COUNT(*) FROM public.fact_weather_hourly;
SELECT COUNT(*) FROM public.fact_route_metrics;
SELECT table_name FROM information_schema.tables WHERE table_schema='analytics' ORDER BY table_name;
```

## Catatan Praktik Baik

- Jangan ubah DAG schedule langsung di production tanpa change record.
- Pisahkan konfigurasi environment per kantor/proyek.
- Simpan kredensial hanya di `.env` lokal atau secret manager.
