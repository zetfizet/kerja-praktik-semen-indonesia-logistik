#!/usr/bin/env python3
"""
Standalone script to fetch weather data and log to MLflow
This demonstrates MLflow integration without Airflow
"""

import mlflow
import json
import time
from datetime import datetime
import requests
import psycopg2
from pytz import timezone

# MLflow Configuration
MLFLOW_TRACKING_URI = "http://localhost:5000"
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
MLFLOW_EXPERIMENT_NAME = "weather_data_fetch"

# Set experiment
try:
    mlflow.create_experiment(MLFLOW_EXPERIMENT_NAME)
except:
    pass

mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

# Jakarta timezone
jakarta_tz = timezone('Asia/Jakarta')

# BMKG API Configuration
BMKG_API_BASE = "https://api.bmkg.go.id/publik/prakiraan-cuaca"

LOCATIONS = [
    {
        'adm4': '35.78.21.1004',
        'location_name': 'Lokasi 1',
    },
    {
        'adm4': '35.25.14.1010',
        'location_name': 'Lokasi 2',
    }
]

# PostgreSQL Connection
DB_CONFIG = {
    'host': 'localhost',
    'database': 'warehouse',
    'user': 'postgres',
    'password': 'postgres123',
}

def fetch_weather_from_bmkg(adm4):
    """Fetch weather data from BMKG API"""
    try:
        url = f"{BMKG_API_BASE}?adm4={adm4}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching from BMKG API: {e}")
        return None

def main():
    """Main script - fetch weather and log to MLflow"""
    
    print("\n" + "=" * 60)
    print("🌦️  Fetching BMKG Weather Data with MLflow Tracking")
    print("=" * 60)
    
    # Start MLflow run
    run = mlflow.start_run(run_name=f"weather_fetch_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    try:
        # Log parameters
        mlflow.log_param("num_locations", len(LOCATIONS))
        mlflow.log_param("api_base", BMKG_API_BASE)
        mlflow.log_param("locations", json.dumps([l['adm4'] for l in LOCATIONS]))
        mlflow.log_param("executor", "standalone_script")
        
        start_time = time.time()
        
        total_records = 0
        location_results = {}
        total_forecasts = 0
        
        # Fetch weather for each location
        for location in LOCATIONS:
            print(f"\n📍 Fetching weather for {location['location_name']} (ADM4: {location['adm4']})")
            
            # Fetch from API
            api_data = fetch_weather_from_bmkg(location['adm4'])
            
            if not api_data:
                print(f"⚠️ Skipping - no data")
                location_results[location['adm4']] = {'status': 'FAILED', 'records': 0}
                continue
            
            # Parse data
            if 'data' in api_data and api_data['data']:
                forecast_count = 0
                for data_item in api_data['data']:
                    cuaca_array = data_item.get('cuaca', [])
                    for time_group in cuaca_array:
                        if isinstance(time_group, list):
                            forecast_count += len(time_group)
                
                print(f"   ✓ Parsed {forecast_count} weather forecasts")
                location_results[location['adm4']] = {'status': 'SUCCESS', 'records': forecast_count}
                total_forecasts += forecast_count
            else:
                print(f"⚠️ No forecasts in data")
                location_results[location['adm4']] = {'status': 'FAILED', 'records': 0}
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        print("\n" + "=" * 60)
        print(f"✓ Total forecasts fetched: {total_forecasts}")
        print(f"✓ Execution time: {execution_time:.2f}s")
        print("=" * 60)
        
        # Log metrics to MLflow
        mlflow.log_metric("total_forecasts_fetched", total_forecasts)
        mlflow.log_metric("execution_time_seconds", execution_time)
        mlflow.log_metric("successful_locations", sum(1 for v in location_results.values() if v['status'] == 'SUCCESS'))
        mlflow.log_metric("failed_locations", sum(1 for v in location_results.values() if v['status'] == 'FAILED'))
        
        if execution_time > 0:
            mlflow.log_metric("forecasts_per_second", total_forecasts / execution_time)
        
        # Log location-specific metrics
        for location_code, result in location_results.items():
            mlflow.log_metric(f"records_{location_code}", result['records'])
        
        # Log artifacts - save summary JSON
        summary = {
            'timestamp': datetime.now(jakarta_tz).isoformat(),
            'total_forecasts': total_forecasts,
            'execution_time_seconds': execution_time,
            'locations': location_results,
            'mlflow_tracking_uri': MLFLOW_TRACKING_URI
        }
        
        with open('/tmp/weather_fetch_summary.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        mlflow.log_artifact('/tmp/weather_fetch_summary.json', 'summary')
        
        # Log detailed metrics
        metrics_data = {
            'FRESH_data': total_forecasts,
            'API_calls_successful': sum(1 for v in location_results.values() if v['status'] == 'SUCCESS'),
            'Data_quality_score': (sum(1 for v in location_results.values() if v['status'] == 'SUCCESS') / len(LOCATIONS) * 100) if LOCATIONS else 0,
        }
        
        with open('/tmp/weather_metrics.json', 'w') as f:
            json.dump(metrics_data, f, indent=2)
        
        mlflow.log_artifact('/tmp/weather_metrics.json', 'metrics')
        
        print("\n✅ MLflow run completed successfully!")
        print(f"   Run ID: {run.info.run_id}")
        print(f"   View at: {MLFLOW_TRACKING_URI}")
        print("\n📊 Metrics logged:")
        print(f"   - Total forecasts: {total_forecasts}")
        print(f"   - Execution time: {execution_time:.2f}s")
        print(f"   - Successful locations: {sum(1 for v in location_results.values() if v['status'] == 'SUCCESS')}/{len(LOCATIONS)}")
        
        mlflow.end_run()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        mlflow.log_param("error", str(e))
        mlflow.end_run(status='FAILED')
        raise

if __name__ == "__main__":
    main()
