# 7-Day Hourly Forecast - Per City

## Table 1: Extended 7-Day Forecast - Kota Surabaya

### SQL Query
```sql
SELECT 
    DATE(waktu)::TEXT as "Tanggal",
    TO_CHAR(waktu, 'DY') as "Hari",
    TO_CHAR(waktu, 'HH:00') as "Jam",
    CASE 
        WHEN cuaca ILIKE '%Hujan Lebat%' THEN '⛈️ ' || cuaca
        WHEN cuaca ILIKE '%Hujan Ringan%' THEN '🌧️ ' || cuaca
        WHEN cuaca ILIKE '%Cerah%' THEN '☀️ ' || cuaca
        WHEN cuaca ILIKE '%Mendung%' THEN '☁️ ' || cuaca
        WHEN cuaca ILIKE '%Berawan%' THEN '⛅ ' || cuaca
        ELSE '🌫️ ' || cuaca
    END as "Cuaca",
    ROUND(suhu_celsius::NUMERIC, 0)::INT as "Suhu_C",
    kelembapan as "Kelembapan_%",
    arah_angin as "Angin",
    ROUND(kecepatan_angin::NUMERIC, 1) as "Kec_Angin_ms"
FROM weather.fact_weather_hourly
WHERE lokasi = 'Kota Surabaya' 
AND waktu >= CURRENT_DATE
ORDER BY waktu ASC
```

### Metabase Setup
1. **Buka Metabase** → **"+" → New Question**
2. **Database:** warehouse
3. **Mode:** Native Query (SQL)
4. **Paste query di atas**
5. **Chart Type:** Table
6. **Save** dengan nama **"7-Day Forecast - Kota Surabaya"**

### Styling
- Column Width: Auto
- Row Height: Comfortable
- Conditional Formatting:
  - Suhu_C > 30°C → Red
  - Suhu_C 25-30°C → Yellow
  - Cuaca = "⛈️ Hujan Lebat" → Dark Blue
  - Cuaca = "🌧️ Hujan Ringan" → Light Blue
  - Cuaca = "☀️ Cerah" → Yellow

---

## Table 2: Extended 7-Day Forecast - Gresik

### SQL Query
```sql
SELECT 
    DATE(waktu)::TEXT as "Tanggal",
    TO_CHAR(waktu, 'DY') as "Hari",
    TO_CHAR(waktu, 'HH:00') as "Jam",
    CASE 
        WHEN cuaca ILIKE '%Hujan Lebat%' THEN '⛈️ ' || cuaca
        WHEN cuaca ILIKE '%Hujan Ringan%' THEN '🌧️ ' || cuaca
        WHEN cuaca ILIKE '%Cerah%' THEN '☀️ ' || cuaca
        WHEN cuaca ILIKE '%Mendung%' THEN '☁️ ' || cuaca
        WHEN cuaca ILIKE '%Berawan%' THEN '⛅ ' || cuaca
        ELSE '🌫️ ' || cuaca
    END as "Cuaca",
    ROUND(suhu_celsius::NUMERIC, 0)::INT as "Suhu_C",
    kelembapan as "Kelembapan_%",
    arah_angin as "Angin",
    ROUND(kecepatan_angin::NUMERIC, 1) as "Kec_Angin_ms"
FROM weather.fact_weather_hourly
WHERE lokasi = 'Gresik' 
AND waktu >= CURRENT_DATE
ORDER BY waktu ASC
```

### Metabase Setup
1. **Buka Metabase** → **"+" → New Question**
2. **Database:** warehouse
3. **Mode:** Native Query (SQL)
4. **Paste query di atas**
5. **Chart Type:** Table
6. **Save** dengan nama **"7-Day Forecast - Gresik"**

### Styling
- Column Width: Auto
- Row Height: Comfortable
- Conditional Formatting:
  - Suhu_C > 30°C → Red
  - Suhu_C 25-30°C → Yellow
  - Cuaca = "⛈️ Hujan Lebat" → Dark Blue
  - Cuaca = "🌧️ Hujan Ringan" → Light Blue
  - Cuaca = "☀️ Cerah" → Yellow

---

## Create Dashboard with Both Tables

### Step 1: Create Dashboard
1. **Klik "+" → New Dashboard**
2. **Nama:** "7-Day Hourly Forecast"
3. **Klik "Create Dashboard"**

### Step 2: Add Both Tables
1. **Edit Dashboard** (pencil icon)
2. **Klik "+"** untuk add card
3. **Select "7-Day Forecast - Kota Surabaya"**
4. **Save** ke dashboard
5. **Klik "+"** lagi
6. **Select "7-Day Forecast - Gresik"**
7. **Save** ke dashboard

### Step 3: Arrange Layout
```
┌─────────────────────────────────────────────────────────┐
│  7-Day Hourly Forecast - Kota Surabaya                  │
├─────────┬────┬─────┬──────────┬────────┬────────┬──────┤
│Tanggal  │Hari│Jam  │Cuaca     │Suhu_C  │Kelembapan│Angin│
├─────────┼────┼─────┼──────────┼────────┼────────┼──────┤
│2026-01-30│WED │00:00│☀️ Cerah  │24      │85      │Timur │
│2026-01-30│WED │01:00│☀️ Cerah  │23      │87      │Timur │
│2026-01-30│WED │02:00│⛅ Berawan│22      │89      │Tenggara│
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  7-Day Hourly Forecast - Gresik                         │
├─────────┬────┬─────┬──────────┬────────┬────────┬──────┤
│Tanggal  │Hari│Jam  │Cuaca     │Suhu_C  │Kelembapan│Angin│
├─────────┼────┼─────┼──────────┼────────┼────────┼──────┤
│2026-01-30│WED │00:00│🌧️ Hujan Ringan│25      │92      │Barat │
│2026-01-30│WED │01:00│☁️ Berawan│26      │90      │Barat │
│2026-01-30│WED │02:00│☀️ Cerah  │25      │88      │Timur │
└─────────────────────────────────────────────────────────┘
```

### Step 4: Customize Dashboard
1. **Title:** "7-Day Hourly Forecast - Real Time"
2. **Description:** "Extended 7-day weather forecast per hour untuk Surabaya dan Gresik"
3. **Auto-refresh:** Every 1 hour
4. **Full screen mode:** Optional

### Step 5: Save Dashboard
**Klik "Save"** → Dashboard siap digunakan

---

## Expected Output

### Kota Surabaya Table:
| Tanggal | Hari | Jam | Cuaca | Suhu_C | Kelembapan_% | Angin | Kec_Angin_ms |
|---------|------|------|-------|--------|------------|-------|------------|
| 2026-01-30 | WED | 00:00 | ☀️ Cerah | 24 | 85 | Timur | 2.5 |
| 2026-01-30 | WED | 01:00 | ☀️ Cerah | 23 | 87 | Timur | 2.2 |
| 2026-01-30 | WED | 02:00 | ⛅ Berawan | 22 | 89 | Tenggara | 1.8 |
| 2026-01-30 | WED | 03:00 | ☁️ Mendung | 21 | 91 | Barat Daya | 1.5 |

### Gresik Table:
| Tanggal | Hari | Jam | Cuaca | Suhu_C | Kelembapan_% | Angin | Kec_Angin_ms |
|---------|------|------|-------|--------|------------|-------|------------|
| 2026-01-30 | WED | 00:00 | 🌧️ Hujan Ringan | 25 | 92 | Barat | 3.2 |
| 2026-01-30 | WED | 01:00 | ☁️ Berawan | 26 | 90 | Barat | 3.0 |
| 2026-01-30 | WED | 02:00 | ☀️ Cerah | 25 | 88 | Timur | 2.5 |
| 2026-01-30 | WED | 03:00 | ⛅ Berawan | 24 | 87 | Timur Laut | 2.1 |

---

## Icon Legend

| Icon | Kondisi | Arti |
|------|---------|------|
| ☀️ | Cerah | Clear/Sunny |
| ⛅ | Berawan | Partly Cloudy |
| ☁️ | Mendung | Cloudy |
| 🌧️ | Hujan Ringan | Light Rain |
| ⛈️ | Hujan Lebat | Heavy Rain/Thunderstorm |
| 🌫️ | Other | Hazy/Fog |

---

## Tips

1. **Scrollable Tables:** Horizontal scroll untuk melihat semua kolom
2. **Real-time Updates:** Set auto-refresh di dashboard
3. **Conditional Formatting:** Highlight kondisi ekstrem (suhu tinggi, hujan lebat)
4. **Mobile Friendly:** Table design responsive
5. **Easy Comparison:** Side-by-side tables untuk bandingkan 2 kota

---

**Last Updated:** January 30, 2026  
**Database:** warehouse (postgres/postgres123)  
**Update Frequency:** Hourly via weather_data_fetch DAG
