# MLflow Setup Guide - Localhost

## 📊 Overview

MLflow is an open-source platform for managing the machine learning lifecycle, including:
- **Experiment Tracking**: Log parameters, metrics, and artifacts
- **Model Registry**: Manage model versions and transitions
- **Model Serving**: Deploy models via REST API

This setup runs MLflow with PostgreSQL backend for persistent storage of experiments and artifacts.

---

## 🚀 Quick Start

### 1. Install MLflow (if not already installed)

```bash
pip install mlflow
```

### 2. Start MLflow Server

```bash
bash /home/rafiez/airflow-stack/start_mlflow.sh
```

**Expected Output:**
```
✅ MLflow Server Started Successfully!

📊 Access MLflow UI:
   URL: http://localhost:5000

📝 Tracking URI for Python code:
   mlflow.set_tracking_uri('http://localhost:5000')

📂 Artifacts Location:
   /home/rafiez/airflow-stack/mlflow/artifacts
```

### 3. Access MLflow UI

Open your browser: **http://localhost:5000**

### 4. Stop MLflow Server

```bash
bash /home/rafiez/airflow-stack/stop_mlflow.sh
```

---

## 🔧 Configuration

**MLflow Configuration File:**
```
/home/rafiez/airflow-stack/mlflow/mlflow.conf
```

**Key Settings:**
- **Tracking URI**: `http://localhost:5000`
- **Backend Store**: PostgreSQL (warehouse database)
- **Artifact Store**: `/home/rafiez/airflow-stack/mlflow/artifacts`
- **Host**: `0.0.0.0`
- **Port**: `5000`

---

## 💻 Python Integration Examples

### Example 1: Basic Experiment Tracking

```python
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestRegressor
from sklearn.datasets import load_diabetes
from sklearn.model_selection import train_test_split

# Set tracking URI
mlflow.set_tracking_uri("http://localhost:5000")

# Create experiment
mlflow.set_experiment("weather_prediction")

# Load data
X, y = load_diabetes(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Start MLflow run
with mlflow.start_run():
    # Train model
    model = RandomForestRegressor(n_estimators=100, max_depth=10)
    model.fit(X_train, y_train)
    
    # Log parameters
    mlflow.log_param("n_estimators", 100)
    mlflow.log_param("max_depth", 10)
    
    # Log metrics
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    mlflow.log_metric("train_r2", train_score)
    mlflow.log_metric("test_r2", test_score)
    
    # Log model
    mlflow.sklearn.log_model(model, "model")
    
    print(f"✓ Model logged - Train R²: {train_score:.4f}, Test R²: {test_score:.4f}")
```

### Example 2: Experiment with Hyperparameter Tuning

```python
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestRegressor
from sklearn.datasets import load_diabetes
from sklearn.model_selection import train_test_split, cross_val_score

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("rf_hyperparameter_tuning")

X, y = load_diabetes(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Try different hyperparameters
for n_estimators in [50, 100, 200]:
    for max_depth in [5, 10, 20]:
        with mlflow.start_run():
            model = RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth)
            model.fit(X_train, y_train)
            
            mlflow.log_param("n_estimators", n_estimators)
            mlflow.log_param("max_depth", max_depth)
            
            cv_score = cross_val_score(model, X_train, y_train, cv=5).mean()
            test_score = model.score(X_test, y_test)
            
            mlflow.log_metric("cv_score", cv_score)
            mlflow.log_metric("test_score", test_score)
            mlflow.sklearn.log_model(model, "model")
            
            print(f"n_est={n_estimators}, depth={max_depth} → CV: {cv_score:.4f}, Test: {test_score:.4f}")
```

### Example 3: Logging Weather Prediction Metrics

```python
import mlflow
import pandas as pd
from datetime import datetime

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("weather_forecast_evaluation")

# Simulate weather forecast data
actual = [24, 25, 26, 25, 24]  # Actual temperatures
predicted = [23.5, 25.2, 25.8, 24.9, 24.1]  # Predicted temperatures

with mlflow.start_run(run_name=f"forecast_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
    # Calculate metrics
    mae = sum(abs(a - p) for a, p in zip(actual, predicted)) / len(actual)
    rmse = (sum((a - p) ** 2 for a, p in zip(actual, predicted)) / len(actual)) ** 0.5
    
    # Log parameters
    mlflow.log_param("model_type", "BMKG API")
    mlflow.log_param("cities", "Surabaya, Gresik")
    
    # Log metrics
    mlflow.log_metric("MAE", mae)
    mlflow.log_metric("RMSE", rmse)
    
    # Log data as artifact
    df = pd.DataFrame({
        'actual': actual,
        'predicted': predicted
    })
    df.to_csv('/tmp/forecast_comparison.csv', index=False)
    mlflow.log_artifact('/tmp/forecast_comparison.csv')
    
    print(f"✓ Weather forecast logged - MAE: {mae:.4f}, RMSE: {rmse:.4f}")
```

---

## 📝 Integration with Airflow DAGs

### Example: Weather Prediction DAG with MLflow Tracking

Create a file: `/home/rafiez/airflow-stack/dags/weather_prediction_mlflow.py`

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestRegressor
import psycopg2
import pandas as pd

default_args = {
    'owner': 'data_team',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2026, 2, 1),
}

dag = DAG(
    'weather_prediction_mlflow',
    default_args=default_args,
    description='Weather prediction with MLflow tracking',
    schedule='0 12 * * *',  # Daily at 12:00
    catchup=False,
    tags=['weather', 'mlflow', 'prediction'],
)

def fetch_weather_features():
    """Fetch historical weather data for training"""
    conn = psycopg2.connect(
        host='localhost', database='warehouse',
        user='postgres', password='postgres123'
    )
    
    query = """
    SELECT waktu, suhu_celsius, kelembapan, kecepatan_angin
    FROM weather.fact_weather_hourly
    WHERE lokasi = 'Kota Surabaya'
    AND waktu >= NOW() - INTERVAL '30 days'
    ORDER BY waktu
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Save features for next task
    df.to_csv('/tmp/weather_features.csv', index=False)
    print(f"✓ Fetched {len(df)} records")
    return len(df)

def train_weather_model():
    """Train weather prediction model with MLflow tracking"""
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("weather_prediction_daily")
    
    # Load features
    df = pd.read_csv('/tmp/weather_features.csv')
    
    # Prepare data (simple example)
    X = df[['kelembapan', 'kecepatan_angin']].values
    y = df['suhu_celsius'].values
    
    with mlflow.start_run(run_name=f"training_{datetime.now().strftime('%Y%m%d')}"):
        # Train model
        model = RandomForestRegressor(n_estimators=100, max_depth=10)
        model.fit(X, y)
        
        # Calculate metrics
        r2_score = model.score(X, y)
        
        # Log parameters
        mlflow.log_param("model_type", "RandomForest")
        mlflow.log_param("n_estimators", 100)
        mlflow.log_param("max_depth", 10)
        mlflow.log_param("features", ["kelembapan", "kecepatan_angin"])
        
        # Log metrics
        mlflow.log_metric("train_r2", r2_score)
        
        # Log model
        mlflow.sklearn.log_model(model, "weather_model")
        
        print(f"✓ Model trained - R² Score: {r2_score:.4f}")

# Tasks
fetch_task = PythonOperator(
    task_id='fetch_weather_features',
    python_callable=fetch_weather_features,
    dag=dag,
)

train_task = PythonOperator(
    task_id='train_weather_model',
    python_callable=train_weather_model,
    dag=dag,
)

fetch_task >> train_task
```

---

## 📊 MLflow UI Features

### Experiments View
- Browse all experiments
- Compare runs side-by-side
- View run details, metrics, parameters, and artifacts

### Run Details
- **Metrics**: View metric history and trends
- **Parameters**: View logged parameters
- **Artifacts**: Download logged files (models, plots, data)
- **Notes**: Add notes to runs

### Model Registry
- Register models
- Transition model stages (Staging → Production)
- View model versions and metadata

---

## 🔍 Monitoring and Troubleshooting

### Check MLflow Status
```bash
# View logs
tail -f /home/rafiez/airflow-stack/mlflow/logs/mlflow.log

# Check if running
curl http://localhost:5000

# List running processes
lsof -i :5000
```

### Verify Database Connection
```bash
psql -h localhost -U postgres -d mlflow -c "SELECT 1"
```

### Check Artifacts
```bash
ls -lah /home/rafiez/airflow-stack/mlflow/artifacts/
```

### Reset MLflow Database (caution: deletes all experiments)
```bash
# Stop MLflow
bash /home/rafiez/airflow-stack/stop_mlflow.sh

# Drop database
psql -h localhost -U postgres -c "DROP DATABASE mlflow"

# Start MLflow (creates new database)
bash /home/rafiez/airflow-stack/start_mlflow.sh
```

---

## 📚 Useful Commands

### List all experiments
```bash
mlflow experiments list
```

### View run details
```bash
mlflow runs describe --experiment-id <experiment_id> --run-id <run_id>
```

### Download artifacts
```bash
mlflow artifacts download --artifact-path <path> --run-id <run_id> --dst-path /local/path
```

### Create experiment via CLI
```bash
mlflow experiments create --experiment-name "my_experiment"
```

---

## 🎯 Next Steps

1. ✅ MLflow server running on `localhost:5000`
2. ✅ PostgreSQL backend configured
3. ⏳ Create your first experiment in Python
4. ⏳ Integrate with Airflow DAGs for automated tracking
5. ⏳ Monitor model performance over time
6. ⏳ Use Model Registry for production deployments

---

## 📞 Resources

- **MLflow Official Docs**: https://mlflow.org/docs/latest/
- **Tracking Server Docs**: https://mlflow.org/docs/latest/tracking-servers.html
- **Python API**: https://mlflow.org/docs/latest/python_api/mlflow.html
