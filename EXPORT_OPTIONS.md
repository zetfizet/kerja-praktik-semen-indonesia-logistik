# 📤 EXPORT DATA - 3 METODE

## Status Koneksi Network:
- ❌ Docker container: Tidak bisa reach database
- ❌ Host machine: Tidak bisa reach database
- ✅ pgAdmin4 UI: Bisa akses (Anda sudah verified)

**Kesimpulan:** Network routing issue - metode manual via UI adalah yang paling reliable.

---

## ✅ METODE 1: pgAdmin4 Query Tool (RECOMMENDED)

Ini adalah metode paling simple & reliable.

### Step 1: Buka pgAdmin4
```
URL: http://localhost:5050
Login dengan credentials Anda
```

### Step 2: Buka Query Tool
```
Klik: Tools → Query Tool
```

### Step 3: Untuk SETIAP table, jalankan query ini:

#### Query 1: driver_armada
```sql
SELECT * FROM driver_armada;
```
- Klik ▶️ Execute
- Klik ⋮ (menu) → Download as CSV
- Simpan sebagai: `driver_armada.csv`

#### Query 2: rating
```sql
SELECT * FROM rating;
```
→ Download: `rating.csv`

#### Query 3: delivery_order
```sql
SELECT * FROM delivery_order;
```
→ Download: `delivery_order.csv`

#### Query 4: perangkat_gps_driver
```sql
SELECT * FROM perangkat_gps_driver;
```
→ Download: `perangkat_gps_driver.csv`

#### Query 5: rekening_driver
```sql
SELECT * FROM rekening_driver;
```
→ Download: `rekening_driver.csv`

### Step 4: Copy CSV ke Folder Airflow
```bash
cp ~/Downloads/*.csv /home/rafiez/airflow-stack/data/
```

### Step 5: Run Import
```bash
bash /home/rafiez/airflow-stack/run_etl.sh
```

---

## 📄 METODE 2: COPY Command (Jika pgAdmin4 tidak punya download feature)

Di pgAdmin4 Query Tool:

```sql
-- Export driver_armada
\copy (SELECT * FROM driver_armada) TO '/tmp/driver_armada.csv' WITH CSV HEADER;

-- Export rating
\copy (SELECT * FROM rating) TO '/tmp/rating.csv' WITH CSV HEADER;

-- Export delivery_order
\copy (SELECT * FROM delivery_order) TO '/tmp/delivery_order.csv' WITH CSV HEADER;

-- Export perangkat_gps_driver
\copy (SELECT * FROM perangkat_gps_driver) TO '/tmp/perangkat_gps_driver.csv' WITH CSV HEADER;

-- Export rekening_driver
\copy (SELECT * FROM rekening_driver) TO '/tmp/rekening_driver.csv' WITH CSV HEADER;
```

Kemudian file tersimpan di `/tmp/` dan bisa didownload.

---

## 🔧 METODE 3: Command Line (Jika ada SSH access)

Jika Anda punya SSH access ke server database:

```bash
# Dari host yang bisa reach database:
PGPASSWORD=om pg_dump -h devom.silog.co.id -U om -d devom.silog.co.id \
  -t driver_armada --data-only --csv > driver_armada.csv

# Repeat untuk table lain...
```

---

## ⚡ Quick Decision Matrix

| Metode | Effort | Reliability | Recommended |
|--------|--------|-------------|-------------|
| **Metode 1: pgAdmin4 UI** | 5 min | ✅✅✅ | 👈 USE THIS |
| Metode 2: COPY Command | 3 min | ✅✅ | If Method 1 has issues |
| Metode 3: CLI Dump | 2 min | ✅✅✅ | If have SSH access |

---

## 🎯 RECOMMENDED WORKFLOW:

```
1. Buka pgAdmin4 UI
   ↓
2. Run 5 SELECT queries
   ↓
3. Download hasil sebagai CSV
   ↓
4. Copy ke /home/rafiez/airflow-stack/data/
   ↓
5. bash /home/rafiez/airflow-stack/run_etl.sh
   ↓
6. Monitor di Airflow UI
   ↓
✨ COMPLETE!
```

**Total time: 10-15 menit**

---

## ✨ Why This Approach?

❌ **Direct connection tidak work:**
- Network routing issue (tidak bisa fix dari sini)
- Database server mungkin di private network
- Firewall blocking external connections

✅ **pgAdmin4 method work:**
- Anda sudah bisa akses via UI
- UI bisa download data
- Data validated sebelum import
- Reliable & proven method

---

## 📞 Alternative Options

Jika ingin fully automated tanpa manual download:

### Option A: Setup SSH Tunnel
```bash
ssh -L 5433:localhost:5432 your_user@devom.silog.co.id -N -f
# Then connect via: localhost:5433
```

### Option B: VPN ke Database Network
- Minta IT untuk setup VPN akses
- Atau whitelist IP Anda di firewall

### Option C: Ask IT untuk expose PostgreSQL
- Minta IT buka port 5432 untuk akses eksternal
- Atau setup read-only replica

---

**🚀 ACTION NOW: Use Metode 1 (pgAdmin4 UI) - paling simple & reliable!**
