# Airflow ELT Pipeline

Data pipeline menggunakan Airflow untuk sync data dari source database ke warehouse PostgreSQL, dengan transformasi daily aggregations.

## Architecture

```
Source DB (SQL Server/MySQL)
    ↓
[warehouse_sync_optimized] @ 02:00 AM → public.* (88 tables, raw data)
    ↓
[warehouse_transform_simple] @ 03:00 AM → analytics.* (5 aggregated tables)
    ↓
Metabase Dashboard (query analytics.*)
```

## Setup

### 1. Prerequisites
- Docker/Podman installed
- PostgreSQL 16
- Python 3.13+

### 2. Configuration

Copy environment template:
```bash
cp .env.example .env
# Edit .env dan isi dengan credentials kamu
```

Generate secrets:
```bash
# Generate Fernet Key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Generate Secret Key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Start Services

```bash
podman-compose up -d
```

### 4. Access Airflow

- URL: http://localhost:8080
- User: admin
- Password: Check logs dengan `podman-compose logs airflow-webserver | grep "Password"`

## DAGs

### warehouse_sync_optimized
- **Schedule**: Daily @ 02:00 AM
- **Purpose**: Sync 88 tables dari source database ke warehouse (public schema)
- **Features**: Soft-delete support, incremental sync, parallel execution

### warehouse_transform_simple  
- **Schedule**: Daily @ 03:00 AM
- **Purpose**: Transform raw data ke analytics aggregations
- **Transforms**:
  - `daily_table_counts`: Row counts semua tables
  - `orders_daily_summary`: Daily order metrics
  - `customers_summary`: Customer statistics
  - `delivery_daily_summary`: Delivery performance
  - `inventory_summary`: Stock levels

## Documentation

- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Deployment instructions
- [PIPELINE_SETUP.md](PIPELINE_SETUP.md) - Pipeline configuration
- [SOFT_DELETE_IMPLEMENTATION.md](SOFT_DELETE_IMPLEMENTATION.md) - Soft delete feature
- [MLFLOW_QUICKSTART.md](MLFLOW_QUICKSTART.md) - ML tracking setup

## Project Structure

```
dags/                          # Airflow DAG files
  ├── warehouse_sync_optimized.py
  ├── warehouse_transform_simple.py
  ├── config/                  # DAG configurations
  └── utils/                   # Utility modules

logs/                          # Runtime logs (not in git)
plugins/                       # Airflow plugins
docs/                          # Additional documentation

*.sql                          # SQL setup scripts
setup_*.sh                     # Shell setup scripts
requirements-mlflow.txt        # Python dependencies
Dockerfile                     # Custom Airflow image
compose.yml                    # Docker compose (DO NOT commit with secrets!)
```

## Security Notes

⚠️ **NEVER commit**:
- `.env` file (contains real credentials)
- `compose.yml` dengan hardcoded passwords
- `logs/` folder
- `__pycache__/` folders

✅ **Safe to commit**:
- `.env.example` (template without real values)
- `compose.example.yml` (template using env vars)
- DAG files
- Documentation
- SQL scripts

## Contributing

1. Clone repo
2. Copy `.env.example` ke `.env` dan isi credentials
3. Run `podman-compose up -d`
4. Access http://localhost:8080
