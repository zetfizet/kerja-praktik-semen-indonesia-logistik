"""
Configuration untuk tabel-tabel yang akan di-sync
Customize sesuai dengan kebutuhan business Anda
"""

# Daftar tabel yang akan di-sync dari PostgreSQL kantor
# Hanya pilih tabel yang diperlukan untuk dashboard (bukan semua 85 tabel)
TABLES_TO_SYNC = [
    {
        'name': 'armada_tms',
        'source_schema': 'public',
        'target_schema': 'raw',
        'target_table': 'armada',  # Nama table di raw schema
        'sync_strategy': 'incremental',  # 'incremental' atau 'full'
        'timestamp_column': 'diubah_pada',  # Kolom untuk incremental sync
        'primary_key': 'id_armada',
        'batch_size': 1000,
        'priority': 1,  # 1=highest priority
        'description': 'Data armada kendaraan',
        'enabled': True,
        'data_quality_checks': [
            {
                'check_name': 'null_check',
                'columns': ['id_armada', 'no_polisi'],  # Kolom yang tidak boleh NULL
            },
            {
                'check_name': 'duplicate_check',
                'columns': ['id_armada'],
            },
        ],
    },
    {
        'name': 'jenis_armada',
        'source_schema': 'public',
        'target_schema': 'raw',
        'target_table': 'jenis_armada',
        'sync_strategy': 'full',  # Full load karena data master biasanya kecil
        'timestamp_column': None,
        'primary_key': 'id_jenis_armada',
        'batch_size': 500,
        'priority': 2,
        'description': 'Master jenis armada',
        'enabled': True,
        'data_quality_checks': [
            {
                'check_name': 'null_check',
                'columns': ['id_jenis_armada'],
            },
        ],
    },
    {
        'name': 'parent_armada',
        'source_schema': 'public',
        'target_schema': 'raw',
        'target_table': 'parent_armada',
        'sync_strategy': 'full',
        'timestamp_column': None,
        'primary_key': 'id_parent_armada',
        'batch_size': 500,
        'priority': 3,
        'description': 'Master parent/kategori armada',
        'enabled': True,
        'data_quality_checks': [
            {
                'check_name': 'null_check',
                'columns': ['id_parent_armada'],
            },
        ],
    },
    {
        'name': 'status_armada',
        'source_schema': 'public',
        'target_schema': 'raw',
        'target_table': 'status_armada',
        'sync_strategy': 'full',
        'timestamp_column': None,
        'primary_key': 'id_status_armada',
        'batch_size': 500,
        'priority': 4,
        'description': 'Master status armada',
        'enabled': True,
        'data_quality_checks': [
            {
                'check_name': 'null_check',
                'columns': ['id_status_armada'],
            },
        ],
    },
    {
        'name': 'delivery_order',
        'source_schema': 'public',
        'target_schema': 'raw',
        'target_table': 'delivery_order',
        'sync_strategy': 'incremental',
        'timestamp_column': 'updated_at',  # Sesuaikan dengan column timestamp yang ada
        'primary_key': 'id_do',  # Sesuaikan dengan primary key yang ada
        'batch_size': 1000,
        'priority': 1,
        'description': 'Data delivery order',
        'enabled': True,
        'data_quality_checks': [
            {
                'check_name': 'null_check',
                'columns': ['id_do'],
            },
        ],
    },
]

# ETL Configuration
ETL_CONFIG = {
    'default_batch_size': 5000,
    'max_parallel_tasks': 5,  # Limit concurrent DB connections
    'query_timeout_seconds': 3600,  # 1 hour
    'connection_timeout_seconds': 30,
    'retry_attempts': 3,
    'retry_delay_minutes': 5,
    'incremental_lookback_hours': 2,  # Look back 2 jam untuk avoid missing data
    'data_retention_days': 7,  # Keep raw data for 7 days
}

# Alert Configuration
ALERT_CONFIG = {
    'email_on_failure': True,
    'email_recipients': ['data-team@company.com'],
    'slack_webhook_url': None,  # Set jika ada Slack integration
    'alert_on_data_quality_failure': True,
    'alert_on_sync_lag_hours': 3,  # Alert jika data tidak update > 3 jam
}

# Database Connection IDs (sesuaikan dengan Airflow Connections)
CONNECTION_IDS = {
    'source_db': 'source_db',  # PostgreSQL kantor
    'warehouse_db': 'warehouse_db',  # PostgreSQL analytics
}

# Schema names di warehouse DB
WAREHOUSE_SCHEMAS = {
    'raw': 'raw',  # Raw data dari source
    'staging': 'staging',  # After basic transformation
    'analytics': 'analytics',  # Ready for dashboard
    'metadata': 'metadata',  # ETL tracking tables
}

# Transformation queries untuk analytics layer
TRANSFORMATION_QUERIES = {
    # Tambahkan transformation queries sesuai kebutuhan
}

# Data Quality Thresholds
DATA_QUALITY_THRESHOLDS = {
    'min_row_count': 0,
    'max_null_percentage': 5,
    'max_duplicate_percentage': 0,
    'max_sync_lag_hours': 2,
}
