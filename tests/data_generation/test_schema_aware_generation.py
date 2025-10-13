"""
Tests for schema-aware data generation components.

Validates that data generation components work correctly across different database 
schema versions while maintaining backward compatibility.
"""

import pytest
import sqlite3
import tempfile
import os
from typing import List, Dict, Any
from datetime import date, datetime

from src.syfi.profile_builder import ProfileBuilder, BankingDataGenerator
from src.syfi.patterns.observers import ObservableDataGenerator, DatabaseEventLogger
from src.syfi.database import DatabaseManager
from src.syfi.models import Profile, Customer, Account, Transaction


class TestSchemaAwareDataGeneration:
    """Test schema-aware data generation implementations."""
    
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
                    household_income DECIMAL(12,2),
                    household_size INTEGER DEFAULT 1,
                    employment_status TEXT DEFAULT 'employed'
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
                    description TEXT,
                    category TEXT DEFAULT 'other',
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
                    phone TEXT,
                    household_income DECIMAL(12,2),
                    household_size INTEGER DEFAULT 1,
                    employment_status TEXT DEFAULT 'employed',
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
                    description TEXT,
                    category TEXT DEFAULT 'other',
                    transaction_date DATE DEFAULT CURRENT_DATE,
                    merchant_name TEXT,
                    balance_after DECIMAL(12,2)
                )
            ''')
        
        conn.commit()
        conn.close()
        
        yield db_path, request.param
        
        # Cleanup
        os.unlink(db_path)
    
    def test_profile_builder_schema_compatibility(self, schema_database):
        """Test ProfileBuilder works across schema versions."""
        db_path, schema_version = schema_database
        db_manager = DatabaseManager(db_path)
        
        # Test schema-aware profile builder
        profile_builder = ProfileBuilder(db_manager, seed=12345)
        
        # Verify schema-aware connection is initialized
        assert hasattr(profile_builder, '_schema_db')
        
        # ProfileBuilder should work even without profile tables initially
        # (it creates them as needed)
        print(f"✅ ProfileBuilder initialized for schema: {schema_version}")
        
        db_manager.close()
    
    def test_banking_data_generator_schema_compatibility(self, schema_database):
        """Test BankingDataGenerator works across schema versions."""
        db_path, schema_version = schema_database
        db_manager = DatabaseManager(db_path)
        
        # Test schema-aware banking data generator
        data_generator = BankingDataGenerator(db_manager)
        
        # Verify schema-aware connection is initialized
        assert hasattr(data_generator, '_schema_db')
        assert data_generator._schema_db is not None
        
        # Test schema detection
        schema_db = data_generator._schema_db
        assert schema_db.table_exists('customers')
        assert schema_db.table_exists('accounts')
        assert schema_db.table_exists('transactions')
        
        print(f"✅ BankingDataGenerator initialized for schema: {schema_version}")
        print(f"✅ Schema tables detected: customers, accounts, transactions")
        
        db_manager.close()
    
    def test_observable_data_generator_schema_compatibility(self, schema_database):
        """Test ObservableDataGenerator works across schema versions."""
        db_path, schema_version = schema_database
        db_manager = DatabaseManager(db_path)
        
        # Test schema-aware observable data generator
        observable_gen = ObservableDataGenerator(db_manager)
        
        # Verify schema-aware connection is initialized
        assert hasattr(observable_gen, '_schema_db')
        assert observable_gen._schema_db is not None
        
        # Test schema detection
        schema_db = observable_gen._schema_db
        assert schema_db.table_exists('customers')
        assert schema_db.table_exists('accounts')
        assert schema_db.table_exists('transactions')
        
        print(f"✅ ObservableDataGenerator initialized for schema: {schema_version}")
        
        db_manager.close()
    
    def test_database_event_logger_schema_compatibility(self, schema_database):
        """Test DatabaseEventLogger works across schema versions."""
        db_path, schema_version = schema_database
        db_manager = DatabaseManager(db_path)
        
        # Test schema-aware database event logger
        event_logger = DatabaseEventLogger(db_manager)
        
        # Verify schema-aware connection is initialized
        assert hasattr(event_logger, '_schema_db')
        assert event_logger._schema_db is not None
        
        # Test that events table is created
        schema_db = event_logger._schema_db
        assert schema_db.table_exists('generation_events')
        
        # Test logging an event
        from src.syfi.patterns.observers import GenerationEvent, GenerationEventData
        
        test_event = GenerationEventData(
            GenerationEvent.PROFILE_CREATED,
            {
                'profile_name': 'test_profile',
                'schema_version': schema_version,
                'test': True
            }
        )
        
        # This should work without errors
        event_logger.update(test_event)
        
        # Verify event was logged
        events = schema_db.safe_execute("SELECT * FROM generation_events")
        assert len(events) == 1
        assert events[0]['event_type'] == 'profile_created'
        
        print(f"✅ DatabaseEventLogger working for schema: {schema_version}")
        print(f"✅ Event logged: {events[0]['event_type']}")
        
        db_manager.close()
    
    def test_data_generation_performance(self, schema_database):
        """Test that schema-aware operations don't significantly impact performance."""
        import time
        
        db_path, schema_version = schema_database
        db_manager = DatabaseManager(db_path)
        
        # Measure data generation performance
        start_time = time.time()
        
        # Initialize all data generation components
        profile_builder = ProfileBuilder(db_manager, seed=12345)
        data_generator = BankingDataGenerator(db_manager)
        observable_gen = ObservableDataGenerator(db_manager)
        event_logger = DatabaseEventLogger(db_manager)
        
        # Perform various operations
        for _ in range(5):
            # Test schema checks (these should be cached)
            schema_db = data_generator._schema_db
            tables_exist = [
                schema_db.table_exists('customers'),
                schema_db.table_exists('accounts'),
                schema_db.table_exists('transactions')
            ]
            assert all(tables_exist)
        
        elapsed_time = time.time() - start_time
        
        # Should complete operations within reasonable time (less than 1 second)
        assert elapsed_time < 1.0, f"Data generation operations took too long: {elapsed_time:.3f}s"
        
        print(f"✅ Performance test passed: {elapsed_time:.3f}s for {schema_version}")
        
        db_manager.close()
    
    def test_schema_compatibility_features(self, schema_database):
        """Test schema-specific feature compatibility."""
        db_path, schema_version = schema_database
        db_manager = DatabaseManager(db_path)
        
        data_generator = BankingDataGenerator(db_manager)
        schema_db = data_generator._schema_db
        
        print(f"\\n🔍 Schema Feature Analysis: {schema_version}")
        
        # Test customer table features
        customer_features = {
            'email': schema_db.column_exists('customers', 'email'),
            'phone': schema_db.column_exists('customers', 'phone'),
            'household_income': schema_db.column_exists('customers', 'household_income'),
            'household_size': schema_db.column_exists('customers', 'household_size'),
            'employment_status': schema_db.column_exists('customers', 'employment_status'),
            'profile_description': schema_db.column_exists('customers', 'profile_description')
        }
        
        # Test account table features
        account_features = {
            'available_balance': schema_db.column_exists('accounts', 'available_balance'),
            'status': schema_db.column_exists('accounts', 'status'),
            'is_active': schema_db.column_exists('accounts', 'is_active')
        }
        
        # Test transaction table features
        transaction_features = {
            'description': schema_db.column_exists('transactions', 'description'),
            'category': schema_db.column_exists('transactions', 'category'),
            'transaction_date': schema_db.column_exists('transactions', 'transaction_date'),
            'created_date': schema_db.column_exists('transactions', 'created_date'),
            'merchant_name': schema_db.column_exists('transactions', 'merchant_name'),
            'balance_after': schema_db.column_exists('transactions', 'balance_after')
        }
        
        # Validate expected features per schema version
        if schema_version == 'v1_0_basic':
            # Basic schema should have minimal features
            assert customer_features['email'] == True  # Basic field
            assert customer_features['household_income'] == False  # Extended field
            assert account_features['available_balance'] == False  # Extended field
            assert transaction_features['description'] == False  # Extended field
            
        elif schema_version == 'v1_1_extended':
            # Extended schema should have most features
            assert customer_features['household_income'] == True
            assert customer_features['profile_description'] == False  # Enhanced only
            assert account_features['available_balance'] == True
            assert account_features['status'] == False  # Enhanced field (has is_active instead)
            assert transaction_features['description'] == True
            assert transaction_features['merchant_name'] == False  # Enhanced only
            
        elif schema_version == 'v1_2_enhanced':
            # Enhanced schema should have all features
            assert customer_features['phone'] == True
            assert customer_features['profile_description'] == True
            assert account_features['status'] == True
            assert transaction_features['merchant_name'] == True
            assert transaction_features['balance_after'] == True
        
        print(f"✅ Schema features validated for {schema_version}")
        print(f"   Customer features: {sum(customer_features.values())}/{len(customer_features)}")
        print(f"   Account features: {sum(account_features.values())}/{len(account_features)}")
        print(f"   Transaction features: {sum(transaction_features.values())}/{len(transaction_features)}")
        
        db_manager.close()


if __name__ == "__main__":
    # Quick validation test
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as f:
        test_db = f.name
    
    # Create enhanced schema
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE customers (
            customer_id TEXT PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            household_income DECIMAL(12,2)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE accounts (
            account_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            account_type TEXT,
            balance DECIMAL(12,2),
            status TEXT DEFAULT 'active'
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
    
    conn.commit()
    conn.close()
    
    # Test schema-aware data generation
    from src.syfi.database import DatabaseManager
    from src.syfi.profile_builder import BankingDataGenerator
    
    db_manager = DatabaseManager(test_db)
    data_gen = BankingDataGenerator(db_manager)
    
    print("=== Phase 3 Data Generation Integration Test ===")
    print(f"✅ Schema-aware connection: {data_gen._schema_db is not None}")
    print(f"✅ Customers table: {data_gen._schema_db.table_exists('customers')}")
    print(f"✅ Phone column: {data_gen._schema_db.column_exists('customers', 'phone')}")
    print(f"✅ Status column: {data_gen._schema_db.column_exists('accounts', 'status')}")
    
    # Cleanup
    db_manager.close()
    os.unlink(test_db)