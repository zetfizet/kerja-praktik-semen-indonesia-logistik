# Prediksi Cuaca Per Hari - Real Time Tables

## Table 1: Prediksi Cuaca Kota Surabaya

### SQL Query
```sql
SELECT 
    TO_CHAR(waktu, 'YYYY-MM-DD') as "Tanggal",
    TO_CHAR(waktu, 'DY') as "Hari",
    TO_CHAR(waktu, 'HH24:00') as "Jam",
    'Kota Surabaya' as "Kota",
    CASE 
        WHEN cuaca ILIKE '%Cerah%' THEN '☀️ Cerah'
        WHEN cuaca ILIKE '%Hujan Ringan%' THEN '🌦️ Hujan Ringan'
        WHEN cuaca ILIKE '%Hujan%' THEN '🌧️ Hujan'
        WHEN cuaca ILIKE '%Berawan%' THEN '☁️ Berawan'
        WHEN cuaca ILIKE '%Mendung%' THEN '⛅ Mendung'
        ELSE '🌫️ ' || cuaca
    END as "Cuaca",
    ROUND(suhu_celsius::numeric, 1) as "Suhu_C",
    kelembapan as "Kelembapan_%"
FROM weather.fact_weather_hourly
WHERE lokasi = 'Kota Surabaya'
ORDER BY waktu ASC
```

### Metabase Setup
1. Buka Metabase → **"+" → New Question**
2. Database: **warehouse**
3. Mode: **Native Query (SQL)**
4. Paste query di atas
5. Chart Type: **Table**
6. **Save** dengan nama "Prediksi Cuaca Surabaya"

### Metabase Styling
1. **Klik "⚙️ Settings"** pada chart
2. **Column formatting:**
   - Suhu_C: Highlight dengan Red gradient jika > 32
   - Kelembapan_%: Highlight dengan Blue gradient jika > 85
3. **Enable hover:** Untuk melihat detail
4. **Auto-refresh:** Every 1 hour

---

## Table 2: Prediksi Cuaca Gresik

### SQL Query
```sql
SELECT 
    TO_CHAR(waktu, 'YYYY-MM-DD') as "Tanggal",
    TO_CHAR(waktu, 'DY') as "Hari",
    TO_CHAR(waktu, 'HH24:00') as "Jam",
    'Gresik' as "Kota",
    CASE 
        WHEN cuaca ILIKE '%Cerah%' THEN '☀️ Cerah'
        WHEN cuaca ILIKE '%Hujan Ringan%' THEN '🌦️ Hujan Ringan'
        WHEN cuaca ILIKE '%Hujan%' THEN '🌧️ Hujan'
        WHEN cuaca ILIKE '%Berawan%' THEN '☁️ Berawan'
        WHEN cuaca ILIKE '%Mendung%' THEN '⛅ Mendung'
        ELSE '🌫️ ' || cuaca
    END as "Cuaca",
    ROUND(suhu_celsius::numeric, 1) as "Suhu_C",
    kelembapan as "Kelembapan_%"
FROM weather.fact_weather_hourly
WHERE lokasi = 'Gresik'
ORDER BY waktu ASC
```

### Metabase Setup
1. Buka Metabase → **"+" → New Question**
2. Database: **warehouse**
3. Mode: **Native Query (SQL)**
4. Paste query di atas
5. Chart Type: **Table**
6. **Save** dengan nama "Prediksi Cuaca Gresik"

### Metabase Styling
1. **Klik "⚙️ Settings"** pada chart
2. **Column formatting:**
   - Suhu_C: Highlight dengan Red gradient jika > 32
   - Kelembapan_%: Highlight dengan Blue gradient jika > 85
3. **Enable hover:** Untuk melihat detail
4. **Auto-refresh:** Every 1 hour

---

## Create Dashboard with Both Tables

### Step 1: Create Dashboard
1. **Klik "+" → New Dashboard**
2. Nama: **"Prediksi Cuaca Harian - Real Time"**
3. Klik **"Create Dashboard"**

### Step 2: Add Both Tables
1. **Edit Dashboard** (pencil icon)
2. **Klik "+"** untuk add card
3. **Buat/Select "Prediksi Cuaca Surabaya"** table
4. **Save** ke dashboard
5. **Klik "+"** lagi untuk add card kedua
6. **Buat/Select "Prediksi Cuaca Gresik"** table
7. **Save** ke dashboard

### Step 3: Arrange Layout
```
┌─────────────────────────────────────────────────────────────┐
│ Prediksi Cuaca Kota Surabaya                                │
├─────────┬────┬─────┬──────────┬──────────────┬────────┬──────┤
│Tanggal  │Hari│Jam  │Kota      │Cuaca         │Suhu_C  │Kelembapan│
├─────────┼────┼─────┼──────────┼──────────────┼────────┼──────┤
│2026-01-27│TUE │04:00│Surabaya  │☀️ Cerah      │25      │94    │
│2026-01-27│TUE │05:00│Surabaya  │☀️ Cerah      │24      │93    │
│2026-01-27│TUE │06:00│Surabaya  │⛅ Berawan    │24      │92    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Prediksi Cuaca Gresik                                       │
├─────────┬────┬─────┬──────────┬──────────────┬────────┬──────┤
│Tanggal  │Hari│Jam  │Kota      │Cuaca         │Suhu_C  │Kelembapan│
├─────────┼────┼─────┼──────────┼──────────────┼────────┼──────┤
│2026-01-27│TUE │04:00│Gresik    │🌦️ Hujan Ringan│25      │94    │
│2026-01-27│TUE │05:00│Gresik    │☁️ Berawan     │24      │93    │
│2026-01-27│TUE │06:00│Gresik    │☀️ Cerah       │24      │92    │
└─────────────────────────────────────────────────────────────┘
```

### Step 4: Customize
1. **Title:** "Prediksi Cuaca Harian - Real Time"
2. **Description:** "Data cuaca per jam untuk Surabaya dan Gresik dengan emoji indicator"
3. **Auto-refresh:** Every 1 hour

### Step 5: Save Dashboard
Klik **"Save"** → Dashboard siap digunakan

---

## Icon Legend

| Icon | Cuaca | Kondisi |
|------|-------|---------|
| ☀️ | Cerah | Sunny |
| ⛅ | Mendung | Partly Cloudy |
| ☁️ | Berawan | Cloudy |
| 🌦️ | Hujan Ringan | Light Rain |
| 🌧️ | Hujan | Heavy Rain |
| 🌫️ | Other | Hazy/Lainnya |

---

## Expected Output

### Surabaya Table:
| Tanggal | Hari | Jam | Kota | Cuaca | Suhu_C | Kelembapan_% |
|---------|------|------|---------|-------|--------|------------|
| 2026-01-27 | TUE | 04:00 | Kota Surabaya | ☀️ Cerah | 25 | 94 |
| 2026-01-27 | TUE | 05:00 | Kota Surabaya | ☀️ Cerah | 24 | 93 |
| 2026-01-27 | TUE | 06:00 | Kota Surabaya | ⛅ Mendung | 24 | 92 |
| 2026-01-27 | TUE | 07:00 | Kota Surabaya | ☁️ Berawan | 24 | 91 |

### Gresik Table:
| Tanggal | Hari | Jam | Kota | Cuaca | Suhu_C | Kelembapan_% |
|---------|------|------|------|-------|--------|------------|
| 2026-01-27 | TUE | 04:00 | Gresik | 🌦️ Hujan Ringan | 25 | 94 |
| 2026-01-27 | TUE | 05:00 | Gresik | ☁️ Berawan | 24 | 93 |
| 2026-01-27 | TUE | 06:00 | Gresik | ☀️ Cerah | 24 | 92 |
| 2026-01-27 | TUE | 07:00 | Gresik | ⛅ Mendung | 23 | 91 |

---

## Tips

1. **Icon Display:** Emoji sudah built-in di SQL query, langsung tampil di Metabase
2. **Real-time Updates:** Set auto-refresh di dashboard untuk update setiap jam
3. **Color Coding:** Conditional formatting membantu identify kondisi ekstrem
4. **Sorting:** Sudah diatur ascending by waktu (sekarang → depan)
5. **Mobile Friendly:** Table design responsive untuk mobile devices

---

**Last Updated:** January 30, 2026  
**Database:** warehouse (postgres/postgres123)  
**Update Frequency:** Hourly via weather_data_fetch DAG

