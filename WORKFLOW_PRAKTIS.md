# 📊 WORKFLOW ETL LENGKAP - Panduan Praktis

## 🎯 Situasi Sekarang

✅ **Anda bisa akses:**
- pgAdmin4 di http://localhost:5050 (bisa lihat data aplikasi)
- Airflow di http://localhost:8080
- Database aplikasi di devom.silog.co.id (via pgAdmin4)

❌ **Tidak bisa akses:**
- Direct Python connection dari Docker ke database eksternal (network isolated)
- SSH tunnel (tidak setup)

## ✨ Solusi: Export via pgAdmin4 → Import ke Airflow

Ini adalah workflow yang **paling sederhana dan stabil**.

---

## 📋 LANGKAH-LANGKAH

### STEP 1️⃣: Buka pgAdmin4

```
URL: http://localhost:5050
Login dengan credentials Anda
```

### STEP 2️⃣: Pastikan Connected ke Database Aplikasi

Di sidebar kiri pgAdmin4, cari:
```
Servers → devom.silog.co.id
  └─ Databases → devom.silog.co.id
```

Jika belum ada, tambahkan:
```
Klik kanan Servers → Create → Server
├─ General tab:
│  └─ Name: devom.silog.co.id
├─ Connection tab:
│  ├─ Host: devom.silog.co.id (atau 172.20.145.83)
│  ├─ Port: 5432
│  ├─ Username: om
│  ├─ Password: om
│  └─ Save password: ✓
└─ Save
```

### STEP 3️⃣: Export Data sebagai CSV

Untuk **SETIAP table** di bawah, jalankan query ini di pgAdmin4:

#### Query 1: driver_armada
```
1. Klik Tools → Query Tool
2. Paste query ini:

SELECT * FROM driver_armada;

3. Klik tombol ▶️ Execute
4. Klik menu ⋮ (tiga titik) → Download as CSV
5. Simpan sebagai: driver_armada.csv
```

#### Query 2: rating
```
SELECT * FROM rating;
→ Download sebagai: rating.csv
```

#### Query 3: delivery_order
```
SELECT * FROM delivery_order;
→ Download sebagai: delivery_order.csv
```

#### Query 4: perangkat_gps_driver
```
SELECT * FROM perangkat_gps_driver;
→ Download sebagai: perangkat_gps_driver.csv
```

#### Query 5: rekening_driver
```
SELECT * FROM rekening_driver;
→ Download sebagai: rekening_driver.csv
```

### STEP 4️⃣: Copy CSV Files ke Airflow Folder

```bash
# Copy semua CSV yang didownload
cp ~/Downloads/*.csv /home/rafiez/airflow-stack/data/

# Verify
ls -lh /home/rafiez/airflow-stack/data/
```

**Expected output:**
```
-rw-r--r-- 1 user user 45K Jan 13 10:00 driver_armada.csv
-rw-r--r-- 1 user user 2.3M Jan 13 10:01 rating.csv
-rw-r--r-- 1 user user 8.9M Jan 13 10:02 delivery_order.csv
-rw-r--r-- 1 user user 150K Jan 13 10:03 perangkat_gps_driver.csv
-rw-r--r-- 1 user user 100K Jan 13 10:04 rekening_driver.csv
```

### STEP 5️⃣: Import CSV ke Airflow PostgreSQL

```bash
cd /home/rafiez/airflow-stack

# Run dari Docker container (RECOMMENDED)
docker exec airflow-webserver python3 -c "
import csv
import psycopg2
from pathlib import Path

DATA_FOLDER = Path('/home/rafiez/airflow-stack/data')
DB_CONFIG = {
    'host': 'postgres',
    'database': 'airflow',
    'user': 'airflow',
    'password': 'airflow',
    'port': 5432
}

print('\\n' + '='*80)
print('📥 CSV IMPORT')
print('='*80 + '\\n')

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

csv_files = list(DATA_FOLDER.glob('*.csv'))
total_rows = 0

for csv_path in csv_files:
    table_name = csv_path.stem
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        # Create table
        col_defs = ', '.join([f'\"{col}\" TEXT' for col in headers])
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS public.{table_name} (
                id SERIAL PRIMARY KEY,
                {col_defs}
            );
        ''')
        conn.commit()
        
        # Clear & insert
        cursor.execute(f'TRUNCATE TABLE public.{table_name} CASCADE;')
        
        rows = list(reader)
        for row in rows:
            cols = list(row.keys())
            vals = [row[col] if row[col].strip() else None for col in cols]
            cols_str = ', '.join([f'\"{c}\"' for c in cols])
            placeholders = ', '.join(['%s'] * len(cols))
            cursor.execute(f'INSERT INTO public.{table_name} ({cols_str}) VALUES ({placeholders})', vals)
        
        conn.commit()
        print(f'✅ {table_name:<35} {len(rows):>6} rows')
        total_rows += len(rows)

cursor.close()
conn.close()

print(f'\\n✨ Total: {total_rows} rows imported')
print('='*80 + '\\n')
"
```

**Expected output:**
```
================================================================================
📥 CSV IMPORT
================================================================================

✅ driver_armada                          50 rows
✅ rating                              2300 rows
✅ delivery_order                      8900 rows
✅ perangkat_gps_driver                 100 rows
✅ rekening_driver                       45 rows

✨ Total: 11395 rows imported
================================================================================
```

### STEP 6️⃣: Trigger ETL DAG

```
Buka: http://localhost:8080
Login: admin / rafie123

Navigasi ke:
  DAGs → etl_driver_kpi

Klik tombol ▶️ (Play/Trigger)
```

### STEP 7️⃣: Monitor Execution

Di Airflow UI:
```
Graph View akan menunjukkan 3 tasks:
  1. extract_oltp_data      ← Check tables exist
  2. transform_load_analytics ← Do complex JOIN & KPI calc
  3. validate_data_quality  ← Generate report

Status:
  🟢 Success = Task selesai OK
  🔴 Failed = Ada error (lihat logs)
  ⏳ Running = Sedang berjalan
```

### STEP 8️⃣: Verify Results

Query di Airflow PostgreSQL:
```bash
docker exec postgres psql -U airflow -d airflow -c "
  SELECT COUNT(*) as total_records FROM analytics.fact_driver_performance;
  SELECT uuid_user, id_armada, avg_rating, kpi_score 
  FROM analytics.fact_driver_performance 
  ORDER BY kpi_score DESC 
  LIMIT 5;
"
```

**Expected output:**
```
 total_records
───────────────
    50

        uuid_user         | id_armada | avg_rating | kpi_score
──────────────────────────────────────────────────────────────
 84b4a89d-fb15-4a7d-b76c-750617cf5fb4 |        16 |       4.50 |      4.92
 uuid-2                               |         1 |       4.80 |      4.67
 uuid-3                               |         5 |       4.60 |      4.45
 uuid-4                               |        12 |       4.50 |      4.32
 uuid-5                               |         8 |       4.40 |      4.18
```

---

## 🔄 Workflow Otomatis (Setelah Setup Awal)

Setelah Step 7 berhasil, DAG akan **otomatis berjalan setiap hari jam 00:00 UTC**:

```
SETIAP HARI:
├─ 00:00 UTC → ETL DAG trigger otomatis
├─ Extract 5 OLTP tables
├─ Transform dengan 5-table JOIN
├─ Calculate 5 KPI metrics
├─ Load ke analytics.fact_driver_performance
└─ Generate quality report
```

Anda **tidak perlu manual trigger** lagi setelah hari pertama!

---

## 📞 Quick Reference

| Langkah | Aplikasi | URL | Akses |
|---------|----------|-----|-------|
| 1 | pgAdmin4 | http://localhost:5050 | 🟢 Bisa |
| 2 | Query & Export | Query Tool | 🟢 Bisa |
| 4 | Copy Files | Terminal | 🟢 Bisa |
| 5 | Import | Docker/Terminal | 🟢 Bisa |
| 6 | Trigger DAG | http://localhost:8080 | 🟢 Bisa |
| 7 | Monitor | Graph View | 🟢 Bisa |
| 8 | Verify | PostgreSQL | 🟢 Bisa |

---

## ⚡ Shortcuts

```bash
# Check CSV files
ls -lh /home/rafiez/airflow-stack/data/

# View Airflow logs
tail -100 /home/rafiez/airflow-stack/airflow/logs/etl_driver_kpi/*/task_logs.txt

# Check DAG status
docker exec airflow-scheduler airflow dags list-runs -d etl_driver_kpi

# Force trigger DAG
docker exec airflow-scheduler airflow dags trigger etl_driver_kpi
```

---

## 🚀 Summary

**Workflow ringkas:**

```
1. pgAdmin4 → SELECT * FROM each_table
2. Download CSV
3. Copy ke /home/rafiez/airflow-stack/data/
4. docker exec → import script
5. Airflow UI → Trigger DAG
6. Monitor di Graph View
7. Query analytics.fact_driver_performance
8. ✨ Done!
```

**Estimated time:** 15-30 menit untuk setup awal

---

## 💾 Credentials Reference

```
pgAdmin4:
  • URL: http://localhost:5050
  • Database: devom.silog.co.id
  • User: om
  • Password: om
  • Port: 5432

Airflow:
  • URL: http://localhost:8080
  • User: admin
  • Password: rafie123
```

---

**👉 Next Action: Buka pgAdmin4 dan mulai export data!** 🚀
