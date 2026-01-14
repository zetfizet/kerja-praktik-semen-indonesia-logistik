# 📊 Dokumentasi Arsitektur ETL Driver KPI

## 🏗️ Arsitektur Keseluruhan

```
┌─────────────────────────────────┐
│  PostgreSQL OLTP (Production)   │  ← Aplikasi production
│  ├── driver_armada              │
│  ├── rating                     │
│  ├── orders                     │
│  ├── perangkat_gps_driver       │
│  └── rekening_driver            │
└──────────────┬──────────────────┘
               │
               ▼
     ┌─────────────────────┐
     │  Apache Airflow     │      ← Orchestration & Scheduling
     │  ETL DAG            │
     │  - extract_task     │
     │  - transform_task   │
     │  - validate_task    │
     └─────────────┬───────┘
                   │
                   ▼
┌─────────────────────────────────┐
│  PostgreSQL Analytics (OLAP)    │  ← Business Intelligence
│  └── analytics schema           │
│      └── fact_driver_performance│
│          ├── uuid_user          │
│          ├── avg_rating         │
│          ├── total_order        │
│          ├── gps_active_ratio   │
│          ├── rekening_status    │
│          └── kpi_score          │
└──────────────┬──────────────────┘
               │
               ▼
      ┌──────────────────┐
      │  Metabase/BI     │         ← Visualization & Reporting
      │  Dashboard       │
      └──────────────────┘
```

## 📝 Penjelasan Setiap Komponen

### 1️⃣ **OLTP Tables** (PostgreSQL Public Schema)
Database production untuk aplikasi real-time

| Table | Deskripsi |
|-------|-----------|
| `driver_armada` | Master data driver (nama, tipe armada) |
| `rating` | Setiap rating yang diberikan ke driver |
| `orders` | Setiap order yang di-handle driver |
| `perangkat_gps_driver` | Device GPS yang aktif/non-aktif per driver |
| `rekening_driver` | Status rekening (ACTIVE, SUSPENDED) |

### 2️⃣ **Airflow DAG** (Orchestration)
Berjalan **setiap hari** (schedule: @daily) dengan 3 tahap:

```
extract_oltp_data 
    ↓
transform_load_analytics 
    ↓
validate_data_quality
```

**Task Details:**

| Task | Fungsi | Input | Output |
|------|--------|-------|--------|
| **extract_oltp_data** | Check apakah OLTP tables ada | PostgreSQL OLTP | Validation result |
| **transform_load_analytics** | Join data, calculate KPI, insert ke fact table | OLTP tables | fact_driver_performance table |
| **validate_data_quality** | Generate quality report | fact table | Stats & metrics |

### 3️⃣ **Analytics Schema** (PostgreSQL Analytics)
Tabel warehouse untuk analysis dan reporting

**`fact_driver_performance` Table Structure:**
```sql
- driver_kpi_id (PK)
- uuid_user (FK) → Unique driver identifier
- avg_rating → Average rating (0-5) in last 30 days
- total_order → Total orders in last 30 days  
- gps_active_ratio → % GPS devices active (0-100)
- rekening_status → Account status
- kpi_score → Weighted KPI score (0-5)
  Formula: (avg_rating × 0.3) + (order_ratio × 0.3) + (gps_ratio × 0.4)
- created_at → When record created
- updated_at → Last update timestamp
```

## 🔄 ETL Flow Explanation

### **EXTRACT** 
```python
Query OLTP tables untuk ambil data terbaru
- driver_armada → get unique drivers
- rating → get ratings (last 30 days)
- orders → get orders (last 30 days)
- perangkat_gps_driver → get GPS status
- rekening_driver → get account status
```

### **TRANSFORM**
```python
Aggregate & Calculate KPI:
1. GROUP BY uuid_user
2. AVG(rating_value) → avg_rating
3. COUNT(order_id) → total_order
4. COUNT(GPS WHERE active=true)/COUNT(GPS) → gps_active_ratio
5. Get rekening_status
6. Calculate KPI_SCORE dengan weighted formula
```

### **LOAD**
```python
INSERT INTO analytics.fact_driver_performance
Menggunakan UPSERT (ON CONFLICT):
- Jika driver sudah ada (same uuid_user + date)
- UPDATE record lama dengan data terbaru
- Jika driver baru: INSERT record baru
```

### **VALIDATE**
```python
Quality Checks:
- Total records loaded
- Distinct drivers counted
- KPI score range (min, max, avg)
- Alert jika ada anomali
```

## 🚀 Cara Menjalankan ETL

### Option 1: Manual Run (via Airflow UI)
1. Buka `http://localhost:8080`
2. Cari DAG "etl_driver_kpi"
3. Klik play button untuk trigger manual run
4. Monitor di Graph View

### Option 2: Automatic (Scheduled)
- DAG otomatis jalan setiap hari pukul 00:00 (default)
- Edit `schedule="@daily"` di DAG untuk ubah schedule

### Option 3: Via CLI
```bash
docker exec airflow-scheduler airflow dags trigger etl_driver_kpi
```

## 📊 Verifikasi Data

### Check OLTP data
```sql
SELECT * FROM public.driver_armada;
SELECT * FROM public.rating;
SELECT COUNT(*) FROM public.orders;
```

### Check Analytics result
```sql
SELECT * FROM analytics.fact_driver_performance 
WHERE updated_at >= CURRENT_DATE;

-- Lihat KPI statistics
SELECT 
    COUNT(*) as total_drivers,
    ROUND(AVG(kpi_score), 2) as avg_kpi,
    MIN(kpi_score) as min_kpi,
    MAX(kpi_score) as max_kpi
FROM analytics.fact_driver_performance
WHERE updated_at >= CURRENT_DATE;
```

## 🔧 Troubleshooting

### 1. DAG tidak terdeteksi
```bash
# Check DAG syntax
docker exec airflow-scheduler python -c "from dags.etl_driver_kpi import dag; print('OK')"

# Restart scheduler
docker restart airflow-scheduler airflow-dag-processor
```

### 2. Task gagal (check logs)
```bash
docker logs airflow-scheduler | tail -100
docker logs airflow-scheduler | grep etl_driver_kpi
```

### 3. PostgreSQL connection error
```bash
docker exec airflow-scheduler airflow connections list
docker exec airflow-scheduler airflow connections test postgres_default
```

## 📈 Next Steps

1. **Setup Metabase** untuk visualisasi
2. **Add more metrics** (e.g., driver rejection rate, response time)
3. **Implement SLA alerts** jika KPI score turun
4. **Add data lineage tracking** untuk audit trail
5. **Create incremental loads** (hanya load data baru instead of full refresh)

## 📞 Support

Untuk pertanyaan lebih lanjut tentang:
- SQL tuning → Optimize query performance
- Scheduling → Setup backups dan retries
- Monitoring → Setup alerts untuk task failures

---
**Created:** January 12, 2026  
**Version:** 1.0
