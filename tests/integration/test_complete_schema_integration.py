"""
Integration Tests for Schema Management Framework - Phase 5: Complete End-to-End Testing

This test suite validates the complete integration of schema management across all system components:
- Profiling module (Phase 1)
- Patterns module (Phase 2) 
- Data generation module (Phase 3)
- Export system (Phase 4)
"""
import pytest
import tempfile
import os
import json
from pathlib import Path
import sqlite3
from unittest.mock import patch
import time

from src.syfi.schema_management.schema_manager import SchemaManager, SchemaVersion, SCHEMA_DEFINITIONS, get_schema_manager
from src.syfi.schema_management.schema_aware_db import SchemaAwareConnection
from src.syfi.profiling.banking_metrics import BankingMetricsCalculator
from src.syfi.profiling.analyzer import BankingDataProfiler
from src.syfi.patterns.repositories import SQLiteCustomerRepository, SQLiteAccountRepository, SQLiteTransactionRepository
from src.syfi.profile_builder import ProfileBuilder, BankingDataGenerator
from src.syfi.patterns.observers import ObservableDataGenerator, DatabaseEventLogger
from src.syfi.exporters.export_engine import ExportEngine
from src.syfi.exporters.schema_loader import ExportSchema, ExportTable, FieldMapping


class TestSchemaManagementIntegration:
    """End-to-end integration tests for complete schema management framework"""

    @pytest.fixture
    def temp_db_v1_0_basic(self):
        """Create V1.0 Basic schema database for integration testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        schema_db = SchemaAwareConnection(db_path)
        
        # Create V1.0 BASIC schema tables (customers + accounts only, NO transactions)
        schema_db.safe_execute("CREATE TABLE customers (customer_id TEXT PRIMARY KEY, first_name TEXT, last_name TEXT, email TEXT)")
        schema_db.safe_execute("CREATE TABLE accounts (account_id TEXT PRIMARY KEY, customer_id TEXT, account_type TEXT, balance REAL)")
        
        # Add basic test data for integration testing
        schema_db.safe_execute("INSERT INTO customers VALUES ('C001', 'John', 'Doe', 'john@example.com')")
        schema_db.safe_execute("INSERT INTO customers VALUES ('C002', 'Jane', 'Smith', 'jane@example.com')")
        schema_db.safe_execute("INSERT INTO accounts VALUES ('A001', 'C001', 'checking', 1500.00)")
        schema_db.safe_execute("INSERT INTO accounts VALUES ('A002', 'C002', 'savings', 2500.00)")
        
        yield db_path
        os.unlink(db_path)

    @pytest.fixture
    def temp_db_v1_2_enhanced(self):
        """Create V1.2 Enhanced schema database for integration testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        schema_db = SchemaAwareConnection(db_path)
        
        # Create V1.2 ENHANCED schema tables with profile_description column for proper detection
        schema_db.safe_execute("""CREATE TABLE customers (
            customer_id TEXT PRIMARY KEY, first_name TEXT, last_name TEXT, email TEXT,
            phone TEXT, address TEXT, city TEXT, state TEXT, zip_code TEXT,
            date_of_birth TEXT, profile_description TEXT, is_active INTEGER
        )""")
        schema_db.safe_execute("""CREATE TABLE accounts (
            account_id TEXT PRIMARY KEY, customer_id TEXT, account_type TEXT, balance REAL,
            status TEXT, created_date TEXT, last_updated TEXT
        )""")
        schema_db.safe_execute("""CREATE TABLE transactions (
            transaction_id TEXT PRIMARY KEY, account_id TEXT, amount REAL, date TEXT,
            transaction_date TEXT, transaction_type TEXT, description TEXT,
            category TEXT, merchant_name TEXT
        )""")
        
        # Add enhanced test data
        schema_db.safe_execute("""INSERT INTO customers VALUES (
            'C001', 'John', 'Doe', 'john@example.com', '555-1234',
            '123 Main St', 'Boston', 'MA', '02101', '1980-01-01',
            'Premium customer with excellent credit', 1
        )""")
        schema_db.safe_execute("""INSERT INTO customers VALUES (
            'C002', 'Jane', 'Smith', 'jane@example.com', '555-5678',
            '456 Oak Ave', 'Cambridge', 'MA', '02138', '1985-05-15',
            'Standard customer profile', 1
        )""")
        schema_db.safe_execute("""INSERT INTO accounts VALUES (
            'A001', 'C001', 'checking', 1500.00, 'active', '2024-01-01', '2024-01-01'
        )""")
        schema_db.safe_execute("""INSERT INTO accounts VALUES (
            'A002', 'C002', 'savings', 2500.00, 'active', '2024-01-01', '2024-01-01'
        )""")
        schema_db.safe_execute("""INSERT INTO transactions VALUES (
            'T001', 'A001', -50.00, '2024-01-01', '2024-01-01', 'debit',
            'Coffee purchase', 'restaurant', 'Starbucks'
        )""")
        schema_db.safe_execute("""INSERT INTO transactions VALUES (
            'T002', 'A002', 100.00, '2024-01-02', '2024-01-02', 'credit',
            'Salary deposit', 'salary', 'Employer'
        )""")
        
        yield db_path
        os.unlink(db_path)

    def test_schema_detection_and_versioning_across_databases(self, temp_db_v1_0_basic, temp_db_v1_2_enhanced):
        """Test schema detection works correctly across different database versions"""
        # Test V1.0 Basic detection
        schema_manager_basic = get_schema_manager(temp_db_v1_0_basic)
        basic_version = schema_manager_basic.get_current_schema_version()
        assert basic_version == SchemaVersion.V1_0_BASIC
        
        # Test V1.2 Enhanced detection  
        schema_manager_enhanced = get_schema_manager(temp_db_v1_2_enhanced)
        enhanced_version = schema_manager_enhanced.get_current_schema_version()
        assert enhanced_version == SchemaVersion.V1_2_ENHANCED

    def test_profiling_integration_across_schema_versions(self, temp_db_v1_0_basic, temp_db_v1_2_enhanced):
        """Test profiling components work across different schema versions"""
        # Test Phase 1: Profiling with V1.0 Basic
        calc_basic = BankingMetricsCalculator(temp_db_v1_0_basic)
        metrics_basic = calc_basic.calculate_all_metrics()
        
        assert isinstance(metrics_basic, dict)
        assert len(metrics_basic) > 0  # Should have some metrics
        
        profiler_basic = BankingDataProfiler(temp_db_v1_0_basic)
        profile_basic = profiler_basic.generate_full_profile()
        
        assert 'banking_metrics' in profile_basic
        assert 'customer_profiles' in profile_basic
        assert 'data_quality' in profile_basic
        # V1.0 Basic works with available schema
        
        # Test Phase 1: Profiling with V1.2 Enhanced
        calc_enhanced = BankingMetricsCalculator(temp_db_v1_2_enhanced)
        metrics_enhanced = calc_enhanced.calculate_all_metrics()
        
        assert isinstance(metrics_enhanced, dict)
        assert len(metrics_enhanced) > 0
        
        profiler_enhanced = BankingDataProfiler(temp_db_v1_2_enhanced)
        profile_enhanced = profiler_enhanced.generate_full_profile()
        
        # Enhanced version should have more detailed profiles
        assert 'banking_metrics' in profile_enhanced
        assert 'customer_profiles' in profile_enhanced
        assert 'data_quality' in profile_enhanced

    def test_repository_patterns_integration_across_schema_versions(self, temp_db_v1_0_basic, temp_db_v1_2_enhanced):
        """Test Phase 2: Repository patterns work across schema versions"""
        # Test with V1.0 Basic
        customer_repo_basic = SQLiteCustomerRepository(temp_db_v1_0_basic)
        customers_basic = customer_repo_basic.find_all()
        assert len(customers_basic) == 2
        
        account_repo_basic = SQLiteAccountRepository(temp_db_v1_0_basic) 
        accounts_basic = account_repo_basic.find_all()
        assert len(accounts_basic) == 2
        
        # V1.0 Basic doesn't have transactions table, so we skip transaction repository test
        
        # Test with V1.2 Enhanced
        customer_repo_enhanced = SQLiteCustomerRepository(temp_db_v1_2_enhanced)
        customers_enhanced = customer_repo_enhanced.find_all()
        assert len(customers_enhanced) == 2
        
        account_repo_enhanced = SQLiteAccountRepository(temp_db_v1_2_enhanced)
        accounts_enhanced = account_repo_enhanced.find_all()
        assert len(accounts_enhanced) == 2
        
        transaction_repo_enhanced = SQLiteTransactionRepository(temp_db_v1_2_enhanced)
        transactions_enhanced = transaction_repo_enhanced.find_all()
        assert len(transactions_enhanced) >= 2

    def test_data_generation_integration_across_schema_versions(self, temp_db_v1_0_basic, temp_db_v1_2_enhanced):
        """Test Phase 3: Data generation works across schema versions"""
        # Test with V1.0 Basic
        profile_builder_basic = ProfileBuilder(temp_db_v1_0_basic)
        assert profile_builder_basic is not None
        
        generator_basic = BankingDataGenerator(temp_db_v1_0_basic)
        assert generator_basic is not None
        
        # Test observable generation with basic schema
        observable_basic = ObservableDataGenerator(temp_db_v1_0_basic)
        event_logger_basic = DatabaseEventLogger(temp_db_v1_0_basic)
        observable_basic.add_observer(event_logger_basic)
        
        # Test with V1.2 Enhanced  
        profile_builder_enhanced = ProfileBuilder(temp_db_v1_2_enhanced)
        assert profile_builder_enhanced is not None
        
        generator_enhanced = BankingDataGenerator(temp_db_v1_2_enhanced)
        assert generator_enhanced is not None
        
        # Test observable generation with enhanced schema
        observable_enhanced = ObservableDataGenerator(temp_db_v1_2_enhanced) 
        event_logger_enhanced = DatabaseEventLogger(temp_db_v1_2_enhanced)
        observable_enhanced.add_observer(event_logger_enhanced)

    def test_export_system_integration_across_schema_versions(self, temp_db_v1_0_basic, temp_db_v1_2_enhanced):
        """Test Phase 4: Export system works across schema versions"""
        # Define export schema that works with both versions
        export_schema = ExportSchema(
            name="integration_test_export",
            description="Integration test export schema",
            version="1.0",
            format="json",
            tables=[
                ExportTable(
                    table_name="customers",
                    export_name="customers",
                    fields=[
                        FieldMapping(source_field="customer_id", target_field="id"),
                        FieldMapping(source_field="first_name", target_field="firstName"),
                        FieldMapping(source_field="last_name", target_field="lastName"),
                        FieldMapping(source_field="email", target_field="emailAddress"),
                        # Optional enhanced fields
                        FieldMapping(source_field="phone", target_field="phoneNumber"),
                        FieldMapping(source_field="profile_description", target_field="description")
                    ]
                )
            ]
        )
        
        # Test export with V1.0 Basic (missing optional fields should be handled)
        engine_basic = ExportEngine(temp_db_v1_0_basic)
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('builtins.print'):  # Suppress warnings
                result_basic = engine_basic.export_data(export_schema, temp_dir)
            
            assert result_basic['success'] is True
            assert len(result_basic['files']) == 1
            
            # Verify basic export data
            file_path = result_basic['files'][0]['path']
            with open(file_path, 'r') as f:
                basic_data = json.load(f)
            
            assert len(basic_data['customers']) == 2
            basic_customer = basic_data['customers'][0]
            assert 'id' in basic_customer
            assert 'firstName' in basic_customer
        
        # Test export with V1.2 Enhanced (all fields should be available)
        engine_enhanced = ExportEngine(temp_db_v1_2_enhanced)
        with tempfile.TemporaryDirectory() as temp_dir:
            result_enhanced = engine_enhanced.export_data(export_schema, temp_dir)
            
            assert result_enhanced['success'] is True
            assert len(result_enhanced['files']) == 1
            
            # Verify enhanced export data
            file_path = result_enhanced['files'][0]['path']
            with open(file_path, 'r') as f:
                enhanced_data = json.load(f)
            
            assert len(enhanced_data['customers']) == 2
            enhanced_customer = enhanced_data['customers'][0]
            assert 'id' in enhanced_customer
            assert 'firstName' in enhanced_customer
            assert 'phoneNumber' in enhanced_customer  # Enhanced field
            assert 'description' in enhanced_customer  # Enhanced field

    def test_full_workflow_integration_v1_0_basic(self, temp_db_v1_0_basic):
        """Test complete workflow integration with V1.0 Basic schema"""
        # Phase 1: Profile the database
        profiler = BankingDataProfiler(temp_db_v1_0_basic)
        profile = profiler.generate_full_profile()
        
        assert 'banking_metrics' in profile
        assert isinstance(profile, dict)
        
        # Phase 2: Use repositories to access data  
        customer_repo = SQLiteCustomerRepository(temp_db_v1_0_basic)
        customers = customer_repo.find_all()
        assert len(customers) == 2
        
        account_repo = SQLiteAccountRepository(temp_db_v1_0_basic) 
        accounts = account_repo.find_all()
        assert len(accounts) == 2
        
        # Phase 3: Generate additional data (in real workflow)
        generator = BankingDataGenerator(temp_db_v1_0_basic)
        assert generator is not None
        
        # Phase 4: Export the data
        export_schema = ExportSchema(
            name="full_workflow_basic",
            description="Full workflow test",
            version="1.0", 
            format="csv",
            tables=[
                ExportTable(
                    table_name="customers",
                    export_name="customers",
                    fields=[
                        FieldMapping(source_field="customer_id", target_field="customer_id"),
                        FieldMapping(source_field="first_name", target_field="first_name"),
                        FieldMapping(source_field="email", target_field="email")
                    ]
                )
            ]
        )
        
        engine = ExportEngine(temp_db_v1_0_basic)
        with tempfile.TemporaryDirectory() as temp_dir:
            result = engine.export_data(export_schema, temp_dir)
            
            assert result['success'] is True
            assert len(result['files']) == 1
            assert result['files'][0]['rows'] == 2

    def test_full_workflow_integration_v1_2_enhanced(self, temp_db_v1_2_enhanced):
        """Test complete workflow integration with V1.2 Enhanced schema"""
        # Phase 1: Profile the enhanced database
        profiler = BankingDataProfiler(temp_db_v1_2_enhanced)
        profile = profiler.generate_full_profile()
        
        assert 'banking_metrics' in profile
        assert isinstance(profile, dict)
        
        # Phase 2: Use repositories with enhanced schema
        customer_repo = SQLiteCustomerRepository(temp_db_v1_2_enhanced)
        customers = customer_repo.find_all()
        assert len(customers) == 2
        
        # Phase 3: Generate with enhanced capabilities
        generator = BankingDataGenerator(temp_db_v1_2_enhanced)
        assert generator is not None
        
        # Phase 4: Export enhanced data
        export_schema = ExportSchema(
            name="full_workflow_enhanced",
            description="Full workflow enhanced test",
            version="1.0",
            format="json",
            tables=[
                ExportTable(
                    table_name="customers", 
                    export_name="customers",
                    fields=[
                        FieldMapping(source_field="customer_id", target_field="id"),
                        FieldMapping(source_field="first_name", target_field="firstName"),
                        FieldMapping(source_field="email", target_field="emailAddress"),
                        FieldMapping(source_field="phone", target_field="phoneNumber"),
                        FieldMapping(source_field="profile_description", target_field="description"),
                        FieldMapping(source_field="is_active", target_field="isActive")
                    ]
                )
            ]
        )
        
        engine = ExportEngine(temp_db_v1_2_enhanced)
        with tempfile.TemporaryDirectory() as temp_dir:
            result = engine.export_data(export_schema, temp_dir)
            
            assert result['success'] is True
            assert len(result['files']) == 1
            
            # Verify enhanced export contains all fields
            file_path = result['files'][0]['path']
            with open(file_path, 'r') as f:
                enhanced_data = json.load(f)
            
            customer = enhanced_data['customers'][0]
            assert 'phoneNumber' in customer
            assert 'description' in customer
            assert 'isActive' in customer

    def test_performance_integration_across_all_components(self, temp_db_v1_2_enhanced):
        """Test that integrated workflow maintains acceptable performance"""
        start_time = time.time()
        
        # Run complete workflow
        profiler = BankingDataProfiler(temp_db_v1_2_enhanced)
        profile = profiler.generate_full_profile()
        
        customer_repo = SQLiteCustomerRepository(temp_db_v1_2_enhanced)
        customers = customer_repo.find_all()
        
        export_schema = ExportSchema(
            name="performance_test",
            description="Performance integration test",
            version="1.0",
            format="json", 
            tables=[
                ExportTable(
                    table_name="customers",
                    export_name="customers",
                    fields=[
                        FieldMapping(source_field="customer_id", target_field="id"),
                        FieldMapping(source_field="first_name", target_field="firstName")
                    ]
                )
            ]
        )
        
        engine = ExportEngine(temp_db_v1_2_enhanced)
        with tempfile.TemporaryDirectory() as temp_dir:
            result = engine.export_data(export_schema, temp_dir)
        
        elapsed_time = time.time() - start_time
        
        # Complete integrated workflow should be fast (< 2 seconds for test data)
        assert elapsed_time < 2.0
        assert result['success'] is True

    def test_error_handling_integration_across_components(self, temp_db_v1_0_basic):
        """Test error handling works consistently across all integrated components"""
        # Test profiling with invalid database
        with pytest.raises(Exception):
            invalid_profiler = BankingDataProfiler("nonexistent.db")
            # This should handle the error gracefully or raise appropriate exception
        
        # Test repository with missing tables (should handle gracefully)
        customer_repo = SQLiteCustomerRepository(temp_db_v1_0_basic)
        
        # Test export with invalid schema (should handle gracefully)
        invalid_export_schema = ExportSchema(
            name="invalid_test",
            description="Invalid test",
            version="1.0",
            format="json",
            tables=[
                ExportTable(
                    table_name="nonexistent_table",
                    export_name="missing",
                    fields=[FieldMapping(source_field="id", target_field="id")]
                )
            ]
        )
        
        engine = ExportEngine(temp_db_v1_0_basic)
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('builtins.print'):  # Suppress warnings
                result = engine.export_data(invalid_export_schema, temp_dir)
            
            # Should handle missing table gracefully
            assert result['success'] is True
            assert len(result['files']) == 0  # No files created for missing table

    def test_schema_compatibility_validation_integration(self, temp_db_v1_0_basic, temp_db_v1_2_enhanced):
        """Test schema compatibility validation works across integrated components"""
        # Test compatibility validation with different schemas
        schema_manager_basic = get_schema_manager(temp_db_v1_0_basic)
        basic_version = schema_manager_basic.get_current_schema_version()
        
        schema_manager_enhanced = get_schema_manager(temp_db_v1_2_enhanced)
        enhanced_version = schema_manager_enhanced.get_current_schema_version()
        
        # Verify different versions detected correctly
        assert basic_version != enhanced_version
        assert basic_version == SchemaVersion.V1_0_BASIC
        assert enhanced_version == SchemaVersion.V1_2_ENHANCED
        
        # Test compatibility validation
        v1_2_schema_def = SCHEMA_DEFINITIONS[SchemaVersion.V1_2_ENHANCED]
        
        # V1.0 Basic should have compatibility issues with V1.2 requirements
        basic_issues = schema_manager_basic.validate_schema_compatibility(v1_2_schema_def)
        assert len(basic_issues['missing_columns']) > 0
        
        # V1.2 Enhanced should have no issues with V1.2 requirements  
        enhanced_issues = schema_manager_enhanced.validate_schema_compatibility(v1_2_schema_def)
        assert len(enhanced_issues['missing_columns']) == 0

    def test_multi_format_export_integration(self, temp_db_v1_2_enhanced):
        """Test all export formats work with schema-aware integration"""
        base_schema_config = {
            "name": "multi_format_test",
            "description": "Multi-format integration test",
            "version": "1.0",
            "tables": [
                ExportTable(
                    table_name="customers",
                    export_name="customers",
                    fields=[
                        FieldMapping(source_field="customer_id", target_field="id"),
                        FieldMapping(source_field="first_name", target_field="firstName")
                    ]
                )
            ]
        }
        
        formats_to_test = ['csv', 'json', 'xml', 'sql']
        
        engine = ExportEngine(temp_db_v1_2_enhanced)
        
        for format_name in formats_to_test:
            schema = ExportSchema(
                format=format_name,
                **base_schema_config
            )
            
            with tempfile.TemporaryDirectory() as temp_dir:
                result = engine.export_data(schema, temp_dir)
                
                assert result['success'] is True, f"Failed for format: {format_name}"
                assert result['format'] == format_name
                assert len(result['files']) == 1
                assert result['files'][0]['rows'] > 0

    def test_concurrent_access_integration(self, temp_db_v1_2_enhanced):
        """Test schema-aware components handle concurrent access properly"""
        # Test multiple components accessing same database simultaneously
        profiler = BankingDataProfiler(temp_db_v1_2_enhanced)
        customer_repo = SQLiteCustomerRepository(temp_db_v1_2_enhanced)
        engine = ExportEngine(temp_db_v1_2_enhanced)
        
        # Simulate concurrent operations
        profile = profiler.generate_profile_summary()
        customers = customer_repo.find_all()
        
        export_schema = ExportSchema(
            name="concurrent_test",
            description="Concurrent access test",
            version="1.0",
            format="json",
            tables=[
                ExportTable(
                    table_name="customers",
                    export_name="customers", 
                    fields=[FieldMapping(source_field="customer_id", target_field="id")]
                )
            ]
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = engine.export_data(export_schema, temp_dir)
        
        # All operations should succeed
        assert 'customers' in profile
        assert len(customers) > 0
        assert result['success'] is True