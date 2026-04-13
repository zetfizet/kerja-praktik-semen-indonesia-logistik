"""
Routing Enrichment DAG
Fetches weather locations, calculates pairwise routes via GraphHopper,
and upserts metrics into public.fact_route_metrics.
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging
import os
import psycopg2
import re
import requests
import sys
import time

# Add scripts path - works in both local and container
script_paths = [
    "/opt/airflow/dags",
    "/opt/airflow/scripts",
    "/home/xfrih/project/airflow/scripts",
    "/home/xfrih/project/airflow/dags",
]
for path in script_paths:
    if os.path.exists(path):
        sys.path.insert(0, path)
        break

from utils.graphhopper_client import GraphHopperClient

logger = logging.getLogger(__name__)


default_args = {
    "owner": "data_team",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2026, 4, 1),
}


dag = DAG(
    "routing_enrichment",
    default_args=default_args,
    schedule="30 2 * * *",
    catchup=False,
    tags=["routing", "graphhopper", "weather", "analytics"],
)

DB_CONFIG = {
    "host": "postgres",
    "database": "warehouse",
    "user": "airflow",
    "password": "airflow",
    "port": 5432,
}


def _ensure_fact_route_metrics_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS public.fact_route_metrics (
            id SERIAL PRIMARY KEY,
            origin_name VARCHAR(255),
            origin_lat DOUBLE PRECISION,
            origin_lon DOUBLE PRECISION,
            destination_name VARCHAR(255),
            destination_lat DOUBLE PRECISION,
            destination_lon DOUBLE PRECISION,
            distance_km DOUBLE PRECISION,
            duration_min DOUBLE PRECISION,
            vehicle_type VARCHAR(50) DEFAULT 'car',
            computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(origin_name, destination_name)
        )
        """
    )
    cursor.execute(
        """
        ALTER TABLE public.fact_route_metrics
        ADD COLUMN IF NOT EXISTS computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """
    )


def _get_order_tms_columns(cursor) -> set[str]:
    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'order_tms'
        """
    )
    return {row[0] for row in cursor.fetchall()}


def _extract_queries_from_address(address: str) -> list[str]:
    if not address:
        return []

    normalized = " ".join(address.strip().split())
    parts = [part.strip() for part in normalized.split(",") if part.strip()]

    # Prefer city-level queries first; street names like "Jl. Sudirman" are highly ambiguous.
    queries = []
    if parts:
        queries.append(f"{parts[-1]}, Indonesia")
        queries.append(parts[-1])
    if len(parts) >= 2:
        queries.append(f"{parts[-2]}, {parts[-1]}, Indonesia")

    queries.append(normalized)

    # Remove street number noise for broad matching (e.g., "No. 10").
    reduced = re.sub(r"\bno\.?\s*\d+[a-zA-Z]?\b", "", normalized, flags=re.IGNORECASE)
    reduced = " ".join(reduced.split())
    if reduced and reduced not in queries:
        queries.append(reduced)

    deduped = []
    for q in queries:
        if q and q not in deduped:
            deduped.append(q)
    return deduped


def _resolve_from_weather_lookup(address: str, weather_lookup: dict[str, tuple[float, float]]) -> tuple[float, float] | None:
    if not address:
        return None

    address_lower = address.lower()
    for lokasi, coords in weather_lookup.items():
        if lokasi and lokasi in address_lower:
            return coords
    return None


def _geocode_address(address: str, cache: dict[str, tuple[float, float] | None]) -> tuple[float, float] | None:
    if not address:
        return None

    if address in cache:
        return cache[address]

    session = requests.Session()
    session.headers.update({"User-Agent": "airflow-routing-enrichment/1.0"})

    for query in _extract_queries_from_address(address):
        try:
            response = session.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": query, "format": "json", "limit": 1},
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()

            if payload:
                lat = float(payload[0]["lat"])
                lon = float(payload[0]["lon"])
                cache[address] = (lat, lon)
                return cache[address]

            # Respect public endpoint when retrying alternate query.
            time.sleep(0.3)
        except Exception:
            continue

    cache[address] = None
    return None


def fetch_order_routes() -> list[dict]:
    """
    Fetch real route candidates from order_tms.

    Priority:
    1. Direct coordinate columns in order_tms (if present)
    2. Resolve coordinates from alamat_asal/alamat_tujuan using weather locations
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        order_columns = _get_order_tms_columns(cursor)
        coordinate_candidates = [
            ("pickup_lat", "pickup_lon", "drop_lat", "drop_lon"),
            ("origin_lat", "origin_lon", "destination_lat", "destination_lon"),
            ("asal_lat", "asal_lon", "tujuan_lat", "tujuan_lon"),
            ("from_lat", "from_lon", "to_lat", "to_lon"),
            ("latitude_asal", "longitude_asal", "latitude_tujuan", "longitude_tujuan"),
        ]

        selected = next(
            (
                candidate
                for candidate in coordinate_candidates
                if all(col in order_columns for col in candidate)
            ),
            None,
        )

        routes = []
        geocode_cache: dict[str, tuple[float, float] | None] = {}
        if selected:
            pickup_lat_col, pickup_lon_col, drop_lat_col, drop_lon_col = selected
            cursor.execute(
                f"""
                SELECT
                    id_order,
                    COALESCE(alamat_asal, 'order_' || id_order || '_origin') AS origin_name,
                    {pickup_lat_col}::double precision AS origin_lat,
                    {pickup_lon_col}::double precision AS origin_lon,
                    COALESCE(alamat_tujuan, 'order_' || id_order || '_dest') AS destination_name,
                    {drop_lat_col}::double precision AS destination_lat,
                    {drop_lon_col}::double precision AS destination_lon
                FROM public.order_tms
                WHERE {pickup_lat_col} IS NOT NULL
                  AND {pickup_lon_col} IS NOT NULL
                  AND {drop_lat_col} IS NOT NULL
                  AND {drop_lon_col} IS NOT NULL
                  AND deleted_at IS NULL
                ORDER BY dibuat_pada DESC NULLS LAST
                LIMIT 50
                """
            )
            rows = cursor.fetchall()
            routes = [
                {
                    "order_id": row[0],
                    "origin_name": row[1],
                    "origin_lat": float(row[2]),
                    "origin_lon": float(row[3]),
                    "destination_name": row[4],
                    "destination_lat": float(row[5]),
                    "destination_lon": float(row[6]),
                }
                for row in rows
            ]
            logger.info(
                "Fetched %s routes from order_tms direct coordinates (%s)",
                len(routes),
                ", ".join(selected),
            )
        else:
            cursor.execute(
                """
                SELECT DISTINCT ON (lokasi)
                    LOWER(lokasi) AS lokasi_key,
                    latitude::double precision,
                    longitude::double precision
                FROM public.fact_weather_hourly
                WHERE lokasi IS NOT NULL
                  AND latitude IS NOT NULL
                  AND longitude IS NOT NULL
                ORDER BY lokasi, waktu DESC NULLS LAST
                """
            )
            weather_lookup = {
                row[0]: (float(row[1]), float(row[2]))
                for row in cursor.fetchall()
                if row[0]
            }

            cursor.execute(
                """
                SELECT
                    o.id_order,
                    COALESCE(o.alamat_asal, 'order_' || o.id_order || '_origin') AS origin_name,
                    COALESCE(o.alamat_tujuan, 'order_' || o.id_order || '_dest') AS destination_name,
                    o.alamat_asal,
                    o.alamat_tujuan
                FROM public.order_tms o
                WHERE o.deleted_at IS NULL
                ORDER BY o.dibuat_pada DESC NULLS LAST
                LIMIT 50
                """
            )

            rows = cursor.fetchall()

            for row in rows:
                order_id, origin_name, destination_name, origin_address, destination_address = row

                origin_coords = _resolve_from_weather_lookup(origin_address or origin_name, weather_lookup)
                destination_coords = _resolve_from_weather_lookup(destination_address or destination_name, weather_lookup)

                if not origin_coords:
                    origin_coords = _geocode_address(origin_address or origin_name, geocode_cache)
                if not destination_coords:
                    destination_coords = _geocode_address(destination_address or destination_name, geocode_cache)

                if not origin_coords or not destination_coords:
                    continue

                routes.append(
                    {
                        "order_id": order_id,
                        "origin_name": origin_name,
                        "origin_lat": float(origin_coords[0]),
                        "origin_lon": float(origin_coords[1]),
                        "destination_name": destination_name,
                        "destination_lat": float(destination_coords[0]),
                        "destination_lon": float(destination_coords[1]),
                    }
                )

            logger.info(
                "Fetched %s routes from order_tms via address/geocoding resolution",
                len(routes),
            )

        if not routes:
            logger.warning("No valid routes found from order_tms")

        return routes
    finally:
        cursor.close()
        conn.close()


def call_graphhopper(**context) -> list[dict]:
    """Calculate route metrics for each real order route candidate."""
    ti = context["ti"]
    routes = ti.xcom_pull(task_ids="fetch_order_routes") or []

    if not routes:
        logger.warning("No routes available to compute")
        return []

    client = GraphHopperClient()
    route_metrics = []

    for row in routes:
        origin = {
            "name": row["origin_name"],
            "lat": row["origin_lat"],
            "lon": row["origin_lon"],
        }
        destination = {
            "name": row["destination_name"],
            "lat": row["destination_lat"],
            "lon": row["destination_lon"],
        }

        try:
            route = client.get_route(
                start=(origin["lat"], origin["lon"]),
                end=(destination["lat"], destination["lon"]),
                vehicle="car",
                calc_points=False,
            )

            metric = {
                "origin_name": origin["name"],
                "origin_lat": origin["lat"],
                "origin_lon": origin["lon"],
                "destination_name": destination["name"],
                "destination_lat": destination["lat"],
                "destination_lon": destination["lon"],
                "distance_km": route["distance_km"],
                "duration_min": route["time_minutes"],
                "vehicle_type": "car",
            }
            route_metrics.append(metric)

            logger.info(
                "Route computed %s -> %s (%.2f km, %.1f min)",
                origin["name"],
                destination["name"],
                metric["distance_km"],
                metric["duration_min"],
            )
        except Exception as exc:
            logger.exception(
                "Failed route %s -> %s: %s",
                origin["name"],
                destination["name"],
                exc,
            )

    return route_metrics


def upsert_fact_route_metrics(**context):
    """Upsert computed route metrics into warehouse table."""
    ti = context["ti"]
    route_metrics = ti.xcom_pull(task_ids="call_graphhopper") or []

    if not route_metrics:
        logger.warning("No route metrics to upsert")
        return

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        _ensure_fact_route_metrics_table(cursor)

        upsert_sql = """
            INSERT INTO public.fact_route_metrics (
                origin_name, origin_lat, origin_lon,
                destination_name, destination_lat, destination_lon,
                distance_km, duration_min, vehicle_type, computed_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (origin_name, destination_name)
            DO UPDATE SET
                origin_lat = EXCLUDED.origin_lat,
                origin_lon = EXCLUDED.origin_lon,
                destination_lat = EXCLUDED.destination_lat,
                destination_lon = EXCLUDED.destination_lon,
                distance_km = EXCLUDED.distance_km,
                duration_min = EXCLUDED.duration_min,
                vehicle_type = EXCLUDED.vehicle_type,
                computed_at = NOW(),
                created_at = NOW()
        """

        for metric in route_metrics:
            cursor.execute(
                upsert_sql,
                (
                    metric["origin_name"],
                    metric["origin_lat"],
                    metric["origin_lon"],
                    metric["destination_name"],
                    metric["destination_lat"],
                    metric["destination_lon"],
                    metric["distance_km"],
                    metric["duration_min"],
                    metric["vehicle_type"],
                ),
            )

        conn.commit()
        logger.info("Upserted %s route metrics", len(route_metrics))
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


fetch_order_routes_task = PythonOperator(
    task_id="fetch_order_routes",
    python_callable=fetch_order_routes,
    dag=dag,
)

call_graphhopper_task = PythonOperator(
    task_id="call_graphhopper",
    python_callable=call_graphhopper,
    dag=dag,
)

upsert_route_metrics_task = PythonOperator(
    task_id="upsert_fact_route_metrics",
    python_callable=upsert_fact_route_metrics,
    dag=dag,
)

fetch_order_routes_task >> call_graphhopper_task >> upsert_route_metrics_task
