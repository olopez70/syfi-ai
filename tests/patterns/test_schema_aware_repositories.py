"""
Tests for schema-aware repository pattern implementations.

Validates that repository patterns work correctly across different database schema versions
while maintaining backward compatibility and providing graceful fallbacks.
"""

import pytest
import sqlite3
import tempfile
import os
from typing import List, Dict, Any

from src.syfi.patterns.repositories import (
    SQLiteCustomerRepository,
    SQLiteAccountRepository, 
    SQLiteTransactionRepository,
    SQLiteUnitOfWork
)
from src.syfi.database import DatabaseManager
from src.syfi.models import Customer, Account, Transaction, AccountType


class TestSchemaAwareRepositories:
    """Test schema-aware repository implementations."""
    
    @pytest.fixture(params=['v1_0_basic', 'v1_1_extended', 'v1_2_enhanced'])
    def schema_database(self, request):
        """Create test databases with different schema versions."""
        with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as f:
            db_path = f.name
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # V1.0 Basic Schema (minimal required tables)
        if request.param == 'v1_0_basic':
            cursor.execute('''
                CREATE TABLE customers (
                    customer_id TEXT PRIMARY KEY,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE accounts (
                    account_id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    account_type TEXT,
                    balance DECIMAL(12,2)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE transactions (
                    transaction_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    transaction_type TEXT,
                    amount DECIMAL(10,2)
                )
            ''')
        
        # V1.1 Extended Schema (adds optional columns)
        elif request.param == 'v1_1_extended':
            cursor.execute('''
                CREATE TABLE customers (
                    customer_id TEXT PRIMARY KEY,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT,
                    household_income DECIMAL(12,2)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE accounts (
                    account_id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    account_type TEXT,
                    balance DECIMAL(12,2),
                    available_balance DECIMAL(12,2),
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE transactions (
                    transaction_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    transaction_type TEXT,
                    amount DECIMAL(10,2),
                    created_date DATE DEFAULT CURRENT_DATE
                )
            ''')
        
        # V1.2 Enhanced Schema (full feature set)
        elif request.param == 'v1_2_enhanced':
            cursor.execute('''
                CREATE TABLE customers (
                    customer_id TEXT PRIMARY KEY,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT,
                    household_income DECIMAL(12,2),
                    profile_description TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE accounts (
                    account_id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    account_type TEXT,
                    balance DECIMAL(12,2),
                    available_balance DECIMAL(12,2),
                    status TEXT DEFAULT 'active'
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE transactions (
                    transaction_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    transaction_type TEXT,
                    amount DECIMAL(10,2),
                    transaction_date DATE DEFAULT CURRENT_DATE
                )
            ''')
        
        # Insert test data consistent across all schemas
        cursor.execute('''
            INSERT INTO customers (customer_id, first_name, last_name, email) 
            VALUES ('c1', 'John', 'Doe', 'john@example.com')
        ''')
        cursor.execute('''
            INSERT INTO customers (customer_id, first_name, last_name, email) 
            VALUES ('c2', 'Jane', 'Smith', 'jane@example.com')
        ''')
        
        cursor.execute('''
            INSERT INTO accounts (account_id, customer_id, account_type, balance) 
            VALUES ('a1', 'c1', 'checking', 1500.00)
        ''')
        cursor.execute('''
            INSERT INTO accounts (account_id, customer_id, account_type, balance) 
            VALUES ('a2', 'c2', 'savings', 2500.00)
        ''')
        
        cursor.execute('''
            INSERT INTO transactions (transaction_id, account_id, transaction_type, amount) 
            VALUES ('t1', 'a1', 'deposit', 100.00)
        ''')
        cursor.execute('''
            INSERT INTO transactions (transaction_id, account_id, transaction_type, amount) 
            VALUES ('t2', 'a2', 'withdrawal', -50.00)
        ''')
        
        # Add extended data for schemas that support it
        if request.param in ['v1_1_extended', 'v1_2_enhanced']:
            cursor.execute('''
                UPDATE customers SET household_income = 75000.00 WHERE customer_id = 'c1'
            ''')
            cursor.execute('''
                UPDATE customers SET household_income = 95000.00 WHERE customer_id = 'c2'
            ''')
        
        if request.param == 'v1_2_enhanced':
            cursor.execute('''
                UPDATE customers SET profile_description = 'young_professional' WHERE customer_id = 'c1'
            ''')
            cursor.execute('''
                UPDATE customers SET profile_description = 'family_oriented' WHERE customer_id = 'c2'
            ''')
        
        conn.commit()
        conn.close()
        
        yield db_path, request.param
        
        # Cleanup
        os.unlink(db_path)
    
    def test_customer_repository_schema_compatibility(self, schema_database):
        """Test customer repository works across schema versions."""
        db_path, schema_version = schema_database
        db_manager = DatabaseManager(db_path)
        
        # Test schema-aware customer repository
        customer_repo = SQLiteCustomerRepository(db_manager)
        
        # Test find_by_id (should work on all schemas)
        customer = customer_repo.find_by_id('c1')
        assert customer is not None
        assert customer.customer_id == 'c1'
        assert customer.first_name == 'John'
        assert customer.last_name == 'Doe'
        assert customer.email == 'john@example.com'
        
        # Test find_all (should work on all schemas)
        all_customers = customer_repo.find_all()
        assert len(all_customers) == 2
        
        # Test count (should work on all schemas)
        count = customer_repo.count()
        assert count == 2
        
        # Test income range query (schema-dependent)
        income_customers = customer_repo.find_by_income_range(70000.00, 100000.00)
        if schema_version == 'v1_0_basic':
            # No income column - should return empty list gracefully
            assert len(income_customers) == 0
        else:
            # Extended/Enhanced schemas have income data
            assert len(income_customers) == 2  # Both customers in range
        
        db_manager.close()
    
    def test_account_repository_schema_compatibility(self, schema_database):
        """Test account repository works across schema versions."""
        db_path, schema_version = schema_database
        db_manager = DatabaseManager(db_path)
        
        # Test schema-aware account repository
        account_repo = SQLiteAccountRepository(db_manager)
        
        # Test find_by_id (should work on all schemas)
        account = account_repo.find_by_id('a1')
        assert account is not None
        assert account.account_id == 'a1'
        assert account.customer_id == 'c1'
        assert account.account_type == AccountType.CHECKING
        assert account.balance == 1500.00
        
        # Test find_by_customer_id (should work on all schemas)
        customer_accounts = account_repo.find_by_customer_id('c1')
        assert len(customer_accounts) == 1
        assert customer_accounts[0].account_id == 'a1'
        
        # Test count (should work on all schemas)
        count = account_repo.count()
        assert count == 2
        
        db_manager.close()
    
    def test_transaction_repository_schema_compatibility(self, schema_database):
        """Test transaction repository works across schema versions."""
        db_path, schema_version = schema_database
        db_manager = DatabaseManager(db_path)
        
        # Test schema-aware transaction repository
        transaction_repo = SQLiteTransactionRepository(db_manager)
        
        # Test find_by_id (should work on all schemas)
        transaction = transaction_repo.find_by_id('t1')
        assert transaction is not None
        assert transaction.transaction_id == 't1'
        assert transaction.account_id == 'a1'
        assert transaction.amount == 100.00
        
        # Test find_by_account_id with adaptive ordering (should work on all schemas)
        account_transactions = transaction_repo.find_by_account_id('a1')
        assert len(account_transactions) == 1
        assert account_transactions[0].transaction_id == 't1'
        
        # Test count (should work on all schemas)
        count = transaction_repo.count()
        assert count == 2
        
        db_manager.close()
    
    def test_unit_of_work_schema_compatibility(self, schema_database):
        """Test unit of work pattern with schema-aware repositories."""
        db_path, schema_version = schema_database
        db_manager = DatabaseManager(db_path)
        
        # Test schema-aware unit of work
        with SQLiteUnitOfWork(db_manager) as uow:
            # Test that all repositories are initialized properly
            assert uow.customers is not None
            assert uow.accounts is not None
            assert uow.transactions is not None
            assert uow.profiles is not None
            
            # Test cross-repository operations
            customer = uow.customers.find_by_id('c1')
            customer_accounts = uow.accounts.find_by_customer_id('c1')
            account_transactions = uow.transactions.find_by_account_id('a1')
            
            assert customer is not None
            assert len(customer_accounts) == 1
            assert len(account_transactions) == 1
            
            # Validate data consistency
            assert customer_accounts[0].customer_id == customer.customer_id
            assert account_transactions[0].account_id == customer_accounts[0].account_id
        
        db_manager.close()
    
    def test_repository_performance(self, schema_database):
        """Test that schema-aware operations don't significantly impact performance."""
        import time
        
        db_path, schema_version = schema_database
        db_manager = DatabaseManager(db_path)
        
        # Measure repository operation performance
        start_time = time.time()
        
        with SQLiteUnitOfWork(db_manager) as uow:
            # Perform various operations
            for _ in range(10):
                customers = uow.customers.find_all()
                accounts = uow.accounts.find_all()
                transactions = uow.transactions.find_all()
                
                customer_count = uow.customers.count()
                account_count = uow.accounts.count()
                transaction_count = uow.transactions.count()
        
        elapsed_time = time.time() - start_time
        
        # Should complete operations within reasonable time (less than 1 second)
        assert elapsed_time < 1.0, f"Repository operations took too long: {elapsed_time:.3f}s"
        
        db_manager.close()
    
    def test_legacy_compatibility(self, schema_database):
        """Test that repositories still work with legacy db_manager initialization."""
        db_path, schema_version = schema_database
        db_manager = DatabaseManager(db_path)
        
        # Test direct initialization with db_manager (legacy mode)
        customer_repo = SQLiteCustomerRepository(db_manager)
        account_repo = SQLiteAccountRepository(db_manager)  
        transaction_repo = SQLiteTransactionRepository(db_manager)
        
        # These should work even if schema-aware features aren't available
        customer = customer_repo.find_by_id('c1')
        account = account_repo.find_by_id('a1')
        transaction = transaction_repo.find_by_id('t1')
        
        assert customer is not None
        assert account is not None
        assert transaction is not None
        
        db_manager.close()


if __name__ == "__main__":
    # Quick validation test
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as f:
        test_db = f.name
    
    # Create basic schema
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE customers (
            customer_id TEXT PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT
        )
    ''')
    
    cursor.execute('''
        INSERT INTO customers VALUES ('c1', 'Test', 'User', 'test@example.com')
    ''')
    
    conn.commit()
    conn.close()
    
    # Test schema-aware repository
    from src.syfi.database import DatabaseManager
    
    db_manager = DatabaseManager(test_db)
    customer_repo = SQLiteCustomerRepository(db_manager)
    
    customer = customer_repo.find_by_id('c1')
    print(f"✅ Schema-aware repository test: {customer.first_name if customer else 'Failed'}")
    
    # Cleanup
    db_manager.close()
    os.unlink(test_db)