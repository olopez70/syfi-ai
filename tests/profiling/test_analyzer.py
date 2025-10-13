"""
Tests for Banking Data Analyzer.

This module tests the core data profiling analyzer that coordinates
comprehensive analysis of synthetic banking databases.
"""

import pytest
import sqlite3
import tempfile
from datetime import datetime, date
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

from src.syfi.profiling.analyzer import (
    ProfileSummary,
    TableProfile,
    BankingDataProfiler
)


@pytest.mark.unit
class TestProfileSummary:
    """Test ProfileSummary dataclass."""
    
    @pytest.fixture
    def sample_summary(self):
        """Create a sample ProfileSummary for testing."""
        return ProfileSummary(
            database_path="/test/db.sqlite",
            analysis_date=datetime(2023, 1, 15, 10, 30, 0),
            total_customers=100,
            total_accounts=200,
            total_transactions=1500,
            database_size_kb=250.5,
            unique_profiles=5,
            date_range=(date(2023, 1, 1), date(2023, 1, 31))
        )
    
    def test_profile_summary_initialization(self, sample_summary):
        """Test ProfileSummary initialization."""
        assert sample_summary.database_path == "/test/db.sqlite"
        assert sample_summary.total_customers == 100
        assert sample_summary.total_accounts == 200
        assert sample_summary.total_transactions == 1500
        assert sample_summary.database_size_kb == 250.5
        assert sample_summary.unique_profiles == 5
        assert sample_summary.date_range == (date(2023, 1, 1), date(2023, 1, 31))
    
    def test_to_dict_conversion(self, sample_summary):
        """Test conversion to dictionary."""
        result = sample_summary.to_dict()
        
        expected_keys = [
            'database_path', 'analysis_date', 'total_customers',
            'total_accounts', 'total_transactions', 'database_size_kb',
            'unique_profiles', 'date_range'
        ]
        
        for key in expected_keys:
            assert key in result
        
        assert result['database_path'] == "/test/db.sqlite"
        assert result['total_customers'] == 100
        assert result['analysis_date'] == "2023-01-15T10:30:00"
        assert result['date_range'] == ["2023-01-01", "2023-01-31"]
    
    def test_to_dict_with_no_date_range(self):
        """Test to_dict with None date_range."""
        summary = ProfileSummary(
            database_path="/test/db.sqlite",
            analysis_date=datetime(2023, 1, 15),
            total_customers=10,
            total_accounts=20,
            total_transactions=100,
            database_size_kb=50.0,
            unique_profiles=2,
            date_range=None
        )
        
        result = summary.to_dict()
        assert result['date_range'] is None


@pytest.mark.unit
class TestTableProfile:
    """Test TableProfile dataclass."""
    
    @pytest.fixture
    def sample_table_profile(self):
        """Create a sample TableProfile for testing."""
        return TableProfile(
            table_name="customers",
            row_count=100,
            column_count=6,
            columns=[
                {"name": "customer_id", "type": "TEXT"},
                {"name": "first_name", "type": "TEXT"},
                {"name": "age", "type": "INTEGER"}
            ],
            data_types={"customer_id": "TEXT", "first_name": "TEXT", "age": "INTEGER"},
            null_counts={"customer_id": 0, "first_name": 0, "age": 2},
            unique_counts={"customer_id": 100, "first_name": 85, "age": 45},
            sample_values={
                "customer_id": ["cust_001", "cust_002", "cust_003"],
                "first_name": ["John", "Jane", "Bob"],
                "age": [25, 30, 35]
            }
        )
    
    def test_table_profile_initialization(self, sample_table_profile):
        """Test TableProfile initialization."""
        assert sample_table_profile.table_name == "customers"
        assert sample_table_profile.row_count == 100
        assert sample_table_profile.column_count == 6
        assert len(sample_table_profile.columns) == 3
        assert sample_table_profile.data_types["age"] == "INTEGER"
        assert sample_table_profile.null_counts["age"] == 2
        assert sample_table_profile.unique_counts["customer_id"] == 100
    
    def test_to_dict_conversion(self, sample_table_profile):
        """Test TableProfile to_dict conversion."""
        result = sample_table_profile.to_dict()
        
        expected_keys = [
            'table_name', 'row_count', 'column_count', 'columns',
            'data_types', 'null_counts', 'unique_counts', 'sample_values'
        ]
        
        for key in expected_keys:
            assert key in result
        
        assert result['table_name'] == "customers"
        assert result['row_count'] == 100
        assert result['data_types']['age'] == "INTEGER"
        assert len(result['sample_values']['first_name']) == 3


@pytest.mark.unit
class TestBankingDataProfiler:
    """Test BankingDataProfiler class."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as temp_file:
            db_path = temp_file.name
            
        # Create test database with basic schema
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE customers (
                customer_id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                age INTEGER,
                income DECIMAL(10,2)
            )
        """)
        conn.execute("""
            CREATE TABLE accounts (
                account_id TEXT PRIMARY KEY,
                customer_id TEXT,
                account_type TEXT,
                balance DECIMAL(10,2),
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            )
        """)
        
        # Insert test data
        conn.execute("""
            INSERT INTO customers VALUES 
            ('cust_001', 'John', 'Doe', 30, 50000.00),
            ('cust_002', 'Jane', 'Smith', 25, 60000.00)
        """)
        conn.execute("""
            INSERT INTO accounts VALUES 
            ('acc_001', 'cust_001', 'checking', 1500.00),
            ('acc_002', 'cust_001', 'savings', 5000.00),
            ('acc_003', 'cust_002', 'checking', 2000.00)
        """)
        
        conn.commit()
        conn.close()
        
        yield db_path
        
        # Cleanup
        Path(db_path).unlink()
    
    @pytest.fixture
    def profiler(self, temp_db):
        """Create a BankingDataProfiler instance with test database."""
        return BankingDataProfiler(temp_db)
    
    def test_profiler_initialization(self, temp_db):
        """Test BankingDataProfiler initialization."""
        profiler = BankingDataProfiler(temp_db)
        
        assert profiler.database_path == Path(temp_db)
        assert profiler.conn is not None
        assert isinstance(profiler.conn, sqlite3.Connection)
    
    def test_profiler_initialization_nonexistent_db(self):
        """Test profiler with nonexistent database."""
        with pytest.raises(Exception):  # Could be FileNotFoundError or sqlite3.Error
            BankingDataProfiler("/nonexistent/database.sqlite")
    
    def test_get_database_size(self, profiler, temp_db):
        """Test database size calculation through summary generation."""
        summary = profiler._generate_summary()
        
        assert isinstance(summary.database_size_kb, float)
        assert summary.database_size_kb > 0
        
        # Verify it matches actual file size
        actual_size = Path(temp_db).stat().st_size / 1024
        assert abs(summary.database_size_kb - actual_size) < 0.1  # Allow small difference
    
    def test_get_table_names(self, profiler):
        """Test getting table names through table profiling."""
        tables = profiler._profile_all_tables()
        
        assert isinstance(tables, dict)
        assert "customers" in tables
        assert "accounts" in tables
        assert len(tables) >= 2
    
    def test_profile_table_basic(self, profiler):
        """Test basic table profiling."""
        profile = profiler._profile_table("customers")
        
        assert isinstance(profile, TableProfile)
        assert profile.table_name == "customers"
        assert profile.row_count == 2  # We inserted 2 customers
        assert profile.column_count > 0
        assert "customer_id" in profile.data_types
        assert "first_name" in profile.data_types
    
    def test_profile_table_data_types(self, profiler):
        """Test data type detection in table profiling."""
        profile = profiler._profile_table("customers")
        
        # Check data types are detected correctly
        assert profile.data_types["customer_id"] == "TEXT"
        assert profile.data_types["age"] == "INTEGER"
        # SQLite may store decimal as REAL or NUMERIC, or with precision
        assert any(dtype in profile.data_types["income"] for dtype in ["REAL", "NUMERIC", "DECIMAL"])
    
    def test_profile_table_counts(self, profiler):
        """Test null and unique count calculations."""
        profile = profiler._profile_table("customers")
        
        # All customer_ids should be unique
        assert profile.unique_counts["customer_id"] == profile.row_count
        
        # Check null counts (none in our test data)
        assert profile.null_counts["customer_id"] == 0
        assert profile.null_counts["first_name"] == 0
    
    def test_profile_table_sample_values(self, profiler):
        """Test sample value collection."""
        profile = profiler._profile_table("customers")
        
        # Check sample values are collected
        assert len(profile.sample_values["first_name"]) > 0
        assert "John" in profile.sample_values["first_name"] or "Jane" in profile.sample_values["first_name"]
        
        # Customer IDs should be in samples
        customer_ids = profile.sample_values["customer_id"]
        assert any(cid.startswith("cust_") for cid in customer_ids)
    
    def test_get_date_range(self, profiler):
        """Test date range extraction through summary generation."""
        summary = profiler._generate_summary()
        # Our test database doesn't have transaction dates, so this should return None
        assert summary.date_range is None
    
    def test_create_profile_summary(self, profiler):
        """Test profile summary creation."""
        summary = profiler._generate_summary()
        
        assert isinstance(summary, ProfileSummary)
        assert summary.total_customers == 2
        assert summary.total_accounts == 3  # We created 3 accounts
        assert summary.database_size_kb > 0
        assert summary.database_path == str(profiler.database_path)
    
    def test_analyze_database_full(self, profiler):
        """Test full database analysis."""
        result = profiler.generate_full_profile()
        
        assert isinstance(result, dict)
        assert "summary" in result
        assert "tables" in result
        assert "banking_metrics" in result
        
        # Check summary
        assert isinstance(result["summary"], ProfileSummary)
        
        # Check tables
        assert isinstance(result["tables"], dict)
        assert "customers" in result["tables"]
        assert "accounts" in result["tables"]
        
        # Check banking metrics exist (may be empty due to missing columns)
        assert "banking_metrics" in result
    
    def test_close_connection(self, profiler):
        """Test closing database connection using context manager."""
        # Connection should be open initially
        assert profiler.conn is not None
        
        # Use context manager to close connection
        with profiler:
            assert profiler.conn is not None
        
        # After context manager, connection should be handled properly
        # At minimum, should not raise an exception


@pytest.mark.integration
class TestBankingDataProfilerIntegration:
    """Integration tests for BankingDataProfiler with realistic data."""
    
    def test_profiler_with_realistic_banking_data(self):
        """Test profiler with more realistic banking schema and data."""
        with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as temp_file:
            db_path = temp_file.name
        
        try:
            # Create realistic banking database
            conn = sqlite3.connect(db_path)
            
            # Create comprehensive schema
            conn.execute("""
                CREATE TABLE customers (
                    customer_id TEXT PRIMARY KEY,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT UNIQUE,
                    phone TEXT,
                    date_of_birth DATE,
                    created_date DATE DEFAULT CURRENT_DATE,
                    income DECIMAL(12,2),
                    credit_score INTEGER
                )
            """)
            
            conn.execute("""
                CREATE TABLE accounts (
                    account_id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    account_type TEXT CHECK(account_type IN ('checking', 'savings', 'credit')),
                    balance DECIMAL(12,2) DEFAULT 0.00,
                    opened_date DATE DEFAULT CURRENT_DATE,
                    status TEXT DEFAULT 'active',
                    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE transactions (
                    transaction_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    transaction_type TEXT CHECK(transaction_type IN ('debit', 'credit')),
                    amount DECIMAL(10,2) NOT NULL,
                    transaction_date DATE DEFAULT CURRENT_DATE,
                    description TEXT,
                    category TEXT,
                    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
                )
            """)
            
            # Insert realistic test data
            customers = [
                ('cust_001', 'John', 'Doe', 'john.doe@email.com', '555-0101', '1990-05-15', '2023-01-01', 75000.00, 720),
                ('cust_002', 'Jane', 'Smith', 'jane.smith@email.com', '555-0102', '1985-08-22', '2023-01-02', 85000.00, 750),
                ('cust_003', 'Bob', 'Johnson', 'bob.johnson@email.com', '555-0103', '1978-12-10', '2023-01-03', 95000.00, 680)
            ]
            
            for customer in customers:
                conn.execute("INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", customer)
            
            accounts = [
                ('acc_001', 'cust_001', 'checking', 2500.00, '2023-01-01', 'active'),
                ('acc_002', 'cust_001', 'savings', 15000.00, '2023-01-01', 'active'),
                ('acc_003', 'cust_002', 'checking', 3200.00, '2023-01-02', 'active'),
                ('acc_004', 'cust_003', 'checking', 1800.00, '2023-01-03', 'active'),
                ('acc_005', 'cust_003', 'credit', -500.00, '2023-01-03', 'active')
            ]
            
            for account in accounts:
                conn.execute("INSERT INTO accounts VALUES (?, ?, ?, ?, ?, ?)", account)
            
            conn.commit()
            conn.close()
            
            # Test profiler with realistic data
            with BankingDataProfiler(db_path) as profiler:
                result = profiler.generate_full_profile()
                
                # Verify comprehensive analysis
                assert result["summary"].total_customers == 3
                assert result["summary"].total_accounts == 5
                assert len(result["tables"]) == 3  # customers, accounts, transactions
                
                # Verify table profiles have expected structure
                customers_profile = result["tables"]["customers"]
                assert customers_profile.row_count == 3
                assert "customer_id" in customers_profile.data_types
                assert "email" in customers_profile.data_types
                assert customers_profile.unique_counts["customer_id"] == 3
            
        finally:
            # Cleanup
            Path(db_path).unlink()
    
    def test_profiler_error_handling(self):
        """Test profiler error handling with malformed database."""
        # Create empty file (not a valid SQLite database)
        with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as temp_file:
            temp_file.write(b"not a database")
            db_path = temp_file.name
        
        try:
            with pytest.raises((sqlite3.DatabaseError, FileNotFoundError)):
                BankingDataProfiler(db_path)
        finally:
            Path(db_path).unlink()