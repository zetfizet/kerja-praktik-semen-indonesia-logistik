#!/usr/bin/env python3
"""
Basic MLflow Test - No database required
==========================================
Test MLflow functionality dengan synthetic data.
"""

import numpy as np
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score
import warnings
warnings.filterwarnings('ignore')


def test_mlflow():
    """Test basic MLflow functionality"""
    
    print("=" * 70)
    print("🧪 MLflow Basic Test - Synthetic Data")
    print("=" * 70)
    
    # Step 1: Generate synthetic data
    print("\n[1/4] Generating synthetic data...")
    np.random.seed(42)
    
    # Generate 1000 customers
    n_customers = 1000
    data = {
        'total_orders': np.random.randint(1, 50, n_customers),
        'days_since_last_order': np.random.randint(1, 365, n_customers),
        'avg_order_value': np.random.uniform(50000, 5000000, n_customers),
        'account_age_days': np.random.randint(30, 1000, n_customers),
    }
    df = pd.DataFrame(data)
    
    # Create target: churned = no order in last 90 days
    df['is_churned'] = (df['days_since_last_order'] > 90).astype(int)
    
    print(f"   ✓ Generated {len(df)} synthetic customer records")
    print(f"   ✓ Features: {list(data.keys())}")
    print(f"   ✓ Churn rate: {df['is_churned'].mean():.1%}")
    
    # Step 2: Prepare training data
    print("\n[2/4] Preparing training data...")
    
    features = ['total_orders', 'days_since_last_order', 'avg_order_value', 'account_age_days']
    X = df[features]
    y = df['is_churned']
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"   ✓ Training set: {len(X_train)} records")
    print(f"   ✓ Test set: {len(X_test)} records")
    
    # Step 3: Train with MLflow
    print("\n[3/4] Training model with MLflow...")
    
    # Set experiment
    mlflow.set_experiment("test_basic_functionality")
    
    with mlflow.start_run(run_name="synthetic_data_test"):
        # Log parameters
        mlflow.log_param("data_type", "synthetic")
        mlflow.log_param("n_records", len(df))
        mlflow.log_param("model_type", "RandomForest")
        mlflow.log_param("n_estimators", 100)
        mlflow.log_param("max_depth", 10)
        
        # Train
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train, y_train)
        
        # Predict & evaluate
        y_pred = model.predict(X_test)
        
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        
        # Log metrics
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("precision", precision)
        mlflow.log_metric("recall", recall)
        mlflow.log_metric("training_records", len(X_train))
        mlflow.log_metric("test_records", len(X_test))
        
        # Log model
        mlflow.sklearn.log_model(model, "model")
        
        # Get run info
        run_id = mlflow.active_run().info.run_id
        
        print(f"   ✓ Model trained!")
        print(f"   ✓ Accuracy: {accuracy:.3f}")
        print(f"   ✓ Precision: {precision:.3f}")
        print(f"   ✓ Recall: {recall:.3f}")
        print(f"   ✓ MLflow Run ID: {run_id}")
    
    # Step 4: Verify MLflow
    print("\n[4/4] Verifying MLflow...")
    
    # Check experiment
    experiment = mlflow.get_experiment_by_name("test_basic_functionality")
    if experiment:
        print(f"   ✓ Experiment created: {experiment.name}")
        print(f"   ✓ Experiment ID: {experiment.experiment_id}")
        print(f"   ✓ Artifact location: {experiment.artifact_location}")
    else:
        print("   ✗ Experiment not found!")
        return False
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ MLFLOW TEST PASSED!")
    print("=" * 70)
    print("\nWhat was tested:")
    print("  ✓ Generate synthetic training data")
    print("  ✓ Train Random Forest model")
    print("  ✓ Log parameters to MLflow")
    print("  ✓ Log metrics to MLflow")
    print("  ✓ Save model artifact to MLflow")
    print("  ✓ Retrieve experiment metadata")
    
    print("\n🎉 MLflow is working correctly!")
    
    print("\nNext steps:")
    print("  1. Start MLflow UI:")
    print("     mlflow ui --host 0.0.0.0 --port 5000")
    print("\n  2. Open browser:")
    print("     http://localhost:5000")
    print("\n  3. View your experiment:")
    print(f"     - Experiment: test_basic_functionality")
    print(f"     - Run ID: {run_id}")
    print("     - Check metrics, parameters & model artifact")
    
    print("\n  4. Connect to warehouse:")
    print("     - Fix: Port 5433 ✓")
    print("     - Wait for data sync or use real data")
    print("     - Run: python3 simple_mlflow_demo.py")
    
    print("\n" + "=" * 70)
    return True


if __name__ == "__main__":
    import sys
    success = test_mlflow()
    sys.exit(0 if success else 1)
