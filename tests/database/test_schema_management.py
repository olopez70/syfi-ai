"""
Tests for database schema management and validation.

Ensures schema-aware components handle various database configurations gracefully.
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from src.syfi.schema_management.schema_manager import (
    SchemaManager, SchemaVersion, SCHEMA_DEFINITIONS,
    get_schema_manager
)
from src.syfi.schema_management.schema_aware_db import (
    SchemaAwareConnection, SchemaAwareMetricsCalculator
)


class TestSchemaManager:
    """Test schema management functionality."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as f:
            db_path = f.name
        yield db_path
        Path(db_path).unlink(missing_ok=True)
    
    def test_schema_manager_initialization(self, temp_db):
        """Test schema manager creation."""
        manager = SchemaManager(temp_db)
        assert manager.db_path == Path(temp_db)
    
    def test_detect_empty_database_schema(self, temp_db):
        """Test schema detection on empty database."""
        # Create empty database
        conn = sqlite3.connect(temp_db)
        conn.close()
        
        manager = SchemaManager(temp_db)
        version = manager.get_current_schema_version()
        assert version == SchemaVersion.V1_0_BASIC
    
    def test_detect_basic_schema(self, temp_db):
        """Test detection of basic schema (customers + accounts)."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE customers (
                customer_id TEXT PRIMARY KEY,
                first_name TEXT,
                last_name TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE accounts (
                account_id TEXT PRIMARY KEY,
                customer_id TEXT,
                account_type TEXT,
                balance DECIMAL(12,2)
            )
        """)
        
        conn.commit()
        conn.close()
        
        manager = SchemaManager(temp_db)
        version = manager.get_current_schema_version()
        assert version == SchemaVersion.V1_0_BASIC
    
    def test_detect_enhanced_schema(self, temp_db):
        """Test detection of enhanced schema with all tables."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Create full enhanced schema
        cursor.execute("""
            CREATE TABLE customers (
                customer_id TEXT PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                profile_description TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE accounts (
                account_id TEXT PRIMARY KEY,
                customer_id TEXT,
                account_type TEXT,
                balance DECIMAL(12,2),
                status TEXT DEFAULT 'active'
            )
        """)
        
        cursor.execute("""
            CREATE TABLE transactions (
                transaction_id TEXT PRIMARY KEY,
                account_id TEXT,
                transaction_type TEXT,
                amount DECIMAL(10,2)
            )
        """)
        
        conn.commit()
        conn.close()
        
        manager = SchemaManager(temp_db)
        version = manager.get_current_schema_version()
        assert version == SchemaVersion.V1_2_ENHANCED
    
    def test_validate_schema_compatibility_success(self, temp_db):
        """Test successful schema compatibility validation."""
        # Create compatible database
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE customers (
                customer_id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT,
                profile_description TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        
        manager = SchemaManager(temp_db)
        required_schema = SCHEMA_DEFINITIONS[SchemaVersion.V1_2_ENHANCED]
        issues = manager.validate_schema_compatibility(required_schema)
        
        # Should have missing tables but customers table should be compatible
        assert 'accounts' in issues['missing_tables']
        assert 'transactions' in issues['missing_tables']
        # Customers table exists with required columns
        assert not any('customers.customer_id' in issue for issue in issues['missing_columns'])
    
    def test_validate_missing_required_columns(self, temp_db):
        """Test detection of missing required columns."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE customers (
                customer_id TEXT PRIMARY KEY
                -- Missing first_name, last_name required columns
            )
        """)
        
        conn.commit()
        conn.close()
        
        manager = SchemaManager(temp_db)
        required_schema = SCHEMA_DEFINITIONS[SchemaVersion.V1_2_ENHANCED]
        issues = manager.validate_schema_compatibility(required_schema)
        
        assert 'customers.first_name' in issues['missing_columns']
        assert 'customers.last_name' in issues['missing_columns']


class TestSchemaAwareConnection:
    """Test schema-aware database operations."""
    
    @pytest.fixture
    def temp_db_with_data(self):
        """Create temporary database with test data."""
        with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as f:
            db_path = f.name
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE accounts (
                account_id TEXT PRIMARY KEY,
                customer_id TEXT,
                account_type TEXT,
                balance DECIMAL(12,2),
                status TEXT DEFAULT 'active'
            )
        """)
        
        cursor.execute("""
            INSERT INTO accounts VALUES 
            ('acc1', 'cust1', 'checking', 1000.0, 'active'),
            ('acc2', 'cust2', 'savings', 2000.0, 'inactive'),
            ('acc3', 'cust3', 'checking', 500.0, 'active')
        """)
        
        conn.commit()
        conn.close()
        
        yield db_path
        Path(db_path).unlink(missing_ok=True)
    
    def test_table_exists_check(self, temp_db_with_data):
        """Test table existence checking with caching."""
        db = SchemaAwareConnection(temp_db_with_data)
        
        assert db.table_exists('accounts') == True
        assert db.table_exists('nonexistent') == False
        
        # Test caching
        assert db._table_cache['accounts'] == True
        assert db._table_cache['nonexistent'] == False
    
    def test_column_exists_check(self, temp_db_with_data):
        """Test column existence checking."""
        db = SchemaAwareConnection(temp_db_with_data)
        
        assert db.column_exists('accounts', 'status') == True
        assert db.column_exists('accounts', 'is_active') == False
        assert db.column_exists('nonexistent_table', 'column') == False
    
    def test_safe_count_operations(self, temp_db_with_data):
        """Test safe counting operations."""
        db = SchemaAwareConnection(temp_db_with_data)
        
        # Count existing table
        assert db.safe_count('accounts') == 3
        
        # Count with WHERE clause
        assert db.safe_count('accounts', "status = ?", ('active',)) == 2
        
        # Count nonexistent table
        assert db.safe_count('nonexistent') == 0
    
    def test_adaptive_query_building(self, temp_db_with_data):
        """Test adaptive query construction."""
        db = SchemaAwareConnection(temp_db_with_data)
        
        # Query with available columns
        query = db.adaptive_query(
            "SELECT {columns} FROM {table}",
            "accounts",
            required_columns=['account_id', 'status'],
            optional_columns={'is_active': 1}
        )
        
        expected = "SELECT account_id, status, '1' as is_active FROM accounts"
        assert query == expected
        
        # Query for nonexistent table
        query = db.adaptive_query(
            "SELECT {columns} FROM {table}",
            "nonexistent",
            required_columns=['id']
        )
        
        assert query is None


class TestSchemaAwareMetrics:
    """Test schema-aware metrics calculations."""
    
    @pytest.fixture
    def mock_connection(self):
        """Mock schema-aware database connection."""
        mock_db = Mock(spec=SchemaAwareConnection)
        return mock_db
    
    def test_account_status_with_status_column(self, mock_connection):
        """Test account status calculation with 'status' column."""
        mock_connection.table_exists.return_value = True
        mock_connection.safe_execute.side_effect = [
            [(2,)],  # Active count
            [(1,)]   # Inactive count
        ]
        
        calculator = SchemaAwareMetricsCalculator(mock_connection)
        result = calculator.calculate_account_status()
        
        assert result == {'active': 2, 'inactive': 1, 'total': 3}
    
    def test_account_status_fallback_to_all_active(self, mock_connection):
        """Test fallback when no status columns exist."""
        mock_connection.table_exists.return_value = True
        # Set up safe_execute to return None for all calls (meaning columns don't exist)
        mock_connection.safe_execute.return_value = None
        mock_connection.safe_count.return_value = 5
        
        calculator = SchemaAwareMetricsCalculator(mock_connection)
        result = calculator.calculate_account_status()
        
        assert result == {'active': 5, 'inactive': 0, 'total': 5}
    
    def test_account_status_no_accounts_table(self, mock_connection):
        """Test handling when accounts table doesn't exist."""
        mock_connection.table_exists.return_value = False
        
        calculator = SchemaAwareMetricsCalculator(mock_connection)
        result = calculator.calculate_account_status()
        
        assert result == {'active': 0, 'inactive': 0, 'total': 0}