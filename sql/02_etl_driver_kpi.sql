-- ETL: Transform dan Load ke Fact Table
-- Script ini dijalankan oleh Airflow DAG

-- STEP 1: EXTRACT & TRANSFORM
-- Aggregate data dari multiple OLTP tables ke fact table

INSERT INTO analytics.fact_driver_performance (
    uuid_user,
    avg_rating,
    total_order,
    gps_active_ratio,
    rekening_status,
    kpi_score
)
SELECT 
    d.uuid_user,
    -- EXTRACT: avg_rating dari tabel rating
    COALESCE(AVG(r.rating_value), 0)::DECIMAL(3, 2) as avg_rating,
    -- EXTRACT: total_order dari tabel orders
    COUNT(o.order_id)::INTEGER as total_order,
    -- EXTRACT & TRANSFORM: gps_active_ratio dari perangkat_gps_driver
    CASE 
        WHEN COUNT(g.gps_id) > 0 
        THEN (COUNT(CASE WHEN g.is_active = true THEN 1 END)::DECIMAL / COUNT(g.gps_id) * 100)::DECIMAL(5, 2)
        ELSE 0::DECIMAL(5, 2)
    END as gps_active_ratio,
    -- EXTRACT: rekening_status dari tabel rekening_driver
    COALESCE(k.status, 'UNKNOWN') as rekening_status,
    -- TRANSFORM: Calculate KPI Score (weighted scoring)
    ROUND(
        (COALESCE(AVG(r.rating_value), 0) * 0.3 +  -- 30% dari rating
         LEAST(COUNT(o.order_id), 100)::DECIMAL / 100 * 4 * 0.3 +  -- 30% dari order count (max 100)
         CASE 
             WHEN COUNT(g.gps_id) > 0 
             THEN (COUNT(CASE WHEN g.is_active = true THEN 1 END)::DECIMAL / COUNT(g.gps_id) * 5)
             ELSE 0
         END * 0.4  -- 40% dari GPS active ratio
        )::DECIMAL, 2
    ) as kpi_score
FROM 
    -- Prediksi: table driver_armada di OLTP
    public.driver_armada d
    LEFT JOIN public.rating r ON d.uuid_user = r.uuid_user 
        AND r.created_date >= CURRENT_DATE - INTERVAL '30 days'
    LEFT JOIN public.orders o ON d.uuid_user = o.driver_uuid 
        AND o.order_date >= CURRENT_DATE - INTERVAL '30 days'
    LEFT JOIN public.perangkat_gps_driver g ON d.uuid_user = g.uuid_user
    LEFT JOIN public.rekening_driver k ON d.uuid_user = k.uuid_user
GROUP BY 
    d.uuid_user, k.status
ON CONFLICT (uuid_user, updated_at::DATE) 
DO UPDATE SET
    avg_rating = EXCLUDED.avg_rating,
    total_order = EXCLUDED.total_order,
    gps_active_ratio = EXCLUDED.gps_active_ratio,
    rekening_status = EXCLUDED.rekening_status,
    kpi_score = EXCLUDED.kpi_score,
    updated_at = CURRENT_TIMESTAMP;
