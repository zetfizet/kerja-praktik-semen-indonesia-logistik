-- ============================================================================
-- DATA WAREHOUSE SCHEMA - DRIVER KPI ANALYTICS
-- ============================================================================
-- Schema untuk menyimpan data warehouse yang diambil dari devom.silog.co.id
-- Digunakan untuk analytics dan KPI Driver

-- ============================================================================
-- 1. MASTER DATA TABLES
-- ============================================================================

-- Table: driver (Master Data Driver)
CREATE TABLE IF NOT EXISTS warehouse.driver (
    uuid_user UUID PRIMARY KEY,
    nama_driver VARCHAR(255) NOT NULL,
    nomor_identitas VARCHAR(50),
    nomor_telepon VARCHAR(20),
    email VARCHAR(255),
    alamat TEXT,
    status VARCHAR(50),
    tanggal_registrasi TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: armada (Master Data Armada/Vehicle)
CREATE TABLE IF NOT EXISTS warehouse.armada (
    id_armada UUID PRIMARY KEY,
    nomor_plat VARCHAR(50) NOT NULL UNIQUE,
    jenis_armada VARCHAR(100),
    merk VARCHAR(100),
    tahun_produksi INTEGER,
    kapasitas_muatan NUMERIC(10,2),
    status VARCHAR(50),
    tanggal_registrasi TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: driver_armada (Relationship: Driver - Armada)
CREATE TABLE IF NOT EXISTS warehouse.driver_armada (
    id SERIAL PRIMARY KEY,
    uuid_user UUID NOT NULL REFERENCES warehouse.driver(uuid_user) ON DELETE CASCADE,
    id_armada UUID NOT NULL REFERENCES warehouse.armada(id_armada) ON DELETE CASCADE,
    tanggal_mulai DATE NOT NULL,
    tanggal_selesai DATE,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(uuid_user, id_armada, tanggal_mulai)
);

-- Table: perangkat_gps_driver (GPS Device - Driver)
CREATE TABLE IF NOT EXISTS warehouse.perangkat_gps_driver (
    id_perangkat UUID PRIMARY KEY,
    uuid_user UUID NOT NULL REFERENCES warehouse.driver(uuid_user) ON DELETE CASCADE,
    nomor_seri_gps VARCHAR(100) NOT NULL UNIQUE,
    tipe_gps VARCHAR(100),
    tanggal_install TIMESTAMP,
    status VARCHAR(50),
    last_sync TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 2. OPERATIONAL DATA TABLES
-- ============================================================================

-- Table: delivery_order (Pesanan Pengiriman)
CREATE TABLE IF NOT EXISTS warehouse.delivery_order (
    id_order UUID PRIMARY KEY,
    id_armada UUID NOT NULL REFERENCES warehouse.armada(id_armada) ON DELETE RESTRICT,
    nomor_order VARCHAR(100) NOT NULL UNIQUE,
    lokasi_asal VARCHAR(255),
    lokasi_tujuan VARCHAR(255),
    status_pengiriman VARCHAR(50),
    tanggal_order TIMESTAMP,
    tanggal_pickup TIMESTAMP,
    tanggal_delivery TIMESTAMP,
    waktu_delivery_estimate TIMESTAMP,
    berat_barang NUMERIC(10,2),
    biaya_pengiriman NUMERIC(12,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: rating (Customer Rating - KPI Customer Satisfaction)
CREATE TABLE IF NOT EXISTS warehouse.rating (
    id_rating UUID PRIMARY KEY,
    id_order UUID NOT NULL REFERENCES warehouse.delivery_order(id_order) ON DELETE CASCADE,
    uuid_user UUID NOT NULL REFERENCES warehouse.driver(uuid_user) ON DELETE RESTRICT,
    rating_score INTEGER CHECK (rating_score >= 1 AND rating_score <= 5),
    komentar TEXT,
    aspek_rating VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 3. LOG & ACTIVITY TABLES
-- ============================================================================

-- Table: log_aktifitas_driver (Driver Activity Log - Productivity)
CREATE TABLE IF NOT EXISTS warehouse.log_aktifitas_driver (
    id_log BIGSERIAL PRIMARY KEY,
    uuid_user UUID NOT NULL REFERENCES warehouse.driver(uuid_user) ON DELETE CASCADE,
    id_armada UUID REFERENCES warehouse.armada(id_armada) ON DELETE SET NULL,
    status_aktivitas VARCHAR(50), -- 'ACTIVE', 'IDLE', 'BREAK', etc
    durasi_menit INTEGER,
    jam_mulai TIMESTAMP,
    jam_selesai TIMESTAMP,
    catatan TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT log_aktifitas_chk_dates CHECK (jam_selesai > jam_mulai)
);

-- Indexes untuk query yang sering digunakan
CREATE INDEX IF NOT EXISTS idx_log_aktifitas_uuid_user ON warehouse.log_aktifitas_driver(uuid_user);
CREATE INDEX IF NOT EXISTS idx_log_aktifitas_jam_mulai ON warehouse.log_aktifitas_driver(jam_mulai);
CREATE INDEX IF NOT EXISTS idx_log_aktifitas_status ON warehouse.log_aktifitas_driver(status_aktivitas);

-- Table: log_perjalanan_armada (Journey/Travel Log - Safety & Route Compliance)
CREATE TABLE IF NOT EXISTS warehouse.log_perjalanan_armada (
    id_log BIGSERIAL PRIMARY KEY,
    uuid_user UUID NOT NULL REFERENCES warehouse.driver(uuid_user) ON DELETE CASCADE,
    id_armada UUID NOT NULL REFERENCES warehouse.armada(id_armada) ON DELETE CASCADE,
    id_order UUID REFERENCES warehouse.delivery_order(id_order) ON DELETE SET NULL,
    lokasi_mulai VARCHAR(255),
    lokasi_akhir VARCHAR(255),
    latitude_mulai NUMERIC(10,6),
    longitude_mulai NUMERIC(10,6),
    latitude_akhir NUMERIC(10,6),
    longitude_akhir NUMERIC(10,6),
    jarak_km NUMERIC(10,2),
    waktu_mulai TIMESTAMP,
    waktu_selesai TIMESTAMP,
    durasi_menit INTEGER,
    kecepatan_max_kmh NUMERIC(8,2),
    kecepatan_avg_kmh NUMERIC(8,2),
    pengereman_mendadak BOOLEAN DEFAULT FALSE,
    akselerasi_kasar BOOLEAN DEFAULT FALSE,
    kecepatan_terlampaui BOOLEAN DEFAULT FALSE,
    risk_score INTEGER, -- 0-100 (0=safe, 100=very risky)
    catatan TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT log_perjalanan_chk_dates CHECK (waktu_selesai > waktu_mulai)
);

-- Indexes untuk query yang sering digunakan
CREATE INDEX IF NOT EXISTS idx_log_perjalanan_uuid_user ON warehouse.log_perjalanan_armada(uuid_user);
CREATE INDEX IF NOT EXISTS idx_log_perjalanan_id_order ON warehouse.log_perjalanan_armada(id_order);
CREATE INDEX IF NOT EXISTS idx_log_perjalanan_waktu_mulai ON warehouse.log_perjalanan_armada(waktu_mulai);
CREATE INDEX IF NOT EXISTS idx_log_perjalanan_risk_score ON warehouse.log_perjalanan_armada(risk_score);

-- ============================================================================
-- 4. MASTER DATA TABLE
-- ============================================================================

-- Table: rekening_driver (Bank Account - Driver Readiness)
CREATE TABLE IF NOT EXISTS warehouse.rekening_driver (
    id_rekening UUID PRIMARY KEY,
    uuid_user UUID NOT NULL REFERENCES warehouse.driver(uuid_user) ON DELETE CASCADE,
    nama_bank VARCHAR(100),
    nomor_rekening VARCHAR(50) NOT NULL,
    nama_pemilik_rekening VARCHAR(255),
    status_rekening VARCHAR(50), -- 'AKTIF', 'INACTIVE', 'BLOCKED'
    tipe_rekening VARCHAR(50), -- 'GIRO', 'TABUNGAN', etc
    tanggal_aktif DATE,
    tanggal_nonaktif DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(uuid_user, nomor_rekening)
);

-- ============================================================================
-- 5. CREATE INDEXES FOR COMMON QUERIES
-- ============================================================================

-- Driver Indexes
CREATE INDEX IF NOT EXISTS idx_driver_status ON warehouse.driver(status);
CREATE INDEX IF NOT EXISTS idx_driver_nomor_identitas ON warehouse.driver(nomor_identitas);

-- Armada Indexes
CREATE INDEX IF NOT EXISTS idx_armada_status ON warehouse.armada(status);
CREATE INDEX IF NOT EXISTS idx_armada_nomor_plat ON warehouse.armada(nomor_plat);

-- Driver Armada Indexes
CREATE INDEX IF NOT EXISTS idx_driver_armada_uuid_user ON warehouse.driver_armada(uuid_user);
CREATE INDEX IF NOT EXISTS idx_driver_armada_id_armada ON warehouse.driver_armada(id_armada);
CREATE INDEX IF NOT EXISTS idx_driver_armada_status ON warehouse.driver_armada(status);

-- GPS Device Indexes
CREATE INDEX IF NOT EXISTS idx_perangkat_gps_uuid_user ON warehouse.perangkat_gps_driver(uuid_user);
CREATE INDEX IF NOT EXISTS idx_perangkat_gps_status ON warehouse.perangkat_gps_driver(status);

-- Delivery Order Indexes
CREATE INDEX IF NOT EXISTS idx_delivery_order_id_armada ON warehouse.delivery_order(id_armada);
CREATE INDEX IF NOT EXISTS idx_delivery_order_status ON warehouse.delivery_order(status_pengiriman);
CREATE INDEX IF NOT EXISTS idx_delivery_order_tanggal ON warehouse.delivery_order(tanggal_order);

-- Rating Indexes
CREATE INDEX IF NOT EXISTS idx_rating_id_order ON warehouse.rating(id_order);
CREATE INDEX IF NOT EXISTS idx_rating_uuid_user ON warehouse.rating(uuid_user);
CREATE INDEX IF NOT EXISTS idx_rating_score ON warehouse.rating(rating_score);

-- Rekening Driver Indexes
CREATE INDEX IF NOT EXISTS idx_rekening_driver_uuid_user ON warehouse.rekening_driver(uuid_user);
CREATE INDEX IF NOT EXISTS idx_rekening_driver_status ON warehouse.rekening_driver(status_rekening);

-- ============================================================================
-- 6. VIEWS UNTUK KPI ANALYTICS
-- ============================================================================

-- View: Driver Delivery Performance
CREATE OR REPLACE VIEW warehouse.v_driver_delivery_performance AS
SELECT 
    d.uuid_user,
    d.nama_driver,
    COUNT(DISTINCT do.id_order) as total_deliveries,
    COUNT(DISTINCT CASE WHEN do.status_pengiriman = 'COMPLETED' THEN do.id_order END) as completed_deliveries,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN do.status_pengiriman = 'COMPLETED' THEN do.id_order END) / 
          NULLIF(COUNT(DISTINCT do.id_order), 0), 2) as completion_rate,
    ROUND(AVG(CASE WHEN r.rating_score IS NOT NULL THEN r.rating_score END), 2) as avg_rating,
    COUNT(DISTINCT CASE WHEN do.status_pengiriman = 'COMPLETED' AND 
          do.tanggal_delivery <= do.waktu_delivery_estimate THEN do.id_order END) as on_time_deliveries
FROM warehouse.driver d
LEFT JOIN warehouse.driver_armada da ON d.uuid_user = da.uuid_user AND da.tanggal_selesai IS NULL
LEFT JOIN warehouse.delivery_order do ON da.id_armada = do.id_armada
LEFT JOIN warehouse.rating r ON do.id_order = r.id_order
GROUP BY d.uuid_user, d.nama_driver;

-- View: Driver Safety Performance (Driving Behavior)
CREATE OR REPLACE VIEW warehouse.v_driver_safety_performance AS
SELECT 
    d.uuid_user,
    d.nama_driver,
    COUNT(DISTINCT lpa.id_log) as total_trips,
    COUNT(DISTINCT CASE WHEN lpa.pengereman_mendadak = TRUE THEN lpa.id_log END) as harsh_braking_trips,
    COUNT(DISTINCT CASE WHEN lpa.akselerasi_kasar = TRUE THEN lpa.id_log END) as harsh_acceleration_trips,
    COUNT(DISTINCT CASE WHEN lpa.kecepatan_terlampaui = TRUE THEN lpa.id_log END) as speeding_trips,
    ROUND(AVG(lpa.risk_score), 2) as avg_risk_score,
    MAX(lpa.risk_score) as max_risk_score,
    COUNT(DISTINCT CASE WHEN lpa.risk_score >= 70 THEN lpa.id_log END) as high_risk_trips
FROM warehouse.driver d
LEFT JOIN warehouse.log_perjalanan_armada lpa ON d.uuid_user = lpa.uuid_user
GROUP BY d.uuid_user, d.nama_driver;

-- View: Driver Productivity (Active vs Idle Time)
CREATE OR REPLACE VIEW warehouse.v_driver_productivity AS
SELECT 
    d.uuid_user,
    d.nama_driver,
    SUM(CASE WHEN lad.status_aktivitas = 'ACTIVE' THEN lad.durasi_menit ELSE 0 END) as active_minutes,
    SUM(CASE WHEN lad.status_aktivitas = 'IDLE' THEN lad.durasi_menit ELSE 0 END) as idle_minutes,
    SUM(CASE WHEN lad.status_aktivitas = 'BREAK' THEN lad.durasi_menit ELSE 0 END) as break_minutes,
    SUM(lad.durasi_menit) as total_minutes,
    ROUND(100.0 * SUM(CASE WHEN lad.status_aktivitas = 'ACTIVE' THEN lad.durasi_menit ELSE 0 END) / 
          NULLIF(SUM(lad.durasi_menit), 0), 2) as active_percentage
FROM warehouse.driver d
LEFT JOIN warehouse.log_aktifitas_driver lad ON d.uuid_user = lad.uuid_user
GROUP BY d.uuid_user, d.nama_driver;

-- View: Customer Satisfaction (Rating Distribution)
CREATE OR REPLACE VIEW warehouse.v_customer_satisfaction AS
SELECT 
    d.uuid_user,
    d.nama_driver,
    COUNT(DISTINCT r.id_rating) as total_ratings,
    COUNT(DISTINCT CASE WHEN r.rating_score = 5 THEN r.id_rating END) as five_star,
    COUNT(DISTINCT CASE WHEN r.rating_score = 4 THEN r.id_rating END) as four_star,
    COUNT(DISTINCT CASE WHEN r.rating_score = 3 THEN r.id_rating END) as three_star,
    COUNT(DISTINCT CASE WHEN r.rating_score = 2 THEN r.id_rating END) as two_star,
    COUNT(DISTINCT CASE WHEN r.rating_score = 1 THEN r.id_rating END) as one_star,
    ROUND(AVG(r.rating_score), 2) as avg_rating
FROM warehouse.driver d
LEFT JOIN warehouse.delivery_order do ON do.id_order IN (
    SELECT id_order FROM warehouse.delivery_order WHERE status_pengiriman = 'COMPLETED'
)
LEFT JOIN warehouse.rating r ON do.id_order = r.id_order AND d.uuid_user = r.uuid_user
GROUP BY d.uuid_user, d.nama_driver;

-- View: Driver Readiness (Bank Account Status)
CREATE OR REPLACE VIEW warehouse.v_driver_readiness AS
SELECT 
    d.uuid_user,
    d.nama_driver,
    d.status as driver_status,
    COUNT(DISTINCT rd.id_rekening) as total_rekening,
    COUNT(DISTINCT CASE WHEN rd.status_rekening = 'AKTIF' THEN rd.id_rekening END) as rekening_aktif,
    COUNT(DISTINCT CASE WHEN rd.status_rekening = 'INACTIVE' THEN rd.id_rekening END) as rekening_inactive,
    MAX(rd.updated_at) as last_rekening_update
FROM warehouse.driver d
LEFT JOIN warehouse.rekening_driver rd ON d.uuid_user = rd.uuid_user
GROUP BY d.uuid_user, d.nama_driver, d.status;

-- ============================================================================
-- 7. METADATA TABLE (untuk tracking sync)
-- ============================================================================

CREATE TABLE IF NOT EXISTS warehouse.sync_metadata (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    last_sync_time TIMESTAMP,
    row_count INTEGER,
    status VARCHAR(50),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(table_name)
);

-- ============================================================================
-- GRANT PERMISSIONS (Optional - sesuaikan dengan user yang diperlukan)
-- ============================================================================
-- GRANT USAGE ON SCHEMA warehouse TO warehouse_user;
-- GRANT SELECT ON ALL TABLES IN SCHEMA warehouse TO warehouse_user;
-- GRANT INSERT, UPDATE ON ALL TABLES IN SCHEMA warehouse TO warehouse_etl_user;

COMMIT;
