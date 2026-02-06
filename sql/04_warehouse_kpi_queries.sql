-- ============================================================================
-- KPI DRIVER QUERIES - untuk digunakan di pgAdmin atau Metabase/Grafana
-- ============================================================================

-- ============================================================================
-- KPI 1: DELIVERY PERFORMANCE
-- ============================================================================

-- Query 1.1: Delivery Performance Summary per Driver
SELECT 
    d.uuid_user,
    d.nama_driver,
    COUNT(DISTINCT do.id_order) as total_deliveries,
    COUNT(DISTINCT CASE WHEN do.status_pengiriman = 'COMPLETED' THEN do.id_order END) as completed_deliveries,
    COUNT(DISTINCT CASE WHEN do.status_pengiriman = 'FAILED' THEN do.id_order END) as failed_deliveries,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN do.status_pengiriman = 'COMPLETED' THEN do.id_order END) / 
          NULLIF(COUNT(DISTINCT do.id_order), 0), 2) as completion_rate_pct,
    ROUND(AVG(CASE WHEN r.rating_score IS NOT NULL THEN r.rating_score END), 2) as avg_rating,
    COUNT(DISTINCT CASE WHEN do.status_pengiriman = 'COMPLETED' AND 
          do.tanggal_delivery <= do.waktu_delivery_estimate THEN do.id_order END) as on_time_deliveries,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN do.status_pengiriman = 'COMPLETED' AND 
          do.tanggal_delivery <= do.waktu_delivery_estimate THEN do.id_order END) / 
          NULLIF(COUNT(DISTINCT CASE WHEN do.status_pengiriman = 'COMPLETED' THEN do.id_order END), 0), 2) as on_time_rate_pct
FROM warehouse.driver d
LEFT JOIN warehouse.driver_armada da ON d.uuid_user = da.uuid_user AND da.tanggal_selesai IS NULL
LEFT JOIN warehouse.delivery_order do ON da.id_armada = do.id_armada
LEFT JOIN warehouse.rating r ON do.id_order = r.id_order
GROUP BY d.uuid_user, d.nama_driver
ORDER BY total_deliveries DESC;


-- Query 1.2: Delivery Performance by Date Range
SELECT 
    DATE(do.tanggal_order) as delivery_date,
    COUNT(DISTINCT do.id_order) as total_deliveries,
    COUNT(DISTINCT CASE WHEN do.status_pengiriman = 'COMPLETED' THEN do.id_order END) as completed,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN do.status_pengiriman = 'COMPLETED' THEN do.id_order END) / 
          NULLIF(COUNT(DISTINCT do.id_order), 0), 2) as completion_rate_pct,
    ROUND(AVG(CASE WHEN r.rating_score IS NOT NULL THEN r.rating_score END), 2) as avg_rating
FROM warehouse.delivery_order do
LEFT JOIN warehouse.rating r ON do.id_order = r.id_order
WHERE do.tanggal_order >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(do.tanggal_order)
ORDER BY delivery_date DESC;


-- Query 1.3: Bottom Performers (Low Rating, Low Completion Rate)
SELECT 
    d.uuid_user,
    d.nama_driver,
    COUNT(DISTINCT do.id_order) as total_deliveries,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN do.status_pengiriman = 'COMPLETED' THEN do.id_order END) / 
          NULLIF(COUNT(DISTINCT do.id_order), 0), 2) as completion_rate_pct,
    ROUND(AVG(CASE WHEN r.rating_score IS NOT NULL THEN r.rating_score END), 2) as avg_rating,
    COUNT(DISTINCT CASE WHEN r.rating_score <= 2 THEN r.id_rating END) as bad_ratings
FROM warehouse.driver d
LEFT JOIN warehouse.driver_armada da ON d.uuid_user = da.uuid_user AND da.tanggal_selesai IS NULL
LEFT JOIN warehouse.delivery_order do ON da.id_armada = do.id_armada
LEFT JOIN warehouse.rating r ON do.id_order = r.id_order
GROUP BY d.uuid_user, d.nama_driver
HAVING COUNT(DISTINCT do.id_order) >= 10
ORDER BY avg_rating ASC
LIMIT 20;


-- ============================================================================
-- KPI 2: DRIVER PRODUCTIVITY
-- ============================================================================

-- Query 2.1: Active vs Idle Time per Driver
SELECT 
    d.uuid_user,
    d.nama_driver,
    SUM(CASE WHEN lad.status_aktivitas = 'ACTIVE' THEN lad.durasi_menit ELSE 0 END) as active_minutes,
    SUM(CASE WHEN lad.status_aktivitas = 'IDLE' THEN lad.durasi_menit ELSE 0 END) as idle_minutes,
    SUM(CASE WHEN lad.status_aktivitas = 'BREAK' THEN lad.durasi_menit ELSE 0 END) as break_minutes,
    SUM(CASE WHEN lad.status_aktivitas = 'OFFLINE' THEN lad.durasi_menit ELSE 0 END) as offline_minutes,
    SUM(lad.durasi_menit) as total_minutes,
    ROUND(100.0 * SUM(CASE WHEN lad.status_aktivitas = 'ACTIVE' THEN lad.durasi_menit ELSE 0 END) / 
          NULLIF(SUM(lad.durasi_menit), 0), 2) as active_percentage,
    ROUND(100.0 * SUM(CASE WHEN lad.status_aktivitas = 'IDLE' THEN lad.durasi_menit ELSE 0 END) / 
          NULLIF(SUM(lad.durasi_menit), 0), 2) as idle_percentage
FROM warehouse.driver d
LEFT JOIN warehouse.log_aktifitas_driver lad ON d.uuid_user = lad.uuid_user 
    AND lad.jam_mulai >= CURRENT_DATE - INTERVAL '7 days'
WHERE d.status = 'ACTIVE'
GROUP BY d.uuid_user, d.nama_driver
ORDER BY active_percentage DESC;


-- Query 2.2: Daily Productivity Trend
SELECT 
    DATE(lad.jam_mulai) as activity_date,
    COUNT(DISTINCT lad.uuid_user) as active_drivers,
    SUM(CASE WHEN lad.status_aktivitas = 'ACTIVE' THEN lad.durasi_menit ELSE 0 END) as total_active_minutes,
    SUM(CASE WHEN lad.status_aktivitas = 'IDLE' THEN lad.durasi_menit ELSE 0 END) as total_idle_minutes,
    ROUND(100.0 * SUM(CASE WHEN lad.status_aktivitas = 'ACTIVE' THEN lad.durasi_menit ELSE 0 END) / 
          NULLIF(SUM(lad.durasi_menit), 0), 2) as fleet_active_percentage
FROM warehouse.log_aktifitas_driver lad
WHERE lad.jam_mulai >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(lad.jam_mulai)
ORDER BY activity_date DESC;


-- ============================================================================
-- KPI 3: SAFETY DRIVING BEHAVIOR
-- ============================================================================

-- Query 3.1: Risk Score Distribution per Driver
SELECT 
    d.uuid_user,
    d.nama_driver,
    COUNT(DISTINCT lpa.id_log) as total_trips,
    ROUND(AVG(lpa.risk_score), 2) as avg_risk_score,
    MAX(lpa.risk_score) as max_risk_score,
    COUNT(DISTINCT CASE WHEN lpa.risk_score >= 70 THEN lpa.id_log END) as high_risk_trips,
    COUNT(DISTINCT CASE WHEN lpa.risk_score >= 40 AND lpa.risk_score < 70 THEN lpa.id_log END) as medium_risk_trips,
    COUNT(DISTINCT CASE WHEN lpa.risk_score < 40 THEN lpa.id_log END) as low_risk_trips,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN lpa.risk_score >= 70 THEN lpa.id_log END) / 
          NULLIF(COUNT(DISTINCT lpa.id_log), 0), 2) as high_risk_percentage
FROM warehouse.driver d
LEFT JOIN warehouse.log_perjalanan_armada lpa ON d.uuid_user = lpa.uuid_user 
    AND lpa.waktu_mulai >= CURRENT_DATE - INTERVAL '30 days'
WHERE d.status = 'ACTIVE'
GROUP BY d.uuid_user, d.nama_driver
ORDER BY avg_risk_score DESC;


-- Query 3.2: Unsafe Driving Events
SELECT 
    d.uuid_user,
    d.nama_driver,
    COUNT(DISTINCT CASE WHEN lpa.pengereman_mendadak = TRUE THEN lpa.id_log END) as harsh_braking_events,
    COUNT(DISTINCT CASE WHEN lpa.akselerasi_kasar = TRUE THEN lpa.id_log END) as harsh_acceleration_events,
    COUNT(DISTINCT CASE WHEN lpa.kecepatan_terlampaui = TRUE THEN lpa.id_log END) as speeding_events,
    COUNT(DISTINCT lpa.id_log) as total_trips,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN lpa.pengereman_mendadak = TRUE THEN lpa.id_log END) / 
          NULLIF(COUNT(DISTINCT lpa.id_log), 0), 2) as harsh_braking_rate_pct,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN lpa.akselerasi_kasar = TRUE THEN lpa.id_log END) / 
          NULLIF(COUNT(DISTINCT lpa.id_log), 0), 2) as harsh_acceleration_rate_pct,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN lpa.kecepatan_terlampaui = TRUE THEN lpa.id_log END) / 
          NULLIF(COUNT(DISTINCT lpa.id_log), 0), 2) as speeding_rate_pct
FROM warehouse.driver d
LEFT JOIN warehouse.log_perjalanan_armada lpa ON d.uuid_user = lpa.uuid_user 
    AND lpa.waktu_mulai >= CURRENT_DATE - INTERVAL '30 days'
WHERE d.status = 'ACTIVE'
GROUP BY d.uuid_user, d.nama_driver
ORDER BY harsh_braking_events DESC, harsh_acceleration_events DESC;


-- Query 3.3: High Risk Journeys Detail
SELECT 
    d.nama_driver,
    a.nomor_plat,
    lpa.lokasi_mulai,
    lpa.lokasi_akhir,
    lpa.waktu_mulai,
    lpa.durasi_menit,
    lpa.jarak_km,
    lpa.kecepatan_max_kmh,
    lpa.kecepatan_avg_kmh,
    CASE WHEN lpa.pengereman_mendadak THEN 'YES' ELSE 'NO' END as harsh_braking,
    CASE WHEN lpa.akselerasi_kasar THEN 'YES' ELSE 'NO' END as harsh_acceleration,
    CASE WHEN lpa.kecepatan_terlampaui THEN 'YES' ELSE 'NO' END as speeding,
    lpa.risk_score
FROM warehouse.log_perjalanan_armada lpa
JOIN warehouse.driver d ON lpa.uuid_user = d.uuid_user
JOIN warehouse.armada a ON lpa.id_armada = a.id_armada
WHERE lpa.risk_score >= 70
    AND lpa.waktu_mulai >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY lpa.risk_score DESC, lpa.waktu_mulai DESC;


-- ============================================================================
-- KPI 4: ROUTE COMPLIANCE
-- ============================================================================

-- Query 4.1: Route Performance Analysis
SELECT 
    d.uuid_user,
    d.nama_driver,
    COUNT(DISTINCT lpa.id_order) as total_routes,
    ROUND(AVG(lpa.jarak_km), 2) as avg_distance_km,
    ROUND(AVG(lpa.durasi_menit), 2) as avg_duration_minutes,
    ROUND(AVG(lpa.kecepatan_avg_kmh), 2) as avg_speed_kmh,
    ROUND(AVG(CASE WHEN do.waktu_delivery_estimate IS NOT NULL 
              THEN EXTRACT(EPOCH FROM (do.tanggal_delivery - do.tanggal_pickup)) / 60 ELSE NULL END), 2) as avg_delivery_time_minutes,
    COUNT(DISTINCT CASE WHEN do.tanggal_delivery <= do.waktu_delivery_estimate THEN do.id_order END) as on_time_deliveries
FROM warehouse.log_perjalanan_armada lpa
JOIN warehouse.driver d ON lpa.uuid_user = d.uuid_user
LEFT JOIN warehouse.delivery_order do ON lpa.id_order = do.id_order
WHERE lpa.waktu_mulai >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY d.uuid_user, d.nama_driver
ORDER BY total_routes DESC;


-- ============================================================================
-- KPI 5: CUSTOMER SATISFACTION
-- ============================================================================

-- Query 5.1: Rating Distribution per Driver
SELECT 
    d.uuid_user,
    d.nama_driver,
    COUNT(DISTINCT r.id_rating) as total_ratings,
    COUNT(DISTINCT CASE WHEN r.rating_score = 5 THEN r.id_rating END) as five_star,
    COUNT(DISTINCT CASE WHEN r.rating_score = 4 THEN r.id_rating END) as four_star,
    COUNT(DISTINCT CASE WHEN r.rating_score = 3 THEN r.id_rating END) as three_star,
    COUNT(DISTINCT CASE WHEN r.rating_score = 2 THEN r.id_rating END) as two_star,
    COUNT(DISTINCT CASE WHEN r.rating_score = 1 THEN r.id_rating END) as one_star,
    ROUND(AVG(r.rating_score), 2) as avg_rating,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN r.rating_score >= 4 THEN r.id_rating END) / 
          NULLIF(COUNT(DISTINCT r.id_rating), 0), 2) as positive_rating_pct
FROM warehouse.driver d
LEFT JOIN warehouse.rating r ON d.uuid_user = r.uuid_user 
    AND r.created_at >= CURRENT_DATE - INTERVAL '30 days'
WHERE d.status = 'ACTIVE'
GROUP BY d.uuid_user, d.nama_driver
ORDER BY avg_rating DESC;


-- Query 5.2: Rating Comments Analysis (Top Issues)
SELECT 
    r.aspek_rating,
    COUNT(DISTINCT r.id_rating) as count,
    ROUND(AVG(r.rating_score), 2) as avg_rating_for_aspect,
    STRING_AGG(DISTINCT SUBSTRING(r.komentar, 1, 100), ' | ') as sample_comments
FROM warehouse.rating r
WHERE r.created_at >= CURRENT_DATE - INTERVAL '30 days'
    AND r.komentar IS NOT NULL
GROUP BY r.aspek_rating
ORDER BY count DESC;


-- Query 5.3: Driver Satisfaction Trend (Weekly)
SELECT 
    DATE_TRUNC('week', r.created_at) as week_start,
    d.nama_driver,
    COUNT(DISTINCT r.id_rating) as ratings_count,
    ROUND(AVG(r.rating_score), 2) as avg_rating
FROM warehouse.rating r
JOIN warehouse.driver d ON r.uuid_user = d.uuid_user
WHERE r.created_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY DATE_TRUNC('week', r.created_at), d.nama_driver
ORDER BY week_start DESC, avg_rating DESC;


-- ============================================================================
-- KPI 6: DRIVER READINESS
-- ============================================================================

-- Query 6.1: Driver Readiness Status
SELECT 
    d.uuid_user,
    d.nama_driver,
    d.status as driver_status,
    d.nomor_identitas,
    d.nomor_telepon,
    COUNT(DISTINCT rd.id_rekening) as total_bank_accounts,
    COUNT(DISTINCT CASE WHEN rd.status_rekening = 'AKTIF' THEN rd.id_rekening END) as active_rekening,
    COUNT(DISTINCT CASE WHEN rd.status_rekening = 'INACTIVE' THEN rd.id_rekening END) as inactive_rekening,
    CASE 
        WHEN COUNT(DISTINCT CASE WHEN rd.status_rekening = 'AKTIF' THEN rd.id_rekening END) > 0 
        THEN 'READY'
        ELSE 'NOT READY'
    END as readiness_status,
    MAX(rd.updated_at) as last_bank_update
FROM warehouse.driver d
LEFT JOIN warehouse.rekening_driver rd ON d.uuid_user = rd.uuid_user
GROUP BY d.uuid_user, d.nama_driver, d.status, d.nomor_identitas, d.nomor_telepon
ORDER BY readiness_status DESC, d.nama_driver;


-- Query 6.2: Bank Account Status Overview
SELECT 
    COUNT(DISTINCT d.uuid_user) as total_drivers,
    COUNT(DISTINCT CASE WHEN d.status = 'ACTIVE' THEN d.uuid_user END) as active_drivers,
    COUNT(DISTINCT CASE WHEN EXISTS (
        SELECT 1 FROM warehouse.rekening_driver rd 
        WHERE rd.uuid_user = d.uuid_user AND rd.status_rekening = 'AKTIF'
    ) THEN d.uuid_user END) as drivers_with_active_account,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN EXISTS (
        SELECT 1 FROM warehouse.rekening_driver rd 
        WHERE rd.uuid_user = d.uuid_user AND rd.status_rekening = 'AKTIF'
    ) THEN d.uuid_user END) / NULLIF(COUNT(DISTINCT d.uuid_user), 0), 2) as active_account_pct
FROM warehouse.driver d;


-- ============================================================================
-- COMPREHENSIVE KPI DASHBOARD QUERY
-- ============================================================================

-- Semua KPI dalam satu query untuk dashboard overview
WITH driver_summary AS (
    SELECT 
        d.uuid_user,
        d.nama_driver,
        -- Delivery Performance
        COUNT(DISTINCT do.id_order) as total_deliveries,
        ROUND(100.0 * COUNT(DISTINCT CASE WHEN do.status_pengiriman = 'COMPLETED' THEN do.id_order END) / 
              NULLIF(COUNT(DISTINCT do.id_order), 0), 2) as completion_rate_pct,
        ROUND(AVG(CASE WHEN r.rating_score IS NOT NULL THEN r.rating_score END), 2) as avg_rating,
        -- Safety
        ROUND(AVG(lpa.risk_score), 2) as avg_risk_score,
        -- Productivity
        SUM(CASE WHEN lad.status_aktivitas = 'ACTIVE' THEN lad.durasi_menit ELSE 0 END) as active_minutes,
        -- Bank Account
        COUNT(DISTINCT CASE WHEN rd.status_rekening = 'AKTIF' THEN rd.id_rekening END) as active_rekening
    FROM warehouse.driver d
    LEFT JOIN warehouse.driver_armada da ON d.uuid_user = da.uuid_user AND da.tanggal_selesai IS NULL
    LEFT JOIN warehouse.delivery_order do ON da.id_armada = do.id_armada 
        AND do.tanggal_order >= CURRENT_DATE - INTERVAL '30 days'
    LEFT JOIN warehouse.rating r ON do.id_order = r.id_order
    LEFT JOIN warehouse.log_perjalanan_armada lpa ON d.uuid_user = lpa.uuid_user 
        AND lpa.waktu_mulai >= CURRENT_DATE - INTERVAL '30 days'
    LEFT JOIN warehouse.log_aktifitas_driver lad ON d.uuid_user = lad.uuid_user 
        AND lad.jam_mulai >= CURRENT_DATE - INTERVAL '7 days'
    LEFT JOIN warehouse.rekening_driver rd ON d.uuid_user = rd.uuid_user
    WHERE d.status = 'ACTIVE'
    GROUP BY d.uuid_user, d.nama_driver
)
SELECT 
    uuid_user,
    nama_driver,
    total_deliveries,
    completion_rate_pct,
    avg_rating,
    avg_risk_score,
    active_minutes,
    active_rekening,
    CASE 
        WHEN completion_rate_pct >= 95 AND avg_rating >= 4.5 THEN 'A'
        WHEN completion_rate_pct >= 90 AND avg_rating >= 4.0 THEN 'B'
        WHEN completion_rate_pct >= 80 AND avg_rating >= 3.5 THEN 'C'
        ELSE 'D'
    END as performance_grade
FROM driver_summary
ORDER BY completion_rate_pct DESC, avg_rating DESC;


-- ============================================================================
-- END OF KPI QUERIES
-- ============================================================================
