# Documentation Index

Dokumen resmi project ada di folder `docs/` dan tidak bergantung pada folder `archive/`.

## Daftar Dokumen

- `DEPLOYMENT_GUIDE.md`
  - Cara deploy stack Airflow di Docker/Podman.
  - Checklist verifikasi service dan troubleshooting dasar.

- `PIPELINE_SETUP.md`
  - Urutan setup pipeline dari ingestion sampai analytics.
  - Schedule DAG aktif dan validasi output SQL.

- `SOFT_DELETE_IMPLEMENTATION.md`
  - Prinsip implementasi soft delete (`deleted_at`).
  - Dampak ke sinkronisasi dan query dashboard.

- `ENVIRONMENT_VARIABLES.md`
  - Referensi variabel environment yang dipakai compose/DAG.
  - Nilai wajib, default, dan catatan keamanan.

- `OPERATIONS_RUNBOOK.md`
  - Command operasional harian (start/stop/restart/log).
  - Checklist triage saat DAG atau service bermasalah.

## Aturan Dokumentasi

- Semua update operasional terbaru ditulis di folder `docs/`.
- Folder `archive/` (jika ada di lokal) dianggap non-operasional dan tidak jadi sumber referensi utama.

## Prioritas Baca

1. `DEPLOYMENT_GUIDE.md` untuk deploy awal.
2. `PIPELINE_SETUP.md` untuk setup alur data dan validasi output.
3. `ENVIRONMENT_VARIABLES.md` untuk konfigurasi aman.
4. `OPERATIONS_RUNBOOK.md` untuk operasi dan troubleshooting harian.
