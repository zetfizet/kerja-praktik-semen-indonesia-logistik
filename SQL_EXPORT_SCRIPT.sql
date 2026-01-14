# 📄 SQL SCRIPT - Export Tables to CSV
# Jalankan di pgAdmin4 Query Tool

-- 1. COPY driver_armada ke CSV
\copy (SELECT * FROM driver_armada) TO '/tmp/driver_armada.csv' WITH CSV HEADER;

-- 2. COPY rating ke CSV
\copy (SELECT * FROM rating) TO '/tmp/rating.csv' WITH CSV HEADER;

-- 3. COPY delivery_order ke CSV
\copy (SELECT * FROM delivery_order) TO '/tmp/delivery_order.csv' WITH CSV HEADER;

-- 4. COPY perangkat_gps_driver ke CSV
\copy (SELECT * FROM perangkat_gps_driver) TO '/tmp/perangkat_gps_driver.csv' WITH CSV HEADER;

-- 5. COPY rekening_driver ke CSV
\copy (SELECT * FROM rekening_driver) TO '/tmp/rekening_driver.csv' WITH CSV HEADER;

-- List files yang sudah dibuat
-- Di terminal: ls -lh /tmp/*.csv

-- Atau dari query tool, select dan download hasil:
SELECT * FROM driver_armada;      -- klik Download
SELECT * FROM rating;             -- klik Download
SELECT * FROM delivery_order;      -- klik Download
SELECT * FROM perangkat_gps_driver; -- klik Download
SELECT * FROM rekening_driver;     -- klik Download
