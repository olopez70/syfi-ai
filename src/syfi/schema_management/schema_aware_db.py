"""
Schema-aware database utilities for SyFi AI.

Provides safe database operations that gracefully handle
schema variations and missing tables/columns.
"""

import sqlite3
import logging
from typing import Any, Dict, List, Optional, Set, Union
from contextlib import contextmanager

class SchemaAwareConnection:
    """Database connection wrapper with schema awareness."""
    
    def __init__(self, db_path: str, schema_manager=None):
        self.db_path = db_path
        self.schema_manager = schema_manager
        self.logger = logging.getLogger(__name__)
        self._table_cache = {}
        self._column_cache = {}
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper cleanup."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists, with caching."""
        if table_name not in self._table_cache:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (table_name,))
                self._table_cache[table_name] = cursor.fetchone() is not None
        
        return self._table_cache[table_name]
    
    def column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if column exists in table, with caching."""
        cache_key = f"{table_name}.{column_name}"
        
        if cache_key not in self._column_cache:
            if not self.table_exists(table_name):
                self._column_cache[cache_key] = False
            else:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = {row[1] for row in cursor.fetchall()}
                    self._column_cache[cache_key] = column_name in columns
        
        return self._column_cache[cache_key]
    
    def get_table_columns(self, table_name: str) -> Set[str]:
        """Get all columns for a table."""
        if not self.table_exists(table_name):
            return set()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            return {row[1] for row in cursor.fetchall()}
    
    def safe_execute(self, query: str, params: tuple = (), 
                    fallback_result: Any = None) -> Any:
        """Execute query with graceful error handling."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                if query.strip().upper().startswith('SELECT'):
                    return cursor.fetchall()
                else:
                    conn.commit()
                    return cursor.rowcount
                    
        except sqlite3.OperationalError as e:
            self.logger.warning(f"Safe execute failed: {e}, returning fallback")
            return fallback_result
        except Exception as e:
            self.logger.error(f"Unexpected error in safe_execute: {e}")
            raise
    
    def safe_count(self, table_name: str, where_clause: str = "", 
                   params: tuple = ()) -> int:
        """Safely count rows in table."""
        if not self.table_exists(table_name):
            return 0
        
        query = f"SELECT COUNT(*) FROM {table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"
        
        result = self.safe_execute(query, params, fallback_result=[(0,)])
        return result[0][0] if result and len(result) > 0 else 0
    
    def adaptive_query(self, base_query: str, table_name: str, 
                      required_columns: List[str], 
                      optional_columns: Dict[str, Any] = None) -> str:
        """Build query that adapts to available columns."""
        if not self.table_exists(table_name):
            return None
        
        available_columns = self.get_table_columns(table_name)
        
        # Check required columns
        missing_required = [col for col in required_columns if col not in available_columns]
        if missing_required:
            self.logger.warning(f"Missing required columns in {table_name}: {missing_required}")
            return None
        
        # Build adaptive SELECT clause
        select_columns = required_columns.copy()
        
        if optional_columns:
            for col, default_value in optional_columns.items():
                if col in available_columns:
                    select_columns.append(col)
                else:
                    # Use default value for missing column
                    select_columns.append(f"'{default_value}' as {col}")
        
        # Replace column placeholder in base query
        return base_query.format(
            columns=", ".join(select_columns),
            table=table_name
        )

class SchemaAwareMetricsCalculator:
    """Base class for schema-aware metrics calculations."""
    
    def __init__(self, db_connection: SchemaAwareConnection):
        self.db = db_connection
        self.logger = logging.getLogger(__name__)
    
    def calculate_account_status(self) -> Dict[str, int]:
        """Calculate account status with schema flexibility."""
        if not self.db.table_exists('accounts'):
            return {'active': 0, 'inactive': 0, 'total': 0}
        
        # Try different column combinations for status
        status_queries = [
            # Modern schema with 'status' column
            ("status = 'active'", "status != 'active' OR status IS NULL"),
            # Legacy schema with 'is_active' column  
            ("is_active = 1", "is_active = 0 OR is_active IS NULL"),
            # Fallback - assume all accounts are active if no status column
            ("1=1", "1=0")
        ]
        
        for active_condition, inactive_condition in status_queries:
            # Test if we can use this condition
            test_query = f"SELECT COUNT(*) FROM accounts WHERE {active_condition}"
            result = self.db.safe_execute(test_query, fallback_result=None)
            
            if result is not None:
                # This condition works, use it for full calculation
                active_count = result[0][0]
                inactive_count = self.db.safe_execute(
                    f"SELECT COUNT(*) FROM accounts WHERE {inactive_condition}",
                    fallback_result=[(0,)]
                )[0][0]
                
                return {
                    'active': active_count,
                    'inactive': inactive_count, 
                    'total': active_count + inactive_count
                }
        
        # Ultimate fallback
        total = self.db.safe_count('accounts')
        return {'active': total, 'inactive': 0, 'total': total}