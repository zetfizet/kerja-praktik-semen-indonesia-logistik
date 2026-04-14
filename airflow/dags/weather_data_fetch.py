"""
Weather Data Fetch DAG
Fetches BMKG weather forecasts, writes to warehouse, verifies freshness, and cleans old rows.
"""

from datetime import datetime, timedelta
import os

from airflow import DAG
from airflow.operators.python import PythonOperator


def get_warehouse_db_config():
    """Read warehouse DB config from env with defaults for this Podman setup."""
    return {
        "host": os.getenv("WAREHOUSE_DB_HOST", "host.docker.internal"),
        "port": int(os.getenv("WAREHOUSE_DB_PORT", "5433")),
        "database": os.getenv("WAREHOUSE_DB_NAME", "warehouse"),
        "user": os.getenv("WAREHOUSE_DB_USER", "postgres"),
        "password": os.getenv("WAREHOUSE_DB_PASSWORD", "postgres123"),
    }


def fetch_weather_data():
    import requests
    import psycopg2

    db_config = get_warehouse_db_config()
    bmkg_api_base = "https://api.bmkg.go.id/publik/prakiraan-cuaca"

    locations = [
        {"adm4": "35.78.21.1004", "location_name": "Lokasi 1"},
        {"adm4": "35.25.14.1010", "location_name": "Lokasi 2"},
    ]

    def create_table_if_needed(cursor):
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS public.fact_weather_hourly (
                id SERIAL PRIMARY KEY,
                adm4 VARCHAR(50) NOT NULL,
                lokasi VARCHAR(255),
                desa VARCHAR(255),
                kecamatan VARCHAR(255),
                kabupaten VARCHAR(255),
                provinsi VARCHAR(255),
                waktu TIMESTAMP NOT NULL,
                cuaca VARCHAR(255),
                suhu_celsius FLOAT,
                kelembapan INT,
                arah_angin VARCHAR(50),
                kecepatan_angin FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_age_minutes DOUBLE PRECISION,
                freshness_status VARCHAR(20),
                UNIQUE(adm4, waktu)
            )
            """
        )

    def parse_records(api_data, location_name):
        records = []
        lokasi = api_data.get("lokasi", {})

        adm4 = lokasi.get("adm4")
        nama_lokasi = lokasi.get("kotkab", location_name)
        desa = lokasi.get("desa", "")
        kecamatan = lokasi.get("kecamatan", "")
        kabupaten = lokasi.get("kotkab", "")
        provinsi = lokasi.get("provinsi", "")

        for data_item in api_data.get("data", []):
            for time_group in data_item.get("cuaca", []):
                if not isinstance(time_group, list):
                    continue
                for weather_item in time_group:
                    records.append(
                        {
                            "adm4": adm4,
                            "lokasi": nama_lokasi,
                            "desa": desa,
                            "kecamatan": kecamatan,
                            "kabupaten": kabupaten,
                            "provinsi": provinsi,
                            "waktu": weather_item.get("datetime"),
                            "cuaca": weather_item.get("weather_desc"),
                            "suhu_celsius": weather_item.get("t"),
                            "kelembapan": weather_item.get("hu"),
                            "arah_angin": weather_item.get("wd"),
                            "kecepatan_angin": weather_item.get("ws"),
                        }
                    )
        return records

    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SET TIME ZONE 'Asia/Jakarta'")

    create_table_if_needed(cursor)
    conn.commit()

    inserted = 0
    updated = 0

    for location in locations:
        url = f"{bmkg_api_base}?adm4={location['adm4']}"
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        api_data = response.json()

        parsed = parse_records(api_data, location["location_name"])
        print(f"Parsed {len(parsed)} records for ADM4 {location['adm4']}")

        for row in parsed:
            if not row["adm4"] or not row["waktu"]:
                continue

            cursor.execute(
                """
                INSERT INTO public.fact_weather_hourly (
                    adm4, lokasi, desa, kecamatan, kabupaten, provinsi,
                    waktu, cuaca, suhu_celsius, kelembapan, arah_angin, kecepatan_angin,
                    created_at, last_updated
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (adm4, waktu) DO UPDATE SET
                    lokasi = EXCLUDED.lokasi,
                    desa = EXCLUDED.desa,
                    kecamatan = EXCLUDED.kecamatan,
                    kabupaten = EXCLUDED.kabupaten,
                    provinsi = EXCLUDED.provinsi,
                    cuaca = EXCLUDED.cuaca,
                    suhu_celsius = EXCLUDED.suhu_celsius,
                    kelembapan = EXCLUDED.kelembapan,
                    arah_angin = EXCLUDED.arah_angin,
                    kecepatan_angin = EXCLUDED.kecepatan_angin,
                    last_updated = NOW()
                RETURNING (xmax = 0) AS inserted_flag
                """,
                (
                    row["adm4"],
                    row["lokasi"],
                    row["desa"],
                    row["kecamatan"],
                    row["kabupaten"],
                    row["provinsi"],
                    row["waktu"],
                    row["cuaca"],
                    row["suhu_celsius"],
                    row["kelembapan"],
                    row["arah_angin"],
                    row["kecepatan_angin"],
                ),
            )
            was_inserted = cursor.fetchone()[0]
            if was_inserted:
                inserted += 1
            else:
                updated += 1

    conn.commit()
    cursor.close()
    conn.close()

    total = inserted + updated
    print(f"Inserted: {inserted}, Updated: {updated}, Total affected: {total}")
    if total == 0:
        raise RuntimeError("No weather rows were inserted/updated")


def verify_weather_data():
    import psycopg2

    db_config = get_warehouse_db_config()
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SET TIME ZONE 'Asia/Jakarta'")

    cursor.execute(
        """
        SELECT
            COUNT(*) AS total_rows,
            MAX(created_at) AS latest_created_at,
            MAX(last_updated) AS latest_updated_at,
            MAX(waktu) AS latest_forecast_time
        FROM public.fact_weather_hourly
        """
    )
    total_rows, latest_created_at, latest_updated_at, latest_forecast_time = cursor.fetchone()

    print("Verification result:")
    print(f"Total rows: {total_rows}")
    print(f"Latest created_at: {latest_created_at}")
    print(f"Latest last_updated: {latest_updated_at}")
    print(f"Latest forecast waktu: {latest_forecast_time}")

    if total_rows == 0:
        raise RuntimeError("fact_weather_hourly is empty after fetch")

    cursor.close()
    conn.close()


def update_freshness_metrics():
    import psycopg2

    db_config = get_warehouse_db_config()
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SET TIME ZONE 'Asia/Jakarta'")

    cursor.execute(
        """
        UPDATE public.fact_weather_hourly
        SET
            data_age_minutes = EXTRACT(EPOCH FROM (NOW() - COALESCE(last_updated, created_at))) / 60.0,
            freshness_status = CASE
                WHEN EXTRACT(EPOCH FROM (NOW() - COALESCE(last_updated, created_at))) / 60.0 <= 60 THEN 'FRESH'
                WHEN EXTRACT(EPOCH FROM (NOW() - COALESCE(last_updated, created_at))) / 60.0 <= 180 THEN 'WARNING'
                ELSE 'STALE'
            END
        WHERE created_at >= NOW() - INTERVAL '2 days'
        """
    )
    touched = cursor.rowcount
    conn.commit()

    print(f"Freshness updated for {touched} rows")

    cursor.close()
    conn.close()


def cleanup_old_weather_data():
    import psycopg2

    db_config = get_warehouse_db_config()
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SET TIME ZONE 'Asia/Jakarta'")

    cursor.execute(
        """
        DELETE FROM public.fact_weather_hourly
        WHERE created_at < NOW() - INTERVAL '30 days'
        """
    )
    deleted = cursor.rowcount
    conn.commit()

    print(f"Cleanup deleted {deleted} rows older than 30 days")

    cursor.close()
    conn.close()


default_args = {
    "owner": "data_team",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2026, 1, 21),
}


dag = DAG(
    "weather_data_fetch",
    default_args=default_args,
    description="Fetch weather data from BMKG API every hour",
    schedule="0 * * * *",
    catchup=False,
    tags=["weather", "bmkg", "api", "realtime", "warehouse"],
)

fetch_weather = PythonOperator(
    task_id="fetch_bmkg_weather",
    python_callable=fetch_weather_data,
    dag=dag,
)

verify_weather = PythonOperator(
    task_id="verify_weather_data",
    python_callable=verify_weather_data,
    dag=dag,
)

freshness_check = PythonOperator(
    task_id="update_freshness_metrics",
    python_callable=update_freshness_metrics,
    dag=dag,
)

cleanup_weather = PythonOperator(
    task_id="cleanup_old_weather_data",
    python_callable=cleanup_old_weather_data,
    dag=dag,
)

fetch_weather >> verify_weather >> freshness_check >> cleanup_weather
