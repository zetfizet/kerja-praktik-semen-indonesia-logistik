-- Script untuk membuat sample OLTP tables (untuk testing)
-- Jalankan ini di PostgreSQL jika belum ada data

-- Tabel OLTP: driver_armada
CREATE TABLE IF NOT EXISTS public.driver_armada (
    id SERIAL PRIMARY KEY,
    uuid_user UUID UNIQUE NOT NULL,
    nama_driver VARCHAR(255) NOT NULL,
    tipe_armada VARCHAR(100),
    created_date DATE DEFAULT CURRENT_DATE
);

-- Tabel OLTP: rating
CREATE TABLE IF NOT EXISTS public.rating (
    id SERIAL PRIMARY KEY,
    uuid_user UUID NOT NULL,
    rating_value DECIMAL(3, 2) CHECK (rating_value >= 0 AND rating_value <= 5),
    created_date DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY (uuid_user) REFERENCES public.driver_armada(uuid_user)
);

-- Tabel OLTP: orders
CREATE TABLE IF NOT EXISTS public.orders (
    order_id SERIAL PRIMARY KEY,
    driver_uuid UUID NOT NULL,
    order_date DATE DEFAULT CURRENT_DATE,
    order_amount DECIMAL(10, 2),
    FOREIGN KEY (driver_uuid) REFERENCES public.driver_armada(uuid_user)
);

-- Tabel OLTP: perangkat_gps_driver
CREATE TABLE IF NOT EXISTS public.perangkat_gps_driver (
    gps_id SERIAL PRIMARY KEY,
    uuid_user UUID NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (uuid_user) REFERENCES public.driver_armada(uuid_user)
);

-- Tabel OLTP: rekening_driver
CREATE TABLE IF NOT EXISTS public.rekening_driver (
    id SERIAL PRIMARY KEY,
    uuid_user UUID UNIQUE NOT NULL,
    status VARCHAR(50),
    FOREIGN KEY (uuid_user) REFERENCES public.driver_armada(uuid_user)
);