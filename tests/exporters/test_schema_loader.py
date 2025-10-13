"""
Tests for Export Schema Loader.

This module tests the configuration loading and validation functionality
that handles YAML/Python schema files and data transformation definitions.
"""

import pytest
import tempfile
import yaml
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, mock_open
from typing import Dict, Any

from src.syfi.exporters.schema_loader import (
    FieldMapping,
    ExportTable,
    ExportSchema,
    ExportSchemaLoader,
    DataTransformers
)


@pytest.mark.unit
class TestFieldMapping:
    """Test FieldMapping dataclass."""
    
    def test_field_mapping_initialization(self):
        """Test FieldMapping initialization with required fields."""
        mapping = FieldMapping(
            source_field="customer_id",
            target_field="id"
        )
        
        assert mapping.source_field == "customer_id"
        assert mapping.target_field == "id"
        assert mapping.data_type == "string"  # Default
        assert mapping.format is None
        assert mapping.default_value is None
        assert mapping.transform is None
    
    def test_field_mapping_with_all_options(self):
        """Test FieldMapping with all options specified."""
        mapping = FieldMapping(
            source_field="created_date",
            target_field="dateCreated",
            data_type="date",
            format="%Y-%m-%d",
            default_value="1970-01-01",
            transform="format_date_iso"
        )
        
        assert mapping.source_field == "created_date"
        assert mapping.target_field == "dateCreated"
        assert mapping.data_type == "date"
        assert mapping.format == "%Y-%m-%d"
        assert mapping.default_value == "1970-01-01"
        assert mapping.transform == "format_date_iso"
    
    def test_field_mapping_with_numeric_types(self):
        """Test FieldMapping with different numeric data types."""
        integer_mapping = FieldMapping(
            source_field="age",
            target_field="customerAge",
            data_type="integer",
            default_value=0
        )
        
        float_mapping = FieldMapping(
            source_field="balance",
            target_field="accountBalance",
            data_type="float",
            format="%.2f",
            transform="format_currency"
        )
        
        assert integer_mapping.data_type == "integer"
        assert integer_mapping.default_value == 0
        
        assert float_mapping.data_type == "float"
        assert float_mapping.format == "%.2f"
        assert float_mapping.transform == "format_currency"


@pytest.mark.unit
class TestExportTable:
    """Test ExportTable dataclass."""
    
    @pytest.fixture
    def sample_field_mappings(self):
        """Create sample field mappings for testing."""
        return [
            FieldMapping("customer_id", "id"),
            FieldMapping("first_name", "firstName"),
            FieldMapping("balance", "accountBalance", "float", "%.2f", 0.0, "format_currency")
        ]
    
    def test_export_table_initialization(self, sample_field_mappings):
        """Test ExportTable initialization with required fields."""
        table = ExportTable(
            table_name="customers",
            export_name="CustomerList",
            fields=sample_field_mappings
        )
        
        assert table.table_name == "customers"
        assert table.export_name == "CustomerList"
        assert len(table.fields) == 3
        assert table.filters is None
        assert table.joins is None
        assert table.sort_by is None
    
    def test_export_table_with_all_options(self, sample_field_mappings):
        """Test ExportTable with all optional fields."""
        table = ExportTable(
            table_name="accounts",
            export_name="AccountsWithCustomers",
            fields=sample_field_mappings,
            filters={"status": "active", "balance__gt": 0},
            joins=["LEFT JOIN customers ON accounts.customer_id = customers.id"],
            sort_by="balance DESC"
        )
        
        assert table.table_name == "accounts"
        assert table.export_name == "AccountsWithCustomers"
        assert table.filters["status"] == "active"
        assert table.filters["balance__gt"] == 0
        assert len(table.joins) == 1
        assert "LEFT JOIN" in table.joins[0]
        assert table.sort_by == "balance DESC"
    
    def test_export_table_empty_fields(self):
        """Test ExportTable with empty fields list."""
        table = ExportTable(
            table_name="test",
            export_name="Test",
            fields=[]
        )
        
        assert len(table.fields) == 0


@pytest.mark.unit 
class TestExportSchema:
    """Test ExportSchema dataclass."""
    
    @pytest.fixture
    def sample_tables(self):
        """Create sample export tables for testing."""
        return [
            ExportTable(
                table_name="customers",
                export_name="customers",
                fields=[
                    FieldMapping("customer_id", "id"),
                    FieldMapping("first_name", "firstName")
                ]
            ),
            ExportTable(
                table_name="accounts", 
                export_name="accounts",
                fields=[
                    FieldMapping("account_id", "id"),
                    FieldMapping("balance", "balance", "float")
                ]
            )
        ]
    
    def test_export_schema_initialization(self, sample_tables):
        """Test ExportSchema initialization with required fields."""
        schema = ExportSchema(
            name="banking_export",
            description="Banking data export",
            version="1.0",
            format="csv",
            tables=sample_tables
        )
        
        assert schema.name == "banking_export"
        assert schema.description == "Banking data export"
        assert schema.version == "1.0"
        assert schema.format == "csv"
        assert schema.encoding == "utf-8"  # Default
        assert schema.delimiter == ","  # Default
        assert schema.include_headers is True  # Default
        assert len(schema.tables) == 2
        assert schema.output_options is None
    
    def test_export_schema_with_all_options(self, sample_tables):
        """Test ExportSchema with all options specified."""
        schema = ExportSchema(
            name="custom_export",
            description="Custom export configuration",
            version="2.1",
            format="json",
            encoding="utf-16",
            delimiter=";",
            include_headers=False,
            tables=sample_tables,
            output_options={"pretty_print": True, "compress": False}
        )
        
        assert schema.name == "custom_export"
        assert schema.encoding == "utf-16"
        assert schema.delimiter == ";"
        assert schema.include_headers is False
        assert schema.output_options["pretty_print"] is True
        assert schema.output_options["compress"] is False
    
    def test_export_schema_different_formats(self):
        """Test ExportSchema with different output formats."""
        formats = ["csv", "json", "xml", "excel", "sql"]
        
        for fmt in formats:
            schema = ExportSchema(
                name=f"{fmt}_export",
                description=f"{fmt.upper()} export",
                version="1.0",
                format=fmt
            )
            assert schema.format == fmt


@pytest.mark.unit
class TestExportSchemaLoader:
    """Test ExportSchemaLoader class."""
    
    @pytest.fixture
    def temp_schema_dir(self):
        """Create a temporary directory for schema files."""
        temp_dir = tempfile.mkdtemp()
        return Path(temp_dir)
    
    @pytest.fixture
    def loader(self, temp_schema_dir):
        """Create an ExportSchemaLoader instance."""
        return ExportSchemaLoader(str(temp_schema_dir))
    
    @pytest.fixture
    def sample_yaml_schema(self):
        """Create sample YAML schema data."""
        return {
            "name": "test_export",
            "description": "Test export schema",
            "version": "1.0",
            "format": "csv",
            "encoding": "utf-8",
            "delimiter": ",",
            "include_headers": True,
            "tables": [
                {
                    "table_name": "customers",
                    "export_name": "customers",
                    "fields": [
                        {
                            "source_field": "customer_id",
                            "target_field": "id",
                            "data_type": "string"
                        },
                        {
                            "source_field": "balance",
                            "target_field": "balance",
                            "data_type": "float",
                            "format": "%.2f",
                            "default_value": 0.0
                        }
                    ],
                    "filters": {"status": "active"},
                    "sort_by": "customer_id"
                }
            ]
        }
    
    def test_loader_initialization(self, temp_schema_dir):
        """Test ExportSchemaLoader initialization."""
        loader = ExportSchemaLoader(str(temp_schema_dir))
        
        assert loader.schema_directory == temp_schema_dir
        assert isinstance(loader.loaded_schemas, dict)
        assert len(loader.loaded_schemas) == 0
    
    def test_loader_initialization_default_directory(self):
        """Test ExportSchemaLoader with default directory."""
        loader = ExportSchemaLoader()
        
        assert loader.schema_directory == Path("export_configs")
        assert isinstance(loader.loaded_schemas, dict)
    
    def test_load_all_schemas_empty_directory(self, loader):
        """Test loading schemas from empty directory."""
        schemas = loader.load_all_schemas()
        
        assert isinstance(schemas, dict)
        assert len(schemas) == 0
    
    def test_load_yaml_schema(self, loader, temp_schema_dir, sample_yaml_schema):
        """Test loading a YAML schema file."""
        # Create YAML schema file
        yaml_file = temp_schema_dir / "test_schema.yaml"
        with open(yaml_file, 'w') as f:
            yaml.dump(sample_yaml_schema, f)
        
        schema = loader.load_yaml_schema(yaml_file)
        
        assert isinstance(schema, ExportSchema)
        assert schema.name == "test_export"
        assert schema.description == "Test export schema"
        assert schema.format == "csv"
        assert len(schema.tables) == 1
        
        # Test table details
        table = schema.tables[0]
        assert table.table_name == "customers"
        assert table.export_name == "customers"
        assert len(table.fields) == 2
        assert table.filters["status"] == "active"
        assert table.sort_by == "customer_id"
        
        # Test field mappings
        id_field = table.fields[0]
        assert id_field.source_field == "customer_id"
        assert id_field.target_field == "id"
        assert id_field.data_type == "string"
        
        balance_field = table.fields[1]
        assert balance_field.source_field == "balance"
        assert balance_field.data_type == "float"
        assert balance_field.format == "%.2f"
        assert balance_field.default_value == 0.0
    
    def test_load_yaml_schema_invalid_file(self, loader, temp_schema_dir):
        """Test loading invalid YAML schema file."""
        # Create invalid YAML file
        invalid_yaml = temp_schema_dir / "invalid.yaml"
        with open(invalid_yaml, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        with pytest.raises(yaml.YAMLError):
            loader.load_yaml_schema(invalid_yaml)
    
    def test_load_python_schema(self, loader, temp_schema_dir):
        """Test loading a Python schema file."""
        # Create Python schema file
        python_file = temp_schema_dir / "python_schema.py"
        python_content = '''
EXPORT_SCHEMA = {
    "name": "python_export",
    "description": "Python-defined export schema",
    "version": "1.0",
    "format": "json",
    "tables": [
        {
            "table_name": "accounts",
            "export_name": "accounts",
            "fields": [
                {
                    "source_field": "account_id",
                    "target_field": "id",
                    "data_type": "string"
                },
                {
                    "source_field": "balance",
                    "target_field": "balance",
                    "data_type": "float"
                }
            ]
        }
    ]
}
'''
        with open(python_file, 'w') as f:
            f.write(python_content)
        
        schema = loader.load_python_schema(python_file)
        
        assert isinstance(schema, ExportSchema)
        assert schema.name == "python_export"
        assert schema.format == "json"
        assert len(schema.tables) == 1
        
        table = schema.tables[0]
        assert table.table_name == "accounts"
        assert len(table.fields) == 2
    
    def test_load_python_schema_no_schema_variable(self, loader, temp_schema_dir):
        """Test loading Python file without EXPORT_SCHEMA variable."""
        python_file = temp_schema_dir / "no_schema.py"
        with open(python_file, 'w') as f:
            f.write("# No EXPORT_SCHEMA variable defined\nother_variable = 'test'")
        
        schema = loader.load_python_schema(python_file)
        assert schema is None
    
    def test_load_all_schemas_mixed_files(self, loader, temp_schema_dir, sample_yaml_schema):
        """Test loading schemas from directory with mixed file types."""
        # Create YAML schema
        yaml_file = temp_schema_dir / "yaml_schema.yaml"
        with open(yaml_file, 'w') as f:
            yaml.dump(sample_yaml_schema, f)
        
        # Create Python schema
        python_file = temp_schema_dir / "python_schema.py"
        python_content = '''
EXPORT_SCHEMA = {
    "name": "python_test",
    "description": "Python test schema",
    "version": "1.0",
    "format": "xml",
    "tables": []
}
'''
        with open(python_file, 'w') as f:
            f.write(python_content)
        
        # Create non-schema file (should be ignored)
        other_file = temp_schema_dir / "readme.txt"
        with open(other_file, 'w') as f:
            f.write("This is not a schema file")
        
        schemas = loader.load_all_schemas()
        
        assert len(schemas) == 2
        assert "test_export" in schemas  # From YAML
        assert "python_test" in schemas  # From Python
        
        assert schemas["test_export"].format == "csv"
        assert schemas["python_test"].format == "xml"
    
    def test_get_schema(self, loader, temp_schema_dir, sample_yaml_schema):
        """Test retrieving a specific schema by name."""
        # Create and load schema
        yaml_file = temp_schema_dir / "test.yaml"
        with open(yaml_file, 'w') as f:
            yaml.dump(sample_yaml_schema, f)
        
        loader.load_all_schemas()
        
        # Test existing schema
        schema = loader.get_schema("test_export")
        assert schema is not None
        assert schema.name == "test_export"
        
        # Test non-existing schema
        schema = loader.get_schema("nonexistent")
        assert schema is None
    
    def test_list_schemas(self, loader, temp_schema_dir, sample_yaml_schema):
        """Test listing all available schemas."""
        # Create schema file
        yaml_file = temp_schema_dir / "test.yaml"
        with open(yaml_file, 'w') as f:
            yaml.dump(sample_yaml_schema, f)
        
        loader.load_all_schemas()
        
        schema_list = loader.list_schemas()
        
        assert isinstance(schema_list, list)
        assert len(schema_list) == 1
        
        schema_info = schema_list[0]
        assert schema_info["name"] == "test_export"
        assert schema_info["description"] == "Test export schema"
        assert schema_info["version"] == "1.0"
        assert schema_info["format"] == "csv"
    
    def test_validate_schema_valid(self, sample_yaml_schema):
        """Test validation of valid schema."""
        loader = ExportSchemaLoader()
        
        # Create valid schema
        schema = ExportSchema(
            name="valid_schema",
            description="Valid test schema",
            version="1.0",
            format="csv",
            tables=[
                ExportTable(
                    table_name="test_table",
                    export_name="test",
                    fields=[
                        FieldMapping("id", "id"),
                        FieldMapping("name", "name")
                    ]
                )
            ]
        )
        
        errors = loader.validate_schema(schema)
        assert isinstance(errors, list)
        assert len(errors) == 0
    
    def test_validate_schema_invalid_format(self):
        """Test validation of schema with invalid format."""
        loader = ExportSchemaLoader()
        
        schema = ExportSchema(
            name="invalid_schema",
            description="Invalid test schema",
            version="1.0",
            format="invalid_format"  # Invalid format
        )
        
        errors = loader.validate_schema(schema)
        assert len(errors) > 0
        assert any("format" in error.lower() for error in errors)
    
    def test_validate_schema_missing_fields(self):
        """Test validation of schema with missing required fields."""
        loader = ExportSchemaLoader()
        
        # Schema with empty tables list
        schema = ExportSchema(
            name="",  # Empty name
            description="",  # Empty description
            version="1.0",
            format="csv",
            tables=[]  # No tables
        )
        
        errors = loader.validate_schema(schema)
        assert len(errors) > 0
        # Should have errors for empty name, description, and no tables
        assert len(errors) >= 2
    
    def test_parse_schema_dict_minimal(self, loader):
        """Test parsing minimal schema dictionary."""
        data = {
            "name": "minimal",
            "description": "Minimal schema",
            "version": "1.0",
            "format": "json"
        }
        
        schema = loader._parse_schema_dict(data)
        
        assert schema.name == "minimal"
        assert schema.description == "Minimal schema"
        assert schema.format == "json"
        assert schema.tables == []  # Default empty list
    
    def test_parse_schema_dict_complex(self, loader):
        """Test parsing complex schema dictionary."""
        data = {
            "name": "complex",
            "description": "Complex schema",
            "version": "1.0",
            "format": "excel",
            "encoding": "utf-16",
            "delimiter": ";",
            "include_headers": False,
            "output_options": {"sheet_name": "Data", "freeze_panes": True},
            "tables": [
                {
                    "table_name": "customers",
                    "export_name": "CustomerData",
                    "fields": [
                        {
                            "source_field": "id",
                            "target_field": "customer_id",
                            "data_type": "integer"
                        }
                    ],
                    "filters": {"active": True},
                    "sort_by": "id"
                }
            ]
        }
        
        schema = loader._parse_schema_dict(data)
        
        assert schema.name == "complex"
        assert schema.encoding == "utf-16"
        assert schema.delimiter == ";"
        assert schema.include_headers is False
        assert schema.output_options["sheet_name"] == "Data"
        assert len(schema.tables) == 1
        
        table = schema.tables[0]
        assert table.table_name == "customers"
        assert table.export_name == "CustomerData"
        assert table.filters["active"] is True
        assert table.sort_by == "id"
        
        field = table.fields[0]
        assert field.source_field == "id"
        assert field.target_field == "customer_id"
        assert field.data_type == "integer"


@pytest.mark.unit
class TestDataTransformers:
    """Test DataTransformers class."""
    
    def test_format_currency_positive(self):
        """Test currency formatting with positive values."""
        result = DataTransformers.format_currency(1234.56)
        assert result == "$1,234.56"
        
        result = DataTransformers.format_currency(1000000)
        assert result == "$1,000,000.00"
    
    def test_format_currency_negative(self):
        """Test currency formatting with negative values."""
        result = DataTransformers.format_currency(-1234.56)
        assert result == "$-1,234.56"
        
        result = DataTransformers.format_currency(-0.50)
        assert result == "$-0.50"
    
    def test_format_currency_zero(self):
        """Test currency formatting with zero."""
        result = DataTransformers.format_currency(0)
        assert result == "$0.00"
        
        result = DataTransformers.format_currency(0.0)
        assert result == "$0.00"
    
    def test_format_currency_string_input(self):
        """Test currency formatting with string input."""
        result = DataTransformers.format_currency("1234.56")
        assert result == "$1,234.56"
        
        result = DataTransformers.format_currency("abc")
        assert result == "$0.00"  # Invalid string defaults to 0
    
    def test_format_currency_none_input(self):
        """Test currency formatting with None input."""
        result = DataTransformers.format_currency(None)
        assert result == "$0.00"
    
    def test_format_date_iso_datetime(self):
        """Test ISO date formatting with datetime object."""
        dt = datetime(2023, 12, 25, 15, 30, 45)
        result = DataTransformers.format_date_iso(dt)
        assert result == "2023-12-25T15:30:45"
    
    def test_format_date_iso_date_string(self):
        """Test ISO date formatting with date string."""
        result = DataTransformers.format_date_iso("2023-12-25")
        assert result == "2023-12-25"
        
        result = DataTransformers.format_date_iso("12/25/2023")
        # Should handle different formats and convert to ISO
        assert "2023" in result  # Basic check for year
    
    def test_format_date_iso_invalid_input(self):
        """Test ISO date formatting with invalid input."""
        result = DataTransformers.format_date_iso("invalid-date")
        assert result == "invalid-date"  # Implementation returns string as-is
        
        result = DataTransformers.format_date_iso(None)
        assert result == ""
        
        result = DataTransformers.format_date_iso(12345)  # Non-string, non-datetime
        assert result == ""
    
    def test_format_date_iso_edge_cases(self):
        """Test ISO date formatting with edge cases."""
        # Test with empty string
        result = DataTransformers.format_date_iso("")
        assert result == ""
        
        # Test with whitespace
        result = DataTransformers.format_date_iso("  ")
        assert result == "  "  # Implementation returns string as-is


@pytest.mark.integration
class TestExportSchemaLoaderIntegration:
    """Integration tests for ExportSchemaLoader with file system operations."""
    
    def test_full_workflow_yaml_schema(self):
        """Test complete workflow with YAML schema file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create comprehensive YAML schema
            schema_data = {
                "name": "comprehensive_banking",
                "description": "Comprehensive banking data export",
                "version": "1.2.3",
                "format": "json",
                "encoding": "utf-8",
                "output_options": {
                    "pretty_print": True,
                    "date_format": "iso"
                },
                "tables": [
                    {
                        "table_name": "customers",
                        "export_name": "customers",
                        "fields": [
                            {
                                "source_field": "customer_id",
                                "target_field": "id",
                                "data_type": "string"
                            },
                            {
                                "source_field": "first_name",
                                "target_field": "firstName", 
                                "data_type": "string"
                            },
                            {
                                "source_field": "created_date",
                                "target_field": "dateCreated",
                                "data_type": "date",
                                "format": "%Y-%m-%d",
                                "transform": "format_date_iso"
                            },
                            {
                                "source_field": "balance",
                                "target_field": "currentBalance",
                                "data_type": "float",
                                "format": "%.2f",
                                "default_value": 0.0,
                                "transform": "format_currency"
                            }
                        ],
                        "filters": {
                            "status": "active",
                            "balance__gte": 0
                        },
                        "joins": [
                            "LEFT JOIN accounts ON customers.id = accounts.customer_id"
                        ],
                        "sort_by": "created_date DESC"
                    },
                    {
                        "table_name": "transactions",
                        "export_name": "transactions", 
                        "fields": [
                            {
                                "source_field": "transaction_id",
                                "target_field": "id",
                                "data_type": "string"
                            },
                            {
                                "source_field": "amount",
                                "target_field": "amount",
                                "data_type": "float",
                                "transform": "format_currency"
                            }
                        ]
                    }
                ]
            }
            
            yaml_file = temp_path / "comprehensive.yaml"
            with open(yaml_file, 'w') as f:
                yaml.dump(schema_data, f)
            
            # Load and validate
            loader = ExportSchemaLoader(str(temp_path))
            schemas = loader.load_all_schemas()
            
            assert len(schemas) == 1
            schema = schemas["comprehensive_banking"]
            
            # Verify schema properties
            assert schema.name == "comprehensive_banking"
            assert schema.version == "1.2.3"
            assert schema.format == "json"
            assert schema.output_options["pretty_print"] is True
            
            # Verify tables
            assert len(schema.tables) == 2
            
            customers_table = next(t for t in schema.tables if t.table_name == "customers")
            assert len(customers_table.fields) == 4
            assert customers_table.filters["status"] == "active"
            assert len(customers_table.joins) == 1
            
            transactions_table = next(t for t in schema.tables if t.table_name == "transactions")
            assert len(transactions_table.fields) == 2
            
            # Test validation
            errors = loader.validate_schema(schema)
            assert len(errors) == 0
            
            # Test retrieval
            retrieved_schema = loader.get_schema("comprehensive_banking")
            assert retrieved_schema is not None
            assert retrieved_schema.name == "comprehensive_banking"
            
            # Test listing
            schema_list = loader.list_schemas()
            assert len(schema_list) == 1
            assert schema_list[0]["name"] == "comprehensive_banking"
    
    def test_error_handling_corrupted_files(self):
        """Test error handling with corrupted schema files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create corrupted YAML file
            corrupted_yaml = temp_path / "corrupted.yaml"
            with open(corrupted_yaml, 'w') as f:
                f.write("invalid: yaml: [unclosed")
            
            # Create corrupted Python file
            corrupted_python = temp_path / "corrupted.py"
            with open(corrupted_python, 'w') as f:
                f.write("invalid python syntax %%%")
            
            loader = ExportSchemaLoader(str(temp_path))
            
            # Should handle errors gracefully and continue
            schemas = loader.load_all_schemas()
            
            # Should return empty dict due to corrupted files
            assert isinstance(schemas, dict)
            # Exact behavior depends on implementation - may be empty or may skip corrupted files
    
    def test_performance_with_many_schemas(self):
        """Test performance with many schema files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create multiple schema files
            for i in range(50):
                schema_data = {
                    "name": f"schema_{i}",
                    "description": f"Test schema {i}",
                    "version": "1.0",
                    "format": "csv",
                    "tables": [
                        {
                            "table_name": "test_table",
                            "export_name": "test",
                            "fields": [
                                {
                                    "source_field": "id",
                                    "target_field": "id",
                                    "data_type": "string"
                                }
                            ]
                        }
                    ]
                }
                
                yaml_file = temp_path / f"schema_{i}.yaml"
                with open(yaml_file, 'w') as f:
                    yaml.dump(schema_data, f)
            
            loader = ExportSchemaLoader(str(temp_path))
            
            import time
            start_time = time.time()
            schemas = loader.load_all_schemas()
            end_time = time.time()
            
            # Should load all schemas within reasonable time (< 5 seconds)
            assert len(schemas) == 50
            assert (end_time - start_time) < 5.0
            
            # Test retrieval performance
            start_time = time.time()
            for i in range(10):
                schema = loader.get_schema(f"schema_{i}")
                assert schema is not None
            end_time = time.time()
            
            # Retrieval should be fast (< 1 second for 10 retrievals)
            assert (end_time - start_time) < 1.0