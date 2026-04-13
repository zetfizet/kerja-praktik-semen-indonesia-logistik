"""
Data Quality Check utilities
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from airflow.providers.postgres.hooks.postgres import PostgresHook

logger = logging.getLogger(__name__)


class DataQualityChecker:
    """Data quality validation for ETL pipeline"""
    
    def __init__(self, warehouse_conn_id: str):
        self.warehouse_hook = PostgresHook(postgres_conn_id=warehouse_conn_id)
    
    def log_quality_check(
        self,
        table_name: str,
        check_name: str,
        check_type: str,
        status: str,
        expected_value: Any = None,
        actual_value: Any = None,
        details: str = None,
        dag_run_id: str = None,
        execution_date: datetime = None
    ):
        """Log data quality check result"""
        query = """
            INSERT INTO metadata.data_quality_log (
                table_name, check_name, check_type, expected_value,
                actual_value, status, details, dag_run_id, execution_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        try:
            self.warehouse_hook.run(
                query,
                parameters=(
                    table_name, check_name, check_type,
                    str(expected_value) if expected_value else None,
                    str(actual_value) if actual_value else None,
                    status, details, dag_run_id, execution_date
                )
            )
        except Exception as e:
            logger.error(f"Error logging quality check: {e}")
    
    def check_null_values(
        self, schema: str, table_name: str, columns: List[str],
        dag_run_id: str = None, execution_date: datetime = None
    ) -> bool:
        """Check for NULL values in specified columns"""
        all_passed = True
        
        for column in columns:
            query = f"SELECT COUNT(*) FROM {schema}.{table_name} WHERE {column} IS NULL"
            
            try:
                result = self.warehouse_hook.get_first(query)
                null_count = result[0] if result else 0
                
                status = 'passed' if null_count == 0 else 'failed'
                all_passed = all_passed and (null_count == 0)
                
                self.log_quality_check(
                    f"{schema}.{table_name}", f"null_check_{column}",
                    'null_check', status, 0, null_count,
                    f"Found {null_count} NULL values", dag_run_id, execution_date
                )
                
                if null_count > 0:
                    logger.warning(f"NULL check failed for {column}: {null_count} NULLs")
                else:
                    logger.info(f"✓ NULL check passed for {column}")
                    
            except Exception as e:
                logger.error(f"Error checking NULLs: {e}")
                all_passed = False
        
        return all_passed
    
    def check_duplicates(
        self, schema: str, table_name: str, columns: List[str],
        dag_run_id: str = None, execution_date: datetime = None
    ) -> bool:
        """Check for duplicate values"""
        column_list = ', '.join(columns)
        query = f"""
            SELECT {column_list}, COUNT(*) as cnt
            FROM {schema}.{table_name}
            GROUP BY {column_list}
            HAVING COUNT(*) > 1
        """
        
        try:
            result = self.warehouse_hook.get_records(query)
            duplicate_count = len(result) if result else 0
            
            status = 'passed' if duplicate_count == 0 else 'failed'
            
            self.log_quality_check(
                f"{schema}.{table_name}",
                f"duplicate_check_{column_list.replace(', ', '_')}",
                'duplicate_check', status, 0, duplicate_count,
                f"Found {duplicate_count} duplicates",
                dag_run_id, execution_date
            )
            
            if duplicate_count > 0:
                logger.warning(f"Duplicate check failed: {duplicate_count} duplicates")
            else:
                logger.info(f"✓ Duplicate check passed")
            
            return duplicate_count == 0
            
        except Exception as e:
            logger.error(f"Error checking duplicates: {e}")
            return False
    
    def run_table_checks(
        self, table_config: Dict[str, Any], schema: str = 'raw',
        dag_run_id: str = None, execution_date: datetime = None
    ) -> bool:
        """Run all configured data quality checks for a table"""
        table_name = table_config['name']
        checks = table_config.get('data_quality_checks', [])
        
        if not checks:
            logger.info(f"No quality checks configured for {table_name}")
            return True
        
        logger.info(f"Running {len(checks)} quality checks for {table_name}")
        
        all_passed = True
        
        for check in checks:
            check_name = check['check_name']
            
            try:
                if check_name == 'null_check':
                    passed = self.check_null_values(
                        schema, table_name, check['columns'],
                        dag_run_id, execution_date
                    )
                    all_passed = all_passed and passed
                
                elif check_name == 'duplicate_check':
                    passed = self.check_duplicates(
                        schema, table_name, check['columns'],
                        dag_run_id, execution_date
                    )
                    all_passed = all_passed and passed
                
                else:
                    logger.warning(f"Unknown check type: {check_name}")
                    
            except Exception as e:
                logger.error(f"Error running check {check_name}: {e}")
                all_passed = False
        
        if all_passed:
            logger.info(f"✓ All quality checks passed for {table_name}")
        else:
            logger.error(f"✗ Some quality checks failed for {table_name}")
        
        return all_passed
