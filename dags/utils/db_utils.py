"""
Database utility functions untuk ETL operations
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.exceptions import AirflowException

logger = logging.getLogger(__name__)


class ETLDatabaseManager:
    """Manage database operations untuk ETL pipeline"""
    
    def __init__(self, source_conn_id: str, warehouse_conn_id: str):
        self.source_hook = PostgresHook(postgres_conn_id=source_conn_id)
        self.warehouse_hook = PostgresHook(postgres_conn_id=warehouse_conn_id)
    
    def test_connection(self, conn_type: str = 'both') -> Dict[str, bool]:
        """Test database connections"""
        results = {}
        
        if conn_type in ['source', 'both']:
            try:
                conn = self.source_hook.get_conn()
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                conn.close()
                results['source'] = True
                logger.info("✓ Source database connection successful")
            except Exception as e:
                results['source'] = False
                logger.error(f"✗ Source database connection failed: {e}")
        
        if conn_type in ['warehouse', 'both']:
            try:
                conn = self.warehouse_hook.get_conn()
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                conn.close()
                results['warehouse'] = True
                logger.info("✓ Warehouse database connection successful")
            except Exception as e:
                results['warehouse'] = False
                logger.error(f"✗ Warehouse database connection failed: {e}")
        
        return results
    
    def get_last_sync_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get last successful sync information for a table"""
        query = """
            SELECT 
                last_sync_time,
                last_sync_max_id,
                sync_type,
                total_rows_synced
            FROM metadata.etl_sync_tracking
            WHERE source_table = %s
            AND status = 'success'
            ORDER BY updated_at DESC
            LIMIT 1
        """
        
        try:
            result = self.warehouse_hook.get_first(query, parameters=(table_name,))
            
            if result:
                return {
                    'last_sync_time': result[0],
                    'last_sync_max_id': result[1],
                    'sync_type': result[2],
                    'total_rows_synced': result[3]
                }
            else:
                logger.info(f"No previous sync found for {table_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting last sync info: {e}")
            return None
    
    def update_sync_tracking(
        self,
        table_name: str,
        last_sync_time: datetime,
        total_rows: int,
        status: str,
        error_message: Optional[str] = None,
        execution_time: Optional[float] = None,
        sync_type: str = 'incremental'
    ):
        """Update sync tracking table"""
        query = """
            INSERT INTO metadata.etl_sync_tracking (
                source_schema, source_table, target_schema, target_table,
                last_sync_time, sync_type, total_rows_synced,
                execution_time_seconds, status, error_message, updated_at
            ) VALUES (
                'public', %s, 'raw', %s, %s, %s, %s, %s, %s, %s, NOW()
            )
            ON CONFLICT (source_schema, source_table)
            DO UPDATE SET
                last_sync_time = EXCLUDED.last_sync_time,
                sync_type = EXCLUDED.sync_type,
                total_rows_synced = EXCLUDED.total_rows_synced,
                execution_time_seconds = EXCLUDED.execution_time_seconds,
                status = EXCLUDED.status,
                error_message = EXCLUDED.error_message,
                updated_at = NOW()
        """
        
        try:
            self.warehouse_hook.run(
                query,
                parameters=(
                    table_name, table_name, last_sync_time, sync_type,
                    total_rows, execution_time, status, error_message
                )
            )
            logger.info(f"Updated sync tracking for {table_name}: {status}")
        except Exception as e:
            logger.error(f"Error updating sync tracking: {e}")
            raise
    
    def extract_incremental(
        self,
        table_name: str,
        timestamp_column: str,
        primary_key: str,
        lookback_hours: int = 2,
        created_column: Optional[str] = None,
        batch_size: int = 5000
    ) -> int:
        """Extract data incrementally based on timestamp"""
        import time
        start_time = time.time()
        
        try:
            sync_info = self.get_last_sync_info(table_name)
            
            if sync_info:
                last_sync_time = sync_info['last_sync_time']
                last_sync_time = last_sync_time - timedelta(hours=lookback_hours)
            else:
                last_sync_time = datetime(2020, 1, 1)
                logger.info(f"First sync for {table_name}")
            
            logger.info(f"Extracting {table_name} after {last_sync_time}")
            
            where_clause = f"{timestamp_column} > %(last_sync_time)s"
            if created_column:
                where_clause = f"({timestamp_column} > %(last_sync_time)s OR {created_column} > %(last_sync_time)s)"
            
            extract_query = f"SELECT * FROM {table_name} WHERE {where_clause} ORDER BY {timestamp_column}"
            
            df = self.source_hook.get_pandas_df(extract_query, parameters={'last_sync_time': last_sync_time})
            
            if df.empty:
                logger.info(f"No new data for {table_name}")
                execution_time = time.time() - start_time
                self.update_sync_tracking(table_name, datetime.now(), 0, 'success', execution_time=execution_time)
                return 0
            
            df['loaded_at'] = datetime.now()
            df['source_system'] = 'office_db'
            
            rows_inserted = self._load_to_raw(table_name, df, batch_size)
            
            max_timestamp = df[timestamp_column].max()
            execution_time = time.time() - start_time
            
            self.update_sync_tracking(table_name, max_timestamp, rows_inserted, 'success', execution_time=execution_time)
            
            logger.info(f"Extracted {rows_inserted} rows in {execution_time:.2f}s")
            
            return rows_inserted
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error extracting {table_name}: {e}")
            self.update_sync_tracking(table_name, datetime.now(), 0, 'failed', str(e), execution_time)
            raise
    
    def extract_full(self, table_name: str, primary_key: str, batch_size: int = 5000) -> int:
        """Extract all data from table (full load)"""
        import time
        start_time = time.time()
        
        try:
            logger.info(f"Starting full load for {table_name}")
            
            df = self.source_hook.get_pandas_df(f"SELECT * FROM {table_name}")
            
            if df.empty:
                logger.info(f"No data in {table_name}")
                return 0
            
            df['loaded_at'] = datetime.now()
            df['source_system'] = 'office_db'
            
            self.warehouse_hook.run(f"TRUNCATE TABLE raw.{table_name}")
            
            rows_inserted = self._load_to_raw(table_name, df, batch_size)
            
            execution_time = time.time() - start_time
            self.update_sync_tracking(table_name, datetime.now(), rows_inserted, 'success', execution_time=execution_time, sync_type='full')
            
            logger.info(f"Loaded {rows_inserted} rows in {execution_time:.2f}s")
            
            return rows_inserted
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error in full load: {e}")
            self.update_sync_tracking(table_name, datetime.now(), 0, 'failed', str(e), execution_time, 'full')
            raise
    
    def _load_to_raw(self, table_name: str, df: pd.DataFrame, batch_size: int) -> int:
        """Load DataFrame to raw schema in batches"""
        total_rows = 0
        num_batches = (len(df) + batch_size - 1) // batch_size
        
        logger.info(f"Loading {len(df)} rows in {num_batches} batches")
        
        for i in range(0, len(df), batch_size):
            batch = df[i:i + batch_size]
            rows = [tuple(row) for row in batch.values]
            
            self.warehouse_hook.insert_rows(
                table=f'raw.{table_name}',
                rows=rows,
                target_fields=batch.columns.tolist(),
                commit_every=1000
            )
            
            total_rows += len(batch)
        
        return total_rows
    
    def execute_transformation(self, transformation_name: str, sql_query: str, execution_date: datetime) -> int:
        """Execute transformation query"""
        import time
        start_time = time.time()
        
        try:
            logger.info(f"Executing transformation: {transformation_name}")
            
            self.warehouse_hook.run(sql_query, parameters={'execution_date': execution_date})
            
            execution_time = time.time() - start_time
            logger.info(f"Transformation completed in {execution_time:.2f}s")
            
            return 0
            
        except Exception as e:
            logger.error(f"Error in transformation: {e}")
            raise
    
    def get_table_row_count(self, schema: str, table: str) -> int:
        """Get row count for a table"""
        result = self.warehouse_hook.get_first(f"SELECT COUNT(*) FROM {schema}.{table}")
        return result[0] if result else 0
    
    def check_table_exists(self, schema: str, table: str, db: str = 'warehouse') -> bool:
        """Check if table exists"""
        hook = self.warehouse_hook if db == 'warehouse' else self.source_hook
        
        query = """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s
            )
        """
        
        result = hook.get_first(query, parameters=(schema, table))
        return result[0] if result else False
