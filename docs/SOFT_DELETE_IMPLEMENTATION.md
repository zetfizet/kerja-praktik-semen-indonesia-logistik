# Soft Delete Implementation

Dokumen ini menjelaskan implementasi soft delete untuk pipeline sinkronisasi warehouse.

## Tujuan

- Menandai data terhapus tanpa benar-benar menghapus row sumber.
- Menjaga histori perubahan untuk kebutuhan audit dan analytics.
- Tetap kompatibel dengan incremental sync.

## Prinsip Umum

- Kolom `deleted_at` dipakai sebagai flag soft delete.
- Record aktif: `deleted_at IS NULL`.
- Record soft-deleted: `deleted_at IS NOT NULL`.

## Dampak ke Pipeline

Pada `warehouse_sync_optimized`:
- Kolom `deleted_at` ikut disinkronkan untuk tabel transaksional yang relevan.
- Upsert tetap berjalan normal berdasarkan primary key.
- Query analitik perlu eksplisit filter aktif jika dibutuhkan.

## Pola Query

Hanya data aktif:

```sql
SELECT *
FROM public.orders
WHERE deleted_at IS NULL;
```

Lihat data terhapus:

```sql
SELECT *
FROM public.orders
WHERE deleted_at IS NOT NULL;
```

## Rekomendasi untuk Dashboard

- Untuk KPI operasional harian, gunakan data aktif (`deleted_at IS NULL`).
- Untuk audit/historical report, gunakan seluruh data dan pisahkan status delete sebagai dimensi.

## Checklist Verifikasi

- Tabel target punya kolom `deleted_at` sesuai desain.
- Record soft deleted di source tercermin di warehouse.
- Query analytics sudah memilih mode aktif/all-data secara sadar.
