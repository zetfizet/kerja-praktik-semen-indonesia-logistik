-- Create Analytics Schema jika belum ada
CREATE SCHEMA IF NOT EXISTS analytics;

-- Fact Table: Driver Performance KPI
CREATE TABLE IF NOT EXISTS analytics.fact_driver_performance (
    driver_kpi_id SERIAL PRIMARY KEY,
    uuid_user UUID NOT NULL,
    avg_rating DECIMAL(3, 2),
    total_order INTEGER,
    gps_active_ratio DECIMAL(5, 2),
    rekening_status VARCHAR(50),
    kpi_score DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(uuid_user, updated_at::DATE)
);

-- Create index untuk performa query
CREATE INDEX IF NOT EXISTS idx_driver_kpi_uuid ON analytics.fact_driver_performance(uuid_user);
CREATE INDEX IF NOT EXISTS idx_driver_kpi_updated_at ON analytics.fact_driver_performance(updated_at);

-- Dimension Table: Driver (optional tapi recommended untuk normalisasi)
CREATE TABLE IF NOT EXISTS analytics.dim_driver (
    driver_id SERIAL PRIMARY KEY,
    uuid_user UUID UNIQUE NOT NULL,
    driver_name VARCHAR(255),
    created_date DATE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dim_driver_uuid ON analytics.dim_driver(uuid_user);
