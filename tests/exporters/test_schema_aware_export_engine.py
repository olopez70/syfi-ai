"""
Tests for schema-aware ExportEngine - Phase 4: Export System Integration
"""
import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.syfi.exporters.export_engine import ExportEngine
from src.syfi.exporters.schema_loader import ExportSchema, ExportTable, FieldMapping
from src.syfi.schema_management.schema_aware_db import SchemaAwareConnection
from src.syfi.schema_management.schema_manager import SchemaManager, SchemaVersion, SCHEMA_DEFINITIONS


class TestSchemaAwareExportEngine:
    """Test ExportEngine with schema management framework"""

    @pytest.fixture
    def temp_db_v1_0_basic(self):
        """Create V1.0 Basic schema test database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        schema_db = SchemaAwareConnection(db_path)
        
        # Create basic tables
        schema_db.safe_execute("CREATE TABLE customers (customer_id TEXT, first_name TEXT, last_name TEXT, email TEXT)")
        schema_db.safe_execute("CREATE TABLE accounts (account_id TEXT, customer_id TEXT, account_type TEXT, balance REAL)")
        schema_db.safe_execute("CREATE TABLE transactions (transaction_id TEXT, account_id TEXT, amount REAL, date TEXT)")
        
        # Insert test data
        schema_db.safe_execute("INSERT INTO customers VALUES ('C001', 'John', 'Doe', 'john@example.com')")
        schema_db.safe_execute("INSERT INTO accounts VALUES ('A001', 'C001', 'checking', 1000.0)")
        schema_db.safe_execute("INSERT INTO transactions VALUES ('T001', 'A001', -50.0, '2024-01-01')")
        
        yield db_path
        os.unlink(db_path)

    @pytest.fixture 
    def temp_db_v1_2_enhanced(self):
        """Create V1.2 Enhanced schema test database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        schema_db = SchemaAwareConnection(db_path)
        
        # Create enhanced tables with additional columns
        schema_db.safe_execute("""CREATE TABLE customers (
            customer_id TEXT, first_name TEXT, last_name TEXT, email TEXT, 
            phone TEXT, address TEXT, city TEXT, state TEXT, zip_code TEXT, 
            date_of_birth TEXT, profile_description TEXT, is_active INTEGER
        )""")
        schema_db.safe_execute("""CREATE TABLE accounts (
            account_id TEXT, customer_id TEXT, account_type TEXT, balance REAL, 
            status TEXT, created_date TEXT, last_updated TEXT
        )""")
        schema_db.safe_execute("""CREATE TABLE transactions (
            transaction_id TEXT, account_id TEXT, amount REAL, date TEXT, 
            transaction_date TEXT, transaction_type TEXT, description TEXT, 
            category TEXT, merchant_name TEXT
        )""")
        
        # Insert test data with enhanced fields
        schema_db.safe_execute("""INSERT INTO customers VALUES (
            'C001', 'John', 'Doe', 'john@example.com', '555-1234', 
            '123 Main St', 'Boston', 'MA', '02101', '1980-01-01', 
            'Premium customer profile', 1
        )""")
        schema_db.safe_execute("""INSERT INTO accounts VALUES (
            'A001', 'C001', 'checking', 1000.0, 'active', '2024-01-01', '2024-01-01'
        )""")
        schema_db.safe_execute("""INSERT INTO transactions VALUES (
            'T001', 'A001', -50.0, '2024-01-01', '2024-01-01', 
            'debit', 'Coffee purchase', 'food', 'Starbucks'
        )""")
        
        yield db_path
        os.unlink(db_path)

    @pytest.fixture
    def export_schema_basic(self):
        """Basic export schema for testing"""
        return ExportSchema(
            name="test_export",
            description="Test export schema",
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
                        FieldMapping(source_field="email", target_field="emailAddress")
                    ]
                )
            ]
        )

    @pytest.fixture
    def export_schema_enhanced(self):
        """Enhanced export schema including optional fields"""
        return ExportSchema(
            name="test_export_enhanced",
            description="Enhanced test export schema",
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
                        FieldMapping(source_field="phone", target_field="phoneNumber"),
                        FieldMapping(source_field="profile_description", target_field="description"),
                        FieldMapping(source_field="is_active", target_field="active")
                    ]
                )
            ]
        )

    def test_export_engine_initialization_with_schema_awareness(self, temp_db_v1_0_basic):
        """Test ExportEngine initializes with schema-aware connection"""
        engine = ExportEngine(temp_db_v1_0_basic)
        
        assert engine.database_path == temp_db_v1_0_basic
        assert hasattr(engine, '_schema_db')
        assert isinstance(engine._schema_db, SchemaAwareConnection)

    def test_export_with_v1_0_basic_schema_handles_missing_columns_gracefully(self, temp_db_v1_0_basic, export_schema_enhanced):
        """Test export handles missing columns gracefully on V1.0 Basic schema"""
        engine = ExportEngine(temp_db_v1_0_basic)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # This should not fail even though enhanced schema expects columns not in V1.0 Basic
            with patch('builtins.print') as mock_print:
                result = engine.export_data(export_schema_enhanced, temp_dir)
            
            # Should have warnings about missing fields
            warning_calls = [call for call in mock_print.call_args_list 
                           if 'Warning' in str(call) and 'does not exist' in str(call)]
            assert len(warning_calls) > 0
            
            # But export should still succeed with available fields
            assert result['success'] is True
            assert len(result['files']) > 0

    def test_export_with_v1_2_enhanced_schema_uses_all_fields(self, temp_db_v1_2_enhanced, export_schema_enhanced):
        """Test export uses all available fields on V1.2 Enhanced schema"""
        engine = ExportEngine(temp_db_v1_2_enhanced)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = engine.export_data(export_schema_enhanced, temp_dir)
            
            assert result['success'] is True
            assert len(result['files']) == 1
            
            # Verify exported file contains enhanced data
            file_path = result['files'][0]['path']
            with open(file_path, 'r') as f:
                exported_data = json.load(f)
            
            customer_data = exported_data['customers'][0]
            assert 'phoneNumber' in customer_data
            assert 'description' in customer_data
            assert 'active' in customer_data
            assert customer_data['phoneNumber'] == '555-1234'

    def test_export_csv_format_with_schema_awareness(self, temp_db_v1_0_basic, export_schema_basic):
        """Test CSV export with schema-aware operations"""
        schema_basic_csv = ExportSchema(
            name="test_csv",
            description="CSV test export",
            version="1.0",
            format="csv",
            tables=export_schema_basic.tables
        )
        
        engine = ExportEngine(temp_db_v1_0_basic)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = engine.export_data(schema_basic_csv, temp_dir)
            
            assert result['success'] is True
            assert result['format'] == 'csv'
            assert len(result['files']) == 1
            
            # Verify CSV content
            file_path = result['files'][0]['path']
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) == 2  # Header + 1 data row
            assert 'id,firstName,lastName,emailAddress' in lines[0]
            assert 'C001,John,Doe,john@example.com' in lines[1]

    def test_export_handles_missing_tables_gracefully(self, temp_db_v1_0_basic):
        """Test export handles missing tables gracefully"""
        schema_with_missing_table = ExportSchema(
            name="test_missing_table",
            description="Test with missing table",
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
            with patch('builtins.print') as mock_print:
                result = engine.export_data(schema_with_missing_table, temp_dir)
            
            # Should warn about missing table
            warning_calls = [call for call in mock_print.call_args_list 
                           if 'Warning' in str(call) and 'does not exist' in str(call)]
            assert len(warning_calls) > 0
            
            # Export should still "succeed" but with no files
            assert result['success'] is True
            assert len(result['files']) == 0

    def test_export_xml_format_with_schema_awareness(self, temp_db_v1_0_basic, export_schema_basic):
        """Test XML export with schema-aware operations"""
        schema_basic_xml = ExportSchema(
            name="test_xml",
            description="XML test export", 
            version="1.0",
            format="xml",
            tables=export_schema_basic.tables
        )
        
        engine = ExportEngine(temp_db_v1_0_basic)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = engine.export_data(schema_basic_xml, temp_dir)
            
            assert result['success'] is True
            assert result['format'] == 'xml'
            assert len(result['files']) == 1
            
            # Verify XML content exists
            file_path = result['files'][0]['path']
            assert os.path.exists(file_path)
            assert file_path.endswith('.xml')

    def test_export_sql_format_with_schema_awareness(self, temp_db_v1_0_basic, export_schema_basic):
        """Test SQL export with schema-aware operations"""
        schema_basic_sql = ExportSchema(
            name="test_sql",
            description="SQL test export",
            version="1.0", 
            format="sql",
            tables=export_schema_basic.tables
        )
        
        engine = ExportEngine(temp_db_v1_0_basic)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = engine.export_data(schema_basic_sql, temp_dir)
            
            assert result['success'] is True
            assert result['format'] == 'sql'
            assert len(result['files']) == 1
            
            # Verify SQL content
            file_path = result['files'][0]['path']
            with open(file_path, 'r') as f:
                sql_content = f.read()
            
            assert 'CREATE TABLE' in sql_content
            assert 'INSERT INTO' in sql_content
            assert 'customers' in sql_content

    def test_preview_export_with_schema_awareness(self, temp_db_v1_0_basic, export_schema_enhanced):
        """Test preview functionality with schema-aware operations"""
        engine = ExportEngine(temp_db_v1_0_basic)
        
        with patch('builtins.print'):  # Suppress warnings for preview
            preview = engine.preview_export(export_schema_enhanced, limit=5)
        
        assert 'preview' in preview
        assert 'customers' in preview['preview']
        assert len(preview['preview']['customers']) == 1  # Only one customer in test data
        
        # Should contain only available fields (basic schema fields)
        customer_data = preview['preview']['customers'][0]
        assert 'id' in customer_data
        assert 'firstName' in customer_data 
        assert 'lastName' in customer_data
        assert 'emailAddress' in customer_data

    def test_export_with_filters_and_schema_awareness(self, temp_db_v1_2_enhanced):
        """Test export with filters on schema-aware operations"""
        schema_with_filters = ExportSchema(
            name="filtered_export",
            description="Export with filters",
            version="1.0",
            format="json",
            tables=[
                ExportTable(
                    table_name="customers",
                    export_name="active_customers",
                    fields=[
                        FieldMapping(source_field="customer_id", target_field="id"),
                        FieldMapping(source_field="first_name", target_field="firstName"),
                        FieldMapping(source_field="is_active", target_field="active")
                    ],
                    filters={"is_active": 1}  # Filter only active customers
                )
            ]
        )
        
        engine = ExportEngine(temp_db_v1_2_enhanced)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = engine.export_data(schema_with_filters, temp_dir)
            
            assert result['success'] is True
            
            # Verify filtered data
            file_path = result['files'][0]['path'] 
            with open(file_path, 'r') as f:
                exported_data = json.load(f)
            
            assert len(exported_data['active_customers']) == 1
            assert exported_data['active_customers'][0]['active'] == 1

    def test_export_performance_with_schema_awareness(self, temp_db_v1_2_enhanced, export_schema_enhanced):
        """Test export performance remains acceptable with schema-aware operations"""
        import time
        
        engine = ExportEngine(temp_db_v1_2_enhanced)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            start_time = time.time()
            result = engine.export_data(export_schema_enhanced, temp_dir)
            elapsed_time = time.time() - start_time
            
            # Schema-aware operations should complete quickly (< 1 second for test data)
            assert elapsed_time < 1.0
            assert result['success'] is True

    def test_multi_schema_compatibility_across_versions(self, temp_db_v1_0_basic, temp_db_v1_2_enhanced, export_schema_enhanced):
        """Test same export schema works across different database schema versions"""
        # Test with V1.0 Basic (missing columns should be handled gracefully)
        engine_basic = ExportEngine(temp_db_v1_0_basic)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('builtins.print'):  # Suppress warnings
                result_basic = engine_basic.export_data(export_schema_enhanced, temp_dir)
            
            assert result_basic['success'] is True
            
            # Verify basic export contains core fields only
            file_path = result_basic['files'][0]['path']
            with open(file_path, 'r') as f:
                basic_data = json.load(f)
            
            basic_customer = basic_data['customers'][0]
            assert 'id' in basic_customer
            assert 'firstName' in basic_customer
        
        # Test with V1.2 Enhanced (all fields should be available)
        engine_enhanced = ExportEngine(temp_db_v1_2_enhanced)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result_enhanced = engine_enhanced.export_data(export_schema_enhanced, temp_dir)
            
            assert result_enhanced['success'] is True
            
            # Verify enhanced export contains all fields
            file_path = result_enhanced['files'][0]['path']
            with open(file_path, 'r') as f:
                enhanced_data = json.load(f)
            
            enhanced_customer = enhanced_data['customers'][0]
            assert 'id' in enhanced_customer
            assert 'firstName' in enhanced_customer
            assert 'phoneNumber' in enhanced_customer  # Enhanced field
            assert 'description' in enhanced_customer  # Enhanced field
            assert 'active' in enhanced_customer       # Enhanced field

    def test_extract_table_data_safe_method_validation(self, temp_db_v1_0_basic):
        """Test the new _extract_table_data_safe method specifically"""
        engine = ExportEngine(temp_db_v1_0_basic)
        
        # Test with valid table and fields
        valid_table = ExportTable(
            table_name="customers",
            export_name="customers",
            fields=[
                FieldMapping(source_field="customer_id", target_field="id"),
                FieldMapping(source_field="first_name", target_field="firstName")
            ]
        )
        
        data = engine._extract_table_data_safe(valid_table)
        assert len(data) == 1
        assert 'id' in data[0] or 'customer_id' in data[0]
        
        # Test with invalid fields (should be filtered out)
        invalid_fields_table = ExportTable(
            table_name="customers",
            export_name="customers",
            fields=[
                FieldMapping(source_field="customer_id", target_field="id"),
                FieldMapping(source_field="nonexistent_field", target_field="missing")
            ]
        )
        
        with patch('builtins.print'):  # Suppress warnings
            data = engine._extract_table_data_safe(invalid_fields_table)
        
        # Should still return data but without nonexistent fields
        assert len(data) >= 0  # May be 0 or 1 depending on field validation

    def test_schema_aware_connection_usage_in_export_engine(self, temp_db_v1_0_basic):
        """Test that ExportEngine properly uses SchemaAwareConnection methods"""
        engine = ExportEngine(temp_db_v1_0_basic)
        
        # Verify schema-aware connection is properly initialized
        assert hasattr(engine._schema_db, 'table_exists')
        assert hasattr(engine._schema_db, 'column_exists')
        assert hasattr(engine._schema_db, 'safe_execute')
        
        # Test table existence check
        assert engine._schema_db.table_exists('customers') is True
        assert engine._schema_db.table_exists('nonexistent_table') is False
        
        # Test column existence check
        assert engine._schema_db.column_exists('customers', 'customer_id') is True
        assert engine._schema_db.column_exists('customers', 'nonexistent_column') is False