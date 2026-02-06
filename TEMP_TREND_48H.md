# Temperature Trend 48H - Simple Query

## SQL Query untuk Metabase

```sql
SELECT 
    waktu,
    lokasi,
    suhu_celsius
FROM weather.fact_weather_hourly
WHERE waktu >= NOW()
ORDER BY lokasi, waktu ASC
```

---

## Setup di Metabase

1. **Buka Metabase** → Login
2. **Klik "+" → New Question**
3. **Pilih Database:** warehouse
4. **Pilih Mode:** Native Query (SQL)
5. **Paste query di atas**
6. **Klik "Visualize"**

---

## Chart Configuration

| Setting | Value |
|---------|-------|
| **Chart Type** | Line Chart |
| **X-axis** | waktu (unbinned) |
| **Y-axis** | suhu_celsius |
| **Series (Color)** | lokasi |
| **Title** | Temperature Trend 48H |

---

## Styling

**Colors:**
- Gresik: Orange (#FF7F0E)
- Kota Surabaya: Blue (#1F77B4)

**Settings:**
- Enable line smoothing
- Show data labels: ON
- Tooltip: Enable

---

## Expected Result

Chart akan menunjukkan:
- **X-axis:** waktu (dari sekarang sampai ke depan)
- **Y-axis:** suhu dalam °C
- **2 garis berbeda warna:** 
  - Orange = Gresik
  - Blue = Kota Surabaya

