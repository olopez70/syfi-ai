"""
Core data profiling analyzer for SyFi AI banking data.

This module provides the main BankingDataProfiler class that coordinates
comprehensive analysis of synthetic banking databases.
"""

import sqlite3
import json
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal
from ..schema_management import SchemaAwareConnection, get_schema_manager

@dataclass
class ProfileSummary:
    """Summary of database profiling results."""
    database_path: str
    analysis_date: datetime
    total_customers: int
    total_accounts: int 
    total_transactions: int
    database_size_kb: float
    unique_profiles: int
    date_range: Optional[Tuple[date, date]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'database_path': self.database_path,
            'analysis_date': self.analysis_date.isoformat(),
            'total_customers': self.total_customers,
            'total_accounts': self.total_accounts,
            'total_transactions': self.total_transactions,
            'database_size_kb': self.database_size_kb,
            'unique_profiles': self.unique_profiles,
            'date_range': [self.date_range[0].isoformat(), self.date_range[1].isoformat()] if self.date_range else None
        }

@dataclass 
class TableProfile:
    """Detailed profile of a single table."""
    table_name: str
    row_count: int
    column_count: int
    columns: List[Dict[str, Any]]
    data_types: Dict[str, str]
    null_counts: Dict[str, int]
    unique_counts: Dict[str, int]
    sample_values: Dict[str, List[Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'table_name': self.table_name,
            'row_count': self.row_count,
            'column_count': self.column_count,
            'columns': self.columns,
            'data_types': self.data_types,
            'null_counts': self.null_counts,
            'unique_counts': self.unique_counts,
            'sample_values': self.sample_values
        }

class BankingDataProfiler:
    """
    Comprehensive data profiler for SyFi AI banking databases.
    
    Provides detailed analysis of customers, accounts, transactions,
    and banking-specific relationships and patterns.
    """
    
    def __init__(self, database_path: str):
        """
        Initialize profiler with database path.
        
        Args:
            database_path: Path to SQLite database file
        """
        self.database_path = Path(database_path)
        if not self.database_path.exists():
            raise FileNotFoundError(f"Database not found: {database_path}")
        
        # Initialize schema-aware database connection
        try:
            self.db = SchemaAwareConnection(str(database_path))
            self.schema_manager = get_schema_manager(str(database_path))
            # Validate database accessibility
            self.db.safe_execute("SELECT name FROM sqlite_master WHERE type='table'")
        except (sqlite3.DatabaseError, sqlite3.OperationalError) as e:
            raise sqlite3.DatabaseError(f"Invalid database file: {database_path}") from e
        
        # Maintain legacy connection for backward compatibility where needed
        self.conn = sqlite3.connect(str(self.database_path))
        self.conn.row_factory = sqlite3.Row
        
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.conn:
            self.conn.close()
    
    def _column_exists(self, table: str, column: str) -> bool:
        """Check if a column exists in a table."""
        return self.db.column_exists(table, column)
    
    def generate_full_profile(self) -> Dict[str, Any]:
        """
        Generate comprehensive profile of the entire database.
        
        Returns:
            Dictionary containing complete profiling results
        """
        profile = {
            'summary': self._generate_summary(),
            'tables': self._profile_all_tables(),
            'banking_metrics': self._calculate_banking_metrics(),
            'relationships': self._analyze_relationships(),
            'data_quality': self._assess_data_quality(),
            'customer_profiles': self._analyze_customer_profiles()
        }
        
        return profile
    
    def _table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        return self.db.table_exists(table_name)
    
    def _generate_summary(self) -> ProfileSummary:
        """Generate high-level database summary."""
        
        # Get table counts using schema-aware operations
        customer_count = self.db.safe_count('customers')
        account_count = self.db.safe_count('accounts')
        transaction_count = self.db.safe_count('transactions')
        
        # Get database size
        db_size_kb = self.database_path.stat().st_size / 1024
        
        # Get unique profiles using schema-aware operations
        unique_profiles = 0
        if self._table_exists('customers') and self._column_exists('customers', 'profile_description'):
            result = self.db.safe_execute("SELECT COUNT(DISTINCT profile_description) FROM customers WHERE profile_description IS NOT NULL")
            if result and len(result) > 0:
                unique_profiles = result[0][0] if result[0][0] else 0
        
        # Get transaction date range using schema-aware operations
        date_range = None
        if transaction_count > 0 and self._table_exists('transactions') and self._column_exists('transactions', 'transaction_date'):
            result = self.db.safe_execute("SELECT MIN(DATE(transaction_date)), MAX(DATE(transaction_date)) FROM transactions")
            if result and len(result) > 0 and result[0][0] and result[0][1]:
                try:
                    date_range = (
                        datetime.strptime(result[0][0], '%Y-%m-%d').date(),
                        datetime.strptime(result[0][1], '%Y-%m-%d').date()
                    )
                except (ValueError, TypeError):
                    date_range = None
        
        return ProfileSummary(
            database_path=str(self.database_path),
            analysis_date=datetime.now(),
            total_customers=customer_count,
            total_accounts=account_count,
            total_transactions=transaction_count,
            database_size_kb=db_size_kb,
            unique_profiles=unique_profiles,
            date_range=date_range
        )
    
    def _profile_all_tables(self) -> Dict[str, TableProfile]:
        """Profile all tables in the database."""
        cursor = self.conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        
        profiles = {}
        for table_name in tables:
            profiles[table_name] = self._profile_table(table_name)
            
        return profiles
    
    def _profile_table(self, table_name: str) -> TableProfile:
        """Profile a single table."""
        cursor = self.conn.cursor()
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        
        columns = []
        data_types = {}
        for col in columns_info:
            col_dict = {
                'name': col[1],
                'type': col[2], 
                'not_null': bool(col[3]),
                'primary_key': bool(col[5])
            }
            columns.append(col_dict)
            data_types[col[1]] = col[2]
        
        # Validate table name (security: prevent injection)
        if not table_name.replace('_', '').isalnum():
            raise ValueError(f"Invalid table name: {table_name}")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")  # nosec B608 - table_name validated
        row_count = cursor.fetchone()[0]
        
        # Analyze each column if table has data
        null_counts = {}
        unique_counts = {}
        sample_values = {}
        
        if row_count > 0:
            for col_name in data_types.keys():
                # Validate column name (security: prevent injection)
                if not col_name.replace('_', '').isalnum():
                    continue  # Skip invalid column names
                
                # Count nulls
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {col_name} IS NULL")  # nosec B608 - validated
                null_counts[col_name] = cursor.fetchone()[0]
                
                # Count unique values
                cursor.execute(f"SELECT COUNT(DISTINCT {col_name}) FROM {table_name}")  # nosec B608 - validated
                unique_counts[col_name] = cursor.fetchone()[0]
                
                # Get sample values (up to 5)
                cursor.execute(f"SELECT DISTINCT {col_name} FROM {table_name} WHERE {col_name} IS NOT NULL LIMIT 5")  # nosec B608 - validated
                samples = [row[0] for row in cursor.fetchall()]
                sample_values[col_name] = samples
        
        return TableProfile(
            table_name=table_name,
            row_count=row_count,
            column_count=len(columns),
            columns=columns,
            data_types=data_types,
            null_counts=null_counts,
            unique_counts=unique_counts,
            sample_values=sample_values
        )
    
    def _calculate_banking_metrics(self) -> Dict[str, Any]:
        """Calculate banking-specific metrics."""
        from .banking_metrics import BankingMetricsCalculator
        
        # Use schema-aware BankingMetricsCalculator
        calculator = BankingMetricsCalculator(str(self.database_path))
        return calculator.calculate_all_metrics()
    
    def _analyze_relationships(self) -> Dict[str, Any]:
        """Analyze relationships between tables."""
        cursor = self.conn.cursor()
        
        relationships = {}
        
        # Customer-Account relationships
        if self._table_exists('customers') and self._table_exists('accounts'):
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_relationships,
                    AVG(account_count) as avg_accounts_per_customer,
                    MIN(account_count) as min_accounts,
                    MAX(account_count) as max_accounts
                FROM (
                    SELECT customer_id, COUNT(*) as account_count
                    FROM accounts 
                    GROUP BY customer_id
                )
            """)
            result = cursor.fetchone()
            relationships['customer_accounts'] = {
                'total_relationships': result[0],
                'avg_accounts_per_customer': round(result[1], 2) if result[1] else 0,
                'min_accounts': result[2] if result[2] else 0,
                'max_accounts': result[3] if result[3] else 0
            }
        
        # Account-Transaction relationships
        if self._table_exists('accounts') and self._table_exists('transactions'):
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT a.account_id) as accounts_with_transactions,
                    COUNT(t.transaction_id) as total_transactions,
                    COALESCE(AVG(t_count.transaction_count), 0) as avg_transactions_per_account
                FROM accounts a
                LEFT JOIN transactions t ON a.account_id = t.account_id
                LEFT JOIN (
                    SELECT account_id, COUNT(*) as transaction_count
                    FROM transactions 
                    GROUP BY account_id
                ) t_count ON a.account_id = t_count.account_id
            """)
            result = cursor.fetchone()
            relationships['account_transactions'] = {
                'accounts_with_transactions': result[0],
                'total_transactions': result[1],
                'avg_transactions_per_account': round(result[2], 2) if result[2] else 0
            }
        
        return relationships
    
    def _assess_data_quality(self) -> Dict[str, Any]:
        """Assess data quality across tables."""
        cursor = self.conn.cursor()
        
        quality_metrics = {}
        
        # Check for orphaned records
        orphaned_accounts = 0
        orphaned_transactions = 0
        
        if self._table_exists('accounts') and self._table_exists('customers'):
            cursor.execute("""
                SELECT COUNT(*) FROM accounts a 
                LEFT JOIN customers c ON a.customer_id = c.customer_id 
                WHERE c.customer_id IS NULL
            """)
            orphaned_accounts = cursor.fetchone()[0]
        
        if self._table_exists('transactions') and self._table_exists('accounts'):
            cursor.execute("""
                SELECT COUNT(*) FROM transactions t 
                LEFT JOIN accounts a ON t.account_id = a.account_id 
                WHERE a.account_id IS NULL
            """)
            orphaned_transactions = cursor.fetchone()[0]
        
        quality_metrics['referential_integrity'] = {
            'orphaned_accounts': orphaned_accounts,
            'orphaned_transactions': orphaned_transactions
        }
        
        # Profile completeness
        if self._table_exists('customers'):
            # Build query safely using predefined column expressions
            profile_check = "SUM(CASE WHEN profile_description IS NOT NULL THEN 1 ELSE 0 END)" if self._column_exists('customers', 'profile_description') else "0"
            email_check = "SUM(CASE WHEN email IS NOT NULL THEN 1 ELSE 0 END)" if self._column_exists('customers', 'email') else "0"
            phone_check = "SUM(CASE WHEN phone IS NOT NULL THEN 1 ELSE 0 END)" if self._column_exists('customers', 'phone') else "0"
            
            # Safe query execution - expressions are predefined constants, not user input
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total_customers,
                    {profile_check} as customers_with_profiles,
                    {email_check} as customers_with_email,
                    {phone_check} as customers_with_phone
                FROM customers
            """)  # nosec B608 - expressions are safe constants
            result = cursor.fetchone()
            total = result[0]
            quality_metrics['customer_completeness'] = {
                'total_customers': total,
                'profile_completeness': round((result[1] / total * 100), 1) if total > 0 else 0,
                'email_completeness': round((result[2] / total * 100), 1) if total > 0 else 0,
                'phone_completeness': round((result[3] / total * 100), 1) if total > 0 else 0
            }
        
        return quality_metrics
    
    def _analyze_customer_profiles(self) -> Dict[str, Any]:
        """Analyze customer profile patterns."""
        cursor = self.conn.cursor()
        
        profile_analysis = {}
        
        if not self._table_exists('customers'):
            return profile_analysis
        
        # Profile distribution (handle databases without profile_description)
        try:
            cursor.execute("""
                SELECT profile_description, COUNT(*) as count
                FROM customers 
                WHERE profile_description IS NOT NULL
                GROUP BY profile_description
                ORDER BY count DESC
            """)
            profile_dist = {}
            for row in cursor.fetchall():
                profile_dist[row[0]] = row[1]
            profile_analysis['profile_distribution'] = profile_dist
        except sqlite3.OperationalError:
            # Column doesn't exist
            profile_analysis['profile_distribution'] = {'No profile data': 0}
        
        # Household composition analysis (handle missing columns)
        try:
            cursor.execute("""
                SELECT 
                    AVG(household_size) as avg_household_size,
                    AVG(num_adults) as avg_adults,
                    AVG(num_children) as avg_children,
                    AVG(num_pets) as avg_pets
                FROM customers 
                WHERE household_size IS NOT NULL
            """)
            result = cursor.fetchone()
            if result[0]:
                profile_analysis['household_composition'] = {
                    'avg_household_size': round(result[0], 1),
                    'avg_adults': round(result[1], 1),
                    'avg_children': round(result[2], 1), 
                    'avg_pets': round(result[3], 1)
                }
        except sqlite3.OperationalError:
            # Columns don't exist, skip household analysis
            pass
        
        # Employment distribution (handle missing columns)
        try:
            cursor.execute("""
                SELECT employment_status, COUNT(*) as count
                FROM customers 
                WHERE employment_status IS NOT NULL
                GROUP BY employment_status
                ORDER BY count DESC
            """)
            employment_dist = {}
            for row in cursor.fetchall():
                employment_dist[row[0]] = row[1]
            profile_analysis['employment_distribution'] = employment_dist
        except sqlite3.OperationalError:
            # Column doesn't exist
            profile_analysis['employment_distribution'] = {}
        
        return profile_analysis
    
    def _table_exists(self, table_name: str) -> bool:
        """Check if table exists in database."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (table_name,))
        return cursor.fetchone() is not None