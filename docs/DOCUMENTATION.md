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

## Aturan Dokumentasi

- Semua update operasional terbaru ditulis di folder `docs/`.
- Folder `archive/` (jika ada di lokal) dianggap non-operasional dan tidak jadi sumber referensi utama.
