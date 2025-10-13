"""
Multi-schema compatibility tests for profiling components.

Tests profiling functionality across different database schema versions to ensure
graceful handling of missing tables/columns and consistent behavior.
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import Mock

from src.syfi.profiling.analyzer import BankingDataProfiler
from src.syfi.profiling.banking_metrics import BankingMetricsCalculator
from src.syfi.schema_management import SchemaVersion, SCHEMA_DEFINITIONS


class TestProfilingSchemaCompatibility:
    """Test profiling components work with different database schemas."""
    
    @pytest.fixture(params=[
        SchemaVersion.V1_0_BASIC,
        SchemaVersion.V1_1_EXTENDED, 
        SchemaVersion.V1_2_ENHANCED
    ])
    def schema_database(self, request):
        """Create test database with specific schema version."""
        schema_version = request.param
        
        with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as f:
            db_path = f.name
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create schema manually based on version (simpler approach)
        if schema_version == SchemaVersion.V1_0_BASIC:
            # Basic schema: customers + accounts (minimal columns)
            cursor.execute("""
                CREATE TABLE customers (
                    customer_id TEXT PRIMARY KEY,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE accounts (
                    account_id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    account_type TEXT,
                    balance DECIMAL(12,2)
                )
            """)
        elif schema_version == SchemaVersion.V1_1_EXTENDED:
            # Extended schema: + transactions table
            cursor.execute("""
                CREATE TABLE customers (
                    customer_id TEXT PRIMARY KEY,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE accounts (
                    account_id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    account_type TEXT,
                    balance DECIMAL(12,2)
                )
            """)
            cursor.execute("""
                CREATE TABLE transactions (
                    transaction_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    transaction_type TEXT,
                    amount DECIMAL(10,2),
                    transaction_date DATE DEFAULT CURRENT_DATE
                )
            """)
        elif schema_version == SchemaVersion.V1_2_ENHANCED:
            # Enhanced schema: + optional columns (status, profile_description)
            cursor.execute("""
                CREATE TABLE customers (
                    customer_id TEXT PRIMARY KEY,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT,
                    profile_description TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE accounts (
                    account_id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    account_type TEXT,
                    balance DECIMAL(12,2),
                    status TEXT DEFAULT 'active'
                )
            """)
            cursor.execute("""
                CREATE TABLE transactions (
                    transaction_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    transaction_type TEXT,
                    amount DECIMAL(10,2),
                    transaction_date DATE DEFAULT CURRENT_DATE
                )
            """)
        
        # Insert test data appropriate for schema version
        customer_data = [
            ('cust1', 'John', 'Doe'),
            ('cust2', 'Jane', 'Smith'),
            ('cust3', 'Bob', 'Johnson')
        ]
        
        if schema_version == SchemaVersion.V1_2_ENHANCED:
            # Enhanced schema has additional columns
            cursor.executemany("""
                INSERT INTO customers (customer_id, first_name, last_name, email, profile_description) 
                VALUES (?, ?, ?, ? || '@example.com', 'profile_' || ?)
            """, [(c[0], c[1], c[2], c[1].lower(), c[0]) for c in customer_data])
        elif schema_version == SchemaVersion.V1_1_EXTENDED:
            # Extended schema has email but no profile_description
            cursor.executemany("""
                INSERT INTO customers (customer_id, first_name, last_name, email) 
                VALUES (?, ?, ?, ? || '@example.com')
            """, [(c[0], c[1], c[2], c[1].lower()) for c in customer_data])
        else:
            # Basic schema
            cursor.executemany("""
                INSERT INTO customers (customer_id, first_name, last_name) 
                VALUES (?, ?, ?)
            """, customer_data)
        
        # Insert account data
        account_data = [
            ('acc1', 'cust1', 'checking', 1500.00),
            ('acc2', 'cust2', 'savings', 2500.00),
            ('acc3', 'cust3', 'checking', 500.00),
            ('acc4', 'cust1', 'savings', 5000.00)
        ]
        
        if schema_version == SchemaVersion.V1_2_ENHANCED:
            # Enhanced schema has status column
            cursor.executemany("""
                INSERT INTO accounts (account_id, customer_id, account_type, balance, status) 
                VALUES (?, ?, ?, ?, ?)
            """, [(a[0], a[1], a[2], a[3], 'active' if a[3] > 1000 else 'inactive') for a in account_data])
        else:
            # Basic schema without status
            cursor.executemany("""
                INSERT INTO accounts (account_id, customer_id, account_type, balance) 
                VALUES (?, ?, ?, ?)
            """, account_data)
        
        # Insert transaction data (only for V1.1+ schemas)
        if schema_version in [SchemaVersion.V1_1_EXTENDED, SchemaVersion.V1_2_ENHANCED]:
            transaction_data = [
                ('txn1', 'acc1', 'deposit', 100.00),
                ('txn2', 'acc2', 'withdrawal', -50.00),
                ('txn3', 'acc1', 'transfer', -200.00),
                ('txn4', 'acc3', 'deposit', 75.00)
            ]
            cursor.executemany("""
                INSERT INTO transactions (transaction_id, account_id, transaction_type, amount) 
                VALUES (?, ?, ?, ?)
            """, transaction_data)
        
        conn.commit()
        conn.close()
        
        yield db_path, schema_version
        
        # Cleanup
        Path(db_path).unlink(missing_ok=True)
    
    def test_banking_metrics_calculator_schema_compatibility(self, schema_database):
        """Test BankingMetricsCalculator works with different schemas."""
        db_path, schema_version = schema_database
        
        # Test schema-aware initialization
        calculator = BankingMetricsCalculator(db_path)
        
        # Test account metrics calculation
        account_metrics = calculator._calculate_account_metrics()
        
        # Basic assertions that should work for all schemas
        assert 'total_accounts' in account_metrics
        assert account_metrics['total_accounts'] >= 0
        assert 'account_type_distribution' in account_metrics
        assert 'account_status' in account_metrics
        
        # Enhanced schema should have more detailed account status
        if schema_version == SchemaVersion.V1_2_ENHANCED:
            status = account_metrics['account_status']
            assert status['total'] == account_metrics['total_accounts']
            assert status['active'] + status['inactive'] == status['total']
        else:
            # Basic schemas should default to all active
            status = account_metrics['account_status'] 
            assert status['active'] == account_metrics['total_accounts']
            assert status['inactive'] == 0
        
        # Test transaction analysis
        transaction_metrics = calculator._analyze_transactions()
        
        if schema_version == SchemaVersion.V1_0_BASIC:
            # No transactions table in basic schema
            assert transaction_metrics.get('message') == 'No transactions table found'
        else:
            # Should have transaction data
            assert 'total_transactions' in transaction_metrics or 'message' in transaction_metrics
    
    def test_banking_data_profiler_schema_compatibility(self, schema_database):
        """Test BankingDataProfiler works with different schemas."""
        db_path, schema_version = schema_database
        
        with BankingDataProfiler(db_path) as profiler:
            # Test summary generation
            summary = profiler._generate_summary()
            
            # Basic assertions for all schemas
            assert summary.total_customers >= 0
            assert summary.total_accounts >= 0
            assert summary.total_transactions >= 0
            assert summary.database_size_kb > 0
            
            # Schema-specific assertions
            if schema_version == SchemaVersion.V1_0_BASIC:
                assert summary.total_transactions == 0  # No transactions table
                assert summary.unique_profiles == 0  # No profile_description column
            elif schema_version == SchemaVersion.V1_1_EXTENDED:
                assert summary.total_transactions >= 0  # Has transactions table
                assert summary.unique_profiles == 0  # Still no profile_description
            elif schema_version == SchemaVersion.V1_2_ENHANCED:
                assert summary.total_transactions >= 0  # Has transactions
                assert summary.unique_profiles >= 0  # Has profile_description
            
            # Test banking metrics integration
            banking_metrics = profiler._calculate_banking_metrics()
            assert 'account_stats' in banking_metrics
            assert 'transaction_stats' in banking_metrics
            
            # Verify account stats work for all schemas
            account_stats = banking_metrics['account_stats']
            assert account_stats['total_accounts'] >= 0
            assert 'account_status' in account_stats
    
    def test_profiler_table_column_existence_checks(self, schema_database):
        """Test profiler's schema awareness methods."""
        db_path, schema_version = schema_database
        
        with BankingDataProfiler(db_path) as profiler:
            # Test table existence - should work for all schemas
            assert profiler._table_exists('customers') == True
            assert profiler._table_exists('accounts') == True
            
            # Transactions table only exists in V1.1_EXTENDED+
            if schema_version == SchemaVersion.V1_0_BASIC:
                assert profiler._table_exists('transactions') == False
            else:
                assert profiler._table_exists('transactions') == True
            
            # Non-existent table
            assert profiler._table_exists('nonexistent') == False
            
            # Test column existence
            assert profiler._column_exists('customers', 'customer_id') == True
            assert profiler._column_exists('customers', 'first_name') == True
            
            # Optional columns based on schema version
            if schema_version == SchemaVersion.V1_2_ENHANCED:
                assert profiler._column_exists('customers', 'profile_description') == True
                assert profiler._column_exists('accounts', 'status') == True
            else:
                assert profiler._column_exists('customers', 'profile_description') == False
                assert profiler._column_exists('accounts', 'status') == False
            
            # Non-existent columns
            assert profiler._column_exists('customers', 'nonexistent_column') == False
    
    def test_backward_compatibility_with_legacy_initialization(self):
        """Test that legacy connection-based initialization still works."""
        # Create test database
        with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as f:
            db_path = f.name
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE accounts (
                account_id TEXT PRIMARY KEY,
                balance DECIMAL(12,2),
                account_type TEXT,
                status TEXT DEFAULT 'active'
            )
        """)
        
        cursor.execute("""
            INSERT INTO accounts VALUES 
            ('acc1', 1000.00, 'checking', 'active'),
            ('acc2', 2000.00, 'savings', 'inactive')
        """)
        
        conn.commit()
        conn.close()
        
        # Test legacy initialization
        conn = sqlite3.connect(db_path)
        legacy_calculator = BankingMetricsCalculator(conn)
        
        # Should still work
        metrics = legacy_calculator._calculate_account_metrics()
        assert metrics['total_accounts'] == 2
        assert 'account_status' in metrics
        
        conn.close()
        Path(db_path).unlink()
    
    def test_performance_impact_of_schema_awareness(self, schema_database):
        """Test that schema-aware operations don't significantly impact performance."""
        db_path, schema_version = schema_database
        
        import time
        
        # Time schema-aware operations
        start_time = time.time()
        
        with BankingDataProfiler(db_path) as profiler:
            # Perform multiple schema checks (simulating real usage)
            for _ in range(10):
                profiler._table_exists('customers')
                profiler._table_exists('accounts') 
                profiler._table_exists('transactions')
                profiler._column_exists('accounts', 'status')
                profiler._column_exists('customers', 'profile_description')
            
            # Generate summary and metrics
            summary = profiler._generate_summary()
            banking_metrics = profiler._calculate_banking_metrics()
        
        schema_aware_time = time.time() - start_time
        
        # The operations should complete quickly (< 1 second for this test)
        assert schema_aware_time < 1.0, f"Schema-aware operations took {schema_aware_time:.3f}s (too slow)"
        
        # Note: In real usage, schema metadata is cached, so subsequent operations are very fast


class TestProfilingErrorHandling:
    """Test profiling components handle edge cases gracefully."""
    
    def test_empty_database_handling(self):
        """Test profilers handle empty databases gracefully."""
        with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as f:
            db_path = f.name
        
        # Create empty database
        conn = sqlite3.connect(db_path)
        conn.close()
        
        # Test BankingMetricsCalculator with empty database
        calculator = BankingMetricsCalculator(db_path)
        account_metrics = calculator._calculate_account_metrics()
        
        # Should return sensible defaults
        assert account_metrics['total_accounts'] == 0
        assert account_metrics['account_status']['active'] == 0
        assert account_metrics['account_status']['inactive'] == 0
        
        # Test BankingDataProfiler with empty database
        with BankingDataProfiler(db_path) as profiler:
            summary = profiler._generate_summary()
            assert summary.total_customers == 0
            assert summary.total_accounts == 0
            assert summary.total_transactions == 0
        
        Path(db_path).unlink()
    
    def test_missing_optional_columns_handling(self):
        """Test handling of databases missing optional columns."""
        with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as f:
            db_path = f.name
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create minimal schema without optional columns
        cursor.execute("""
            CREATE TABLE customers (
                customer_id TEXT PRIMARY KEY,
                first_name TEXT,
                last_name TEXT
                -- Missing: email, profile_description
            )
        """)
        
        cursor.execute("""
            CREATE TABLE accounts (
                account_id TEXT PRIMARY KEY,
                customer_id TEXT,
                account_type TEXT,
                balance DECIMAL(12,2)
                -- Missing: status
            )
        """)
        
        cursor.execute("INSERT INTO customers VALUES ('cust1', 'John', 'Doe')")
        cursor.execute("INSERT INTO accounts VALUES ('acc1', 'cust1', 'checking', 1000.00)")
        
        conn.commit()
        conn.close()
        
        # Test profiling with missing optional columns
        with BankingDataProfiler(db_path) as profiler:
            summary = profiler._generate_summary()
            assert summary.total_customers == 1
            assert summary.total_accounts == 1
            assert summary.unique_profiles == 0  # No profile_description column
            
            banking_metrics = profiler._calculate_banking_metrics()
            account_stats = banking_metrics['account_stats']
            
            # Should handle missing status column gracefully
            assert account_stats['total_accounts'] == 1
            account_status = account_stats['account_status']
            assert account_status['active'] == 1  # Default to active
            assert account_status['inactive'] == 0
        
        Path(db_path).unlink()