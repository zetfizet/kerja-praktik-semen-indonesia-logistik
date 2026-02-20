#!/usr/bin/env python3
"""
COMPLETE EXAMPLE: Warehouse → MLflow Flow
==========================================
Show complete flow dari warehouse ke MLflow (NO extra database needed!)
"""

import psycopg2
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

print("=" * 80)
print("📊 COMPLETE FLOW EXAMPLE: Warehouse → Train → MLflow")
print("=" * 80)

# ============================================================================
# STEP 1: Connect to WAREHOUSE (existing database)
# ============================================================================
print("\n[STEP 1] Connect to WAREHOUSE database...")
print("  📍 Location: postgres:5432/warehouse (from container)")
print("  📍 OR: localhost:5433/warehouse (from host)")
print("  💡 This is the ONLY database you need!")

# Try both connection methods (container vs host)
try:
    conn = psycopg2.connect(
        host='postgres',  # Container name (from inside container)
        port=5432,        # Internal port
        database='warehouse',
        user='airflow',
        password='airflow'
    )
    print("  ✓ Connected via postgres:5432 (container)")
except:
    conn = psycopg2.connect(
        host='localhost',
        port=5433,  # External port (from host)
        database='warehouse',
        user='airflow',
        password='airflow'
    )
    print("  ✓ Connected via localhost:5433 (host)")

# ============================================================================
# STEP 2: Get data FROM warehouse (using SQL query)
# ============================================================================
print("\n[STEP 2] Get data FROM warehouse...")
print("  💾 Data stored in: warehouse database (postgres)")
print("  📊 Query: SELECT from tables...")

# For demo: count available tables
cursor = conn.cursor()
cursor.execute("""
    SELECT table_name, 
           (SELECT COUNT(*) FROM information_schema.tables t2 
            WHERE t2.table_name = t1.table_name) as exists
    FROM information_schema.tables t1
    WHERE table_schema = 'public'
    AND table_name IN ('customers', 'orders', 'daftar_user', 'delivery_order')
""")
tables_info = cursor.fetchall()

print("\n  Available tables:")
for table, _ in tables_info:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"    • {table:20} → {count:5} records")

conn.close()
print("\n  ✓ Data retrieved from warehouse!")

# ============================================================================
# STEP 3: Train model (in memory - no database needed)
# ============================================================================
print("\n[STEP 3] Train ML model...")
print("  🧠 Process: Load data → Train → Get metrics")
print("  💾 Storage: Model trained in MEMORY (RAM)")
print("  ❌ NO new database needed!")

# Generate sample data for demo
import numpy as np
np.random.seed(42)

# Simulate customer data
X = pd.DataFrame({
    'total_orders': np.random.randint(1, 50, 100),
    'days_since_last_order': np.random.randint(1, 365, 100),
    'avg_order_value': np.random.uniform(50000, 5000000, 100),
})
y = (X['days_since_last_order'] > 90).astype(int)  # Churn label

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train
model = RandomForestClassifier(n_estimators=50, random_state=42)
model.fit(X_train, y_train)

accuracy = model.score(X_test, y_test)
print(f"  ✓ Model trained! Accuracy: {accuracy:.3f}")

# ============================================================================
# STEP 4: Log results TO MLflow (file system storage)
# ============================================================================
print("\n[STEP 4] Log results TO MLflow...")
print("  📍 Storage: /opt/airflow/mlruns/ (FILE SYSTEM)")
print("  💾 Saves: Metrics + Parameters + Model file")
print("  ❌ NO database involved - just files!")

mlflow.set_experiment("complete_flow_demo")

with mlflow.start_run(run_name="warehouse_to_mlflow_demo"):
    # Log parameters
    mlflow.log_param("model_type", "RandomForest")
    mlflow.log_param("n_estimators", 50)
    mlflow.log_param("data_source", "warehouse")
    mlflow.log_param("training_size", len(X_train))
    
    # Log metrics
    mlflow.log_metric("accuracy", accuracy)
    mlflow.log_metric("train_samples", len(X_train))
    mlflow.log_metric("test_samples", len(X_test))
    
    # Log model
    mlflow.sklearn.log_model(model, "model")
    
    run_id = mlflow.active_run().info.run_id
    
    print(f"\n  ✓ Logged to MLflow!")
    print(f"  ✓ Run ID: {run_id}")
    print(f"\n  📁 Files saved to:")
    print(f"     /opt/airflow/mlruns/.../")
    print(f"     ├── metrics/")
    print(f"     │   ├── accuracy")
    print(f"     │   ├── train_samples")
    print(f"     │   └── test_samples")
    print(f"     ├── params/")
    print(f"     │   ├── model_type")
    print(f"     │   ├── n_estimators")
    print(f"     │   └── data_source")
    print(f"     └── artifacts/")
    print(f"         └── model/")
    print(f"             ├── model.pkl  ← Trained model file")
    print(f"             └── conda.yaml")

# ============================================================================
# STEP 5: View in MLflow UI
# ============================================================================
print("\n[STEP 5] View results in MLflow UI...")
print("  🌐 URL: http://localhost:5000")
print("  👀 View: Experiments → Runs → Metrics → Model")

# ============================================================================
# SUMMARY: What databases are involved?
# ============================================================================
print("\n" + "=" * 80)
print("📊 SUMMARY: Database & Storage Breakdown")
print("=" * 80)

print("\n┌─────────────────────────────────────────────────────────────────────┐")
print("│ DATABASES YANG ADA:                                                 │")
print("├─────────────────────────────────────────────────────────────────────┤")
print("│                                                                     │")
print("│ 1️⃣  PRODUCTION DB (devom.silog.co.id:5432/om)                      │")
print("│    └─ Fungsi: Source data (original)                               │")
print("│    └─ Akses: Read by Airflow DAG                                   │")
print("│                                                                     │")
print("│ 2️⃣  WAREHOUSE DB (localhost:5433/warehouse)                        │")
print("│    └─ Fungsi: Target untuk analytics & ML training                │")
print("│    └─ Akses: Read by Metabase, Python scripts                     │")
print("│    └─ Content: 88 tables synced dari production                   │")
print("│                                                                     │")
print("└─────────────────────────────────────────────────────────────────────┘")

print("\n┌─────────────────────────────────────────────────────────────────────┐")
print("│ MLFLOW STORAGE (BUKAN DATABASE!):                                  │")
print("├─────────────────────────────────────────────────────────────────────┤")
print("│                                                                     │")
print("│ 📁 FILE SYSTEM: /opt/airflow/mlruns/                               │")
print("│    └─ Fungsi: Tracking ML experiments                             │")
print("│    └─ Format: YAML, JSON, PKL files (tidak pakai SQL!)            │")
print("│    └─ Content: Metrics, parameters, models                        │")
print("│    └─ Akses: MLflow UI (localhost:5000)                           │")
print("│                                                                     │")
print("│ ❌ TIDAK PERLU DATABASE BARU!                                       │")
print("│                                                                     │")
print("└─────────────────────────────────────────────────────────────────────┘")

print("\n┌─────────────────────────────────────────────────────────────────────┐")
print("│ FLOW LENGKAP:                                                       │")
print("├─────────────────────────────────────────────────────────────────────┤")
print("│                                                                     │")
print("│  Production DB → Airflow DAG → Warehouse DB                        │")
print("│       ↓                            ↓           ↓                   │")
print("│    (source)                   (Metabase)  (ML scripts)            │")
print("│                                               ↓                    │")
print("│                                      Train model (memory)          │")
print("│                                               ↓                    │")
print("│                                    MLflow files (disk)             │")
print("│                                               ↓                    │")
print("│                                       MLflow UI (view)             │")
print("│                                                                     │")
print("└─────────────────────────────────────────────────────────────────────┘")

print("\n" + "=" * 80)
print("✅ KESIMPULAN:")
print("=" * 80)
print("""
Kamu TIDAK perlu database baru untuk MLflow!

Yang ada:
  ✅ Warehouse DB (localhost:5433) → Untuk data training
  ✅ MLflow files (/opt/airflow/mlruns/) → Untuk tracking experiments
  
Yang TIDAK perlu:
  ❌ Database baru untuk MLflow
  ❌ Setup PostgreSQL lagi
  ❌ Additional storage layer

MLflow pakai FILE SYSTEM, bukan database!
File system sudah cukup untuk:
  - Single user / small team
  - Moderate experiment volume
  - Local development & testing

Optional upgrade ke database backend hanya kalau:
  - Large team (>10 orang)
  - Heavy concurrent access
  - Need centralized tracking server

Untuk sekarang: FILE SYSTEM is PERFECT! ✓
""")

print("=" * 80)
print(f"🎉 DEMO COMPLETE!")
print("=" * 80)
print(f"\n📊 View your experiment:")
print(f"   http://localhost:5000")
print(f"\n📖 Read more:")
print(f"   cat MLFLOW_ARCHITECTURE.md")
print("=" * 80)
