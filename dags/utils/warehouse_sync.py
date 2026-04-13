"""
Warehouse Sync Utility
Reusable functions untuk sync tables dari source ke warehouse
"""

import psycopg2
from typing import Dict, Tuple, List, Optional


# Default database configurations
DEFAULT_SOURCE_DB_CONFIG = {
    'host': 'devom.silog.co.id',
    'database': 'om',
    'user': 'om',
    'password': 'om',
}

DEFAULT_TARGET_DB_CONFIG = {
    'host': 'localhost',
    'database': 'warehouse',
    'user': 'postgres',
    'password': 'postgres123',
}

# Table mappings: source_table -> (target_schema, target_table)
DEFAULT_TABLE_MAPPINGS = {
    # Driver schema
    'daftar_user': ('driver', 'daftar_user'),
    'attachment_driver': ('driver', 'attachment_driver'),
    'laporan_pengemudi': ('driver', 'laporan_pengemudi'),
    'kontak_darurat_pengemudi': ('driver', 'kontak_darurat'),
    
    # Armada schema
    'armada_tms': ('armada', 'armada_tms'),
    'jenis_armada': ('armada', 'jenis_armada'),
    'driver_armada': ('armada', 'driver_armada'),
    'armada_perangkat': ('armada', 'armada_perangkat'),
    'attachment_armada': ('armada', 'attachment_armada'),
    
    # Delivery schema
    'delivery_order': ('delivery', 'delivery_order'),
    'detail_do': ('delivery', 'detail_do'),
    'jenis_order': ('delivery', 'jenis_order'),
    'attachment_gudang': ('delivery', 'attachment_gudang'),
    
    # Activity schema
    'log_perjalanan_armada': ('activity', 'log_perjalanan_armada'),
    'log_aktifitas_driver': ('activity', 'log_aktifitas_driver'),
    'log_perangkat': ('activity', 'log_perangkat'),
    'log_chat': ('activity', 'log_chat'),
    'log_panggilan': ('activity', 'log_panggilan'),
    'log_sensor': ('activity', 'log_sensor'),
    'alert_geofence': ('activity', 'alert_geofence'),
    
    # Financial schema
    'orders': ('financial', 'orders'),
    'detail_po': ('financial', 'detail_po'),
    'jenis_transaksi': ('financial', 'jenis_transaksi'),
    'detail_qc': ('financial', 'detail_qc'),
    'bank': ('financial', 'bank'),
    
    # Support schema
    'attachment': ('support', 'attachment'),
    'jenis_file': ('support', 'jenis_file'),
    'chat_room': ('support', 'chat_room'),
    'attachment_chat': ('support', 'attachment_chat'),
    'attachment_pengembalian': ('support', 'attachment_pengembalian'),
    'attachment_perangkat': ('support', 'attachment_perangkat'),
    'attachment_qc': ('support', 'attachment_qc'),
    
    # Weather schema (PRIORITY)
    'fact_weather_hourly': ('weather', 'fact_weather_hourly'),
    
    # Master schema
    'gudang': ('master', 'gudang'),
    'locations': ('master', 'locations'),
    'kategori_produk': ('master', 'kategori_produk'),
    'konversi': ('master', 'konversi'),
    'jenis_satuan': ('master', 'jenis_satuan'),
    'atribut': ('master', 'atribut'),
    'atribut_produk': ('master', 'atribut_produk'),
    'kriteria_produk': ('master', 'kriteria_produk'),
    'geofence': ('master', 'geofence'),
    'jenis_insiden': ('master', 'jenis_insiden'),
    'jenis_notifikasi': ('master', 'jenis_notifikasi'),
    'laporan_darurat': ('master', 'laporan_darurat'),
    'rating': ('master', 'rating'),
}


def sync_table(
    source_table: str,
    target_schema: str,
    target_table: str,
    source_db_config: Optional[Dict] = None,
    target_db_config: Optional[Dict] = None
) -> Tuple[bool, str]:
    """
    Sync a single table from source to warehouse
    
    Args:
        source_table: Source table name
        target_schema: Target schema name
        target_table: Target table name
        source_db_config: Source database config (optional, uses default if not provided)
        target_db_config: Target database config (optional, uses default if not provided)
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    if source_db_config is None:
        source_db_config = DEFAULT_SOURCE_DB_CONFIG
    if target_db_config is None:
        target_db_config = DEFAULT_TARGET_DB_CONFIG
    
    try:
        # Connect to source
        source_conn = psycopg2.connect(**source_db_config)
        source_cursor = source_conn.cursor()
        
        # Connect to target
        target_conn = psycopg2.connect(**target_db_config)
        target_cursor = target_conn.cursor()
        
        # Get column info from source
        source_cursor.execute(f"SELECT * FROM {source_table} LIMIT 0")
        columns = [desc[0] for desc in source_cursor.description]
        
        # Clear target table
        target_cursor.execute(f"TRUNCATE TABLE {target_schema}.{target_table}")
        
        # Fetch all data from source
        source_cursor.execute(f"SELECT * FROM {source_table}")
        rows = source_cursor.fetchall()
        
        # Insert into target
        if rows:
            col_names = ', '.join(columns)
            placeholders = ', '.join(['%s'] * len(columns))
            insert_query = f"INSERT INTO {target_schema}.{target_table} ({col_names}) VALUES ({placeholders})"
            target_cursor.executemany(insert_query, rows)
            target_conn.commit()
            print(f"✓ {target_schema}.{target_table}: {len(rows)} rows synced")
        else:
            print(f"✓ {target_schema}.{target_table}: 0 rows (table empty in source)")
        
        source_cursor.close()
        source_conn.close()
        target_cursor.close()
        target_conn.close()
        
        return True, f"{target_schema}.{target_table}: {len(rows) if rows else 0} rows"
    
    except Exception as e:
        error_msg = f"ERROR syncing {target_schema}.{target_table}: {str(e)}"
        print(error_msg)
        return False, error_msg


def sync_all_tables(
    table_mappings: Optional[Dict] = None,
    source_db_config: Optional[Dict] = None,
    target_db_config: Optional[Dict] = None,
    priority_tables: Optional[List[str]] = None
) -> Dict[str, any]:
    """
    Sync all tables from source to warehouse
    
    Args:
        table_mappings: Dict mapping source_table -> (target_schema, target_table)
                       Uses DEFAULT_TABLE_MAPPINGS if not provided
        source_db_config: Source database config (optional)
        target_db_config: Target database config (optional)
        priority_tables: List of source table names to sync first (optional)
    
    Returns:
        Dict with 'success_count' and 'failed_count'
    """
    if table_mappings is None:
        table_mappings = DEFAULT_TABLE_MAPPINGS
    if source_db_config is None:
        source_db_config = DEFAULT_SOURCE_DB_CONFIG
    if target_db_config is None:
        target_db_config = DEFAULT_TARGET_DB_CONFIG
    
    print("=" * 60)
    print("Starting warehouse table sync...")
    print("=" * 60)
    
    results = {
        'success': [],
        'failed': [],
    }
    
    # Sync priority tables first if specified
    if priority_tables:
        print(f"\n📍 PRIORITY: Syncing {len(priority_tables)} priority tables first...")
        for source_table in priority_tables:
            if source_table in table_mappings:
                target_schema, target_table = table_mappings[source_table]
                success, msg = sync_table(
                    source_table, target_schema, target_table,
                    source_db_config, target_db_config
                )
                if success:
                    results['success'].append(msg)
                else:
                    results['failed'].append(msg)
    
    # Then sync all other tables
    print("\n📊 Syncing remaining tables...")
    for source_table, (target_schema, target_table) in table_mappings.items():
        # Skip if already synced in priority
        if priority_tables and source_table in priority_tables:
            continue
        
        success, msg = sync_table(
            source_table, target_schema, target_table,
            source_db_config, target_db_config
        )
        if success:
            results['success'].append(msg)
        else:
            results['failed'].append(msg)
    
    # Summary
    print("\n" + "=" * 60)
    print("SYNC SUMMARY")
    print("=" * 60)
    print(f"✅ Success: {len(results['success'])} tables")
    print(f"❌ Failed: {len(results['failed'])} tables")
    
    if results['failed']:
        print("\nFailed tables:")
        for msg in results['failed']:
            print(f"  - {msg}")
    
    print("\nDetailed results:")
    for msg in results['success'][:10]:  # Show first 10
        print(f"  ✓ {msg}")
    if len(results['success']) > 10:
        print(f"  ... and {len(results['success']) - 10} more")
    
    return {
        'success_count': len(results['success']),
        'failed_count': len(results['failed']),
        'success_messages': results['success'],
        'failed_messages': results['failed'],
    }


def sync_tables_by_schema(
    target_schema: str,
    table_mappings: Optional[Dict] = None,
    source_db_config: Optional[Dict] = None,
    target_db_config: Optional[Dict] = None
) -> Dict[str, any]:
    """
    Sync only tables for a specific target schema
    
    Args:
        target_schema: Target schema to sync (e.g., 'driver', 'armada', 'weather')
        table_mappings: Dict mapping source_table -> (target_schema, target_table)
        source_db_config: Source database config
        target_db_config: Target database config
    
    Returns:
        Dict with sync results
    """
    if table_mappings is None:
        table_mappings = DEFAULT_TABLE_MAPPINGS
    
    # Filter table mappings for the specified schema
    filtered_mappings = {
        src: (tgt_schema, tgt_table)
        for src, (tgt_schema, tgt_table) in table_mappings.items()
        if tgt_schema == target_schema
    }
    
    print(f"Syncing {len(filtered_mappings)} tables for schema: {target_schema}")
    
    return sync_all_tables(
        table_mappings=filtered_mappings,
        source_db_config=source_db_config,
        target_db_config=target_db_config
    )
