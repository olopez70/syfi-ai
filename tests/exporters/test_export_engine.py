"""
Tests for Export Engine.

This module tests the comprehensive data export functionality that handles
multi-format data export using configurable schemas with database operations.
"""

import pytest
import tempfile
import sqlite3
import json
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, mock_open, MagicMock
from typing import Dict, Any, List
from io import StringIO

from src.syfi.exporters.export_engine import ExportEngine
from src.syfi.exporters.schema_loader import (
    ExportSchema,
    ExportTable, 
    FieldMapping
)


# Module-level fixtures shared across all test classes
@pytest.fixture
def temp_database():
    """Create a temporary database with test data."""
    temp_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    db_path = temp_file.name
    temp_file.close()
    
    # Create and populate test database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create customers table
    cursor.execute('''
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            balance REAL,
            created_date TEXT,
            status TEXT
        )
    ''')
    
    # Create accounts table
    cursor.execute('''
        CREATE TABLE accounts (
            account_id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            account_type TEXT,
            balance REAL,
            created_date TEXT,
            is_active INTEGER,
            FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
        )
    ''')
    
    # Insert test data
    customers_data = [
        (1, 'John', 'Doe', 'john@example.com', 1234.56, '2023-01-15', 'active'),
        (2, 'Jane', 'Smith', 'jane@example.com', 2345.67, '2023-02-20', 'active'),
        (3, 'Bob', 'Johnson', 'bob@example.com', -100.00, '2023-03-10', 'inactive'),
        (4, 'Alice', 'Brown', 'alice@example.com', 0.00, '2023-04-05', 'active')
    ]
    
    cursor.executemany(
        'INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?)',
        customers_data
    )
    
    accounts_data = [
        (1, 1, 'checking', 1000.00, '2023-01-15', 1),
        (2, 1, 'savings', 234.56, '2023-01-16', 1),
        (3, 2, 'checking', 2345.67, '2023-02-20', 1),
        (4, 3, 'checking', -100.00, '2023-03-10', 0),
        (5, 4, 'savings', 0.00, '2023-04-05', 1)
    ]
    
    cursor.executemany(
        'INSERT INTO accounts VALUES (?, ?, ?, ?, ?, ?)',
        accounts_data
    )
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def export_engine(temp_database):
    """Create ExportEngine instance with test database."""
    return ExportEngine(temp_database)


@pytest.fixture
def sample_schema():
    """Create a sample export schema for testing."""
    return ExportSchema(
        name="test_export",
        description="Test export schema",
        version="1.0",
        format="csv",
        tables=[
            ExportTable(
                table_name="customers",
                export_name="customers",
                fields=[
                    FieldMapping("customer_id", "id", "string"),
                    FieldMapping("first_name", "firstName", "string"),
                    FieldMapping("last_name", "lastName", "string"),
                    FieldMapping("balance", "balance", "float", "%.2f", 0.0, "format_currency")
                ],
                filters={"status": "active"},
                sort_by="customer_id"
            )
        ]
    )


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    
    # Cleanup - remove all files in directory
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.unit
class TestExportEngine:
    """Test ExportEngine class initialization and basic functionality."""
    
    def test_engine_initialization(self):
        """Test ExportEngine initialization with database path."""
        db_path = "/tmp/test.db"
        engine = ExportEngine(db_path)
        
        assert engine.database_path == db_path
        assert engine.transformers is not None
    
    def test_engine_initialization_with_different_paths(self):
        """Test ExportEngine initialization with various database paths."""
        paths = [
            "/home/user/data.db",
            "relative/path/database.sqlite",
            ":memory:",
            "/tmp/banking_data.db"
        ]
        
        for path in paths:
            engine = ExportEngine(path)
            assert engine.database_path == path


@pytest.mark.unit
class TestExportEngineCSV:
    """Test CSV export functionality."""
    
    def test_export_csv_basic(self, export_engine, sample_schema, temp_output_dir):
        """Test basic CSV export functionality."""
        sample_schema.format = "csv"
        
        result = export_engine.export_data(sample_schema, str(temp_output_dir))
        
        assert isinstance(result, dict)
        assert "files" in result
        assert "success" in result
        assert result["success"] is True
        assert len(result["files"]) > 0
        
        # Check that CSV file was created
        csv_files = list(temp_output_dir.glob("*.csv"))
        assert len(csv_files) > 0
        
        # Verify CSV content
        csv_file = csv_files[0]
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) > 0
        assert "id" in rows[0]
        assert "firstName" in rows[0]
        assert "lastName" in rows[0]
    
    def test_export_csv_with_headers(self, export_engine, sample_schema, temp_output_dir):
        """Test CSV export with headers enabled."""
        sample_schema.format = "csv"
        sample_schema.include_headers = True
        
        result = export_engine.export_data(sample_schema, str(temp_output_dir))
        
        csv_file = list(temp_output_dir.glob("*.csv"))[0]
        with open(csv_file, 'r') as f:
            content = f.read()
        
        # Should have header row
        lines = content.strip().split('\n')
        assert len(lines) >= 2  # Header + at least one data row
        
        header_line = lines[0]
        assert "id" in header_line
        assert "firstName" in header_line
    
    def test_export_csv_without_headers(self, export_engine, sample_schema, temp_output_dir):
        """Test CSV export with headers disabled."""
        sample_schema.format = "csv"
        sample_schema.include_headers = False
        
        result = export_engine.export_data(sample_schema, str(temp_output_dir))
        
        csv_file = list(temp_output_dir.glob("*.csv"))[0]
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            first_row = next(reader)
        
        # First row should be data, not headers
        assert first_row[0].isdigit()  # customer_id should be numeric
    
    def test_export_csv_custom_delimiter(self, export_engine, sample_schema, temp_output_dir):
        """Test CSV export with custom delimiter."""
        sample_schema.format = "csv"
        sample_schema.delimiter = ";"
        
        result = export_engine.export_data(sample_schema, str(temp_output_dir))
        
        csv_file = list(temp_output_dir.glob("*.csv"))[0]
        with open(csv_file, 'r') as f:
            content = f.read()
        
        # Should use semicolon delimiter
        assert ";" in content
        
        # Parse with correct delimiter
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f, delimiter=';')
            rows = list(reader)
        
        assert len(rows) > 0
    
    def test_export_csv_encoding(self, export_engine, sample_schema, temp_output_dir):
        """Test CSV export with different encodings."""
        sample_schema.format = "csv"
        sample_schema.encoding = "utf-8"
        
        result = export_engine.export_data(sample_schema, str(temp_output_dir))
        
        csv_file = list(temp_output_dir.glob("*.csv"))[0]
        
        # Should be able to read with specified encoding
        with open(csv_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert len(content) > 0
    
    def test_export_csv_multiple_tables(self, export_engine, temp_output_dir):
        """Test CSV export with multiple tables."""
        schema = ExportSchema(
            name="multi_table_export",
            description="Multi-table test",
            version="1.0",
            format="csv",
            tables=[
                ExportTable(
                    table_name="customers",
                    export_name="customers",
                    fields=[
                        FieldMapping("customer_id", "id"),
                        FieldMapping("first_name", "name")
                    ]
                ),
                ExportTable(
                    table_name="accounts",
                    export_name="accounts", 
                    fields=[
                        FieldMapping("account_id", "id"),
                        FieldMapping("account_type", "type"),
                        FieldMapping("balance", "balance")
                    ]
                )
            ]
        )
        
        result = export_engine.export_data(schema, str(temp_output_dir))
        
        csv_files = list(temp_output_dir.glob("*.csv"))
        assert len(csv_files) == 2  # One file per table


@pytest.mark.unit
class TestExportEngineJSON:
    """Test JSON export functionality."""
    
    def test_export_json_basic(self, export_engine, sample_schema, temp_output_dir):
        """Test basic JSON export functionality."""
        sample_schema.format = "json"
        
        result = export_engine.export_data(sample_schema, str(temp_output_dir))
        
        assert isinstance(result, dict)
        assert "files" in result
        
        # Check that JSON file was created
        json_files = list(temp_output_dir.glob("*.json"))
        assert len(json_files) > 0
        
        # Verify JSON content
        json_file = json_files[0]
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, dict)
        assert "customers" in data
        assert isinstance(data["customers"], list)
        assert len(data["customers"]) > 0
    
    def test_export_json_pretty_print(self, export_engine, sample_schema, temp_output_dir):
        """Test JSON export with pretty printing."""
        sample_schema.format = "json"
        sample_schema.output_options = {"pretty_print": True}
        
        result = export_engine.export_data(sample_schema, str(temp_output_dir))
        
        json_file = list(temp_output_dir.glob("*.json"))[0]
        with open(json_file, 'r') as f:
            content = f.read()
        
        # Pretty printed JSON should have indentation
        assert "  " in content or "\t" in content
        
        # Should still be valid JSON
        data = json.loads(content)
        assert isinstance(data, dict)
    
    def test_export_json_single_table(self, export_engine, sample_schema, temp_output_dir):
        """Test JSON export structure for single table."""
        sample_schema.format = "json"
        
        result = export_engine.export_data(sample_schema, str(temp_output_dir))
        
        json_file = list(temp_output_dir.glob("*.json"))[0]
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Verify structure
        assert "customers" in data
        customers = data["customers"]
        assert isinstance(customers, list)
        
        if len(customers) > 0:
            customer = customers[0]
            assert "id" in customer
            assert "firstName" in customer
            assert "lastName" in customer
    
    def test_export_json_multiple_tables(self, export_engine, temp_output_dir):
        """Test JSON export with multiple tables."""
        schema = ExportSchema(
            name="multi_table_json",
            description="Multi-table JSON test",
            version="1.0",
            format="json",
            tables=[
                ExportTable(
                    table_name="customers",
                    export_name="customers",
                    fields=[FieldMapping("customer_id", "id")]
                ),
                ExportTable(
                    table_name="accounts",
                    export_name="accounts",
                    fields=[FieldMapping("account_id", "id")]
                )
            ]
        )
        
        result = export_engine.export_data(schema, str(temp_output_dir))
        
        json_file = list(temp_output_dir.glob("*.json"))[0]
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        assert "customers" in data
        assert "accounts" in data
        assert isinstance(data["customers"], list)
        assert isinstance(data["accounts"], list)
    
    def test_export_json_encoding(self, export_engine, sample_schema, temp_output_dir):
        """Test JSON export with different encodings."""
        sample_schema.format = "json"
        sample_schema.encoding = "utf-8"
        
        result = export_engine.export_data(sample_schema, str(temp_output_dir))
        
        json_file = list(temp_output_dir.glob("*.json"))[0]
        
        # Should be able to read with specified encoding
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert isinstance(data, dict)


@pytest.mark.unit
class TestExportEngineXML:
    """Test XML export functionality."""
    
    def test_export_xml_basic(self, export_engine, sample_schema, temp_output_dir):
        """Test basic XML export functionality."""
        sample_schema.format = "xml"
        
        result = export_engine.export_data(sample_schema, str(temp_output_dir))
        
        assert isinstance(result, dict)
        assert "files" in result
        
        # Check that XML file was created
        xml_files = list(temp_output_dir.glob("*.xml"))
        assert len(xml_files) > 0
        
        # Verify XML content
        xml_file = xml_files[0]
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        assert root.tag == "export"
        customers = root.find("customers")
        assert customers is not None
        
        # Should have customer records
        customer_records = customers.findall("record")
        assert len(customer_records) > 0
    
    def test_export_xml_structure(self, export_engine, sample_schema, temp_output_dir):
        """Test XML export structure and elements."""
        sample_schema.format = "xml"
        
        result = export_engine.export_data(sample_schema, str(temp_output_dir))
        
        xml_file = list(temp_output_dir.glob("*.xml"))[0]
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Check root element
        assert root.tag == "export"
        
        # Check table element
        customers = root.find("customers")
        assert customers is not None
        
        # Check record elements
        records = customers.findall("record")
        if len(records) > 0:
            record = records[0]
            
            # Check field elements
            id_elem = record.find("id")
            first_name_elem = record.find("firstName")
            
            assert id_elem is not None
            assert first_name_elem is not None
            assert id_elem.text is not None
    
    def test_export_xml_multiple_tables(self, export_engine, temp_output_dir):
        """Test XML export with multiple tables."""
        schema = ExportSchema(
            name="multi_table_xml",
            description="Multi-table XML test",
            version="1.0",
            format="xml",
            tables=[
                ExportTable(
                    table_name="customers",
                    export_name="customers",
                    fields=[FieldMapping("customer_id", "id")]
                ),
                ExportTable(
                    table_name="accounts",
                    export_name="accounts",
                    fields=[FieldMapping("account_id", "id")]
                )
            ]
        )
        
        result = export_engine.export_data(schema, str(temp_output_dir))
        
        xml_file = list(temp_output_dir.glob("*.xml"))[0]
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        customers = root.find("customers")
        accounts = root.find("accounts")
        
        assert customers is not None
        assert accounts is not None
    
    def test_export_xml_encoding(self, export_engine, sample_schema, temp_output_dir):
        """Test XML export with encoding specification."""
        sample_schema.format = "xml"
        sample_schema.encoding = "utf-8"
        
        result = export_engine.export_data(sample_schema, str(temp_output_dir))
        
        xml_file = list(temp_output_dir.glob("*.xml"))[0]
        
        # Check XML declaration
        with open(xml_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert ('<?xml version="1.0" encoding="utf-8"?>' in content or 
                'encoding="utf-8"' in content or 
                "encoding='utf-8'" in content)


@pytest.mark.unit
class TestExportEngineSQL:
    """Test SQL export functionality."""
    
    def test_export_sql_basic(self, export_engine, sample_schema, temp_output_dir):
        """Test basic SQL export functionality."""
        sample_schema.format = "sql"
        
        result = export_engine.export_data(sample_schema, str(temp_output_dir))
        
        assert isinstance(result, dict)
        assert "files" in result
        
        # Check that SQL file was created
        sql_files = list(temp_output_dir.glob("*.sql"))
        assert len(sql_files) > 0
        
        # Verify SQL content
        sql_file = sql_files[0]
        with open(sql_file, 'r') as f:
            content = f.read()
        
        assert "INSERT INTO" in content
        assert "customers" in content
        assert len(content.strip()) > 0
    
    def test_export_sql_insert_statements(self, export_engine, sample_schema, temp_output_dir):
        """Test SQL export generates proper INSERT statements."""
        sample_schema.format = "sql"
        
        result = export_engine.export_data(sample_schema, str(temp_output_dir))
        
        sql_file = list(temp_output_dir.glob("*.sql"))[0]
        with open(sql_file, 'r') as f:
            content = f.read()
        
        # Should have INSERT statements
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        insert_lines = [line for line in lines if line.startswith('INSERT INTO')]
        
        assert len(insert_lines) > 0
        
        # Check format of INSERT statement
        insert_line = insert_lines[0]
        assert "INSERT INTO customers" in insert_line
        assert "VALUES" in insert_line
        assert "(" in insert_line and ")" in insert_line
    
    def test_export_sql_multiple_tables(self, export_engine, temp_output_dir):
        """Test SQL export with multiple tables."""
        schema = ExportSchema(
            name="multi_table_sql",
            description="Multi-table SQL test",
            version="1.0", 
            format="sql",
            tables=[
                ExportTable(
                    table_name="customers",
                    export_name="customers",
                    fields=[
                        FieldMapping("customer_id", "id"),
                        FieldMapping("first_name", "name")
                    ]
                ),
                ExportTable(
                    table_name="accounts",
                    export_name="accounts",
                    fields=[
                        FieldMapping("account_id", "id"),
                        FieldMapping("balance", "balance")
                    ]
                )
            ]
        )
        
        result = export_engine.export_data(schema, str(temp_output_dir))
        
        sql_file = list(temp_output_dir.glob("*.sql"))[0]
        with open(sql_file, 'r') as f:
            content = f.read()
        
        assert "INSERT INTO customers" in content
        assert "INSERT INTO accounts" in content


@pytest.mark.unit 
class TestExportEngineExcel:
    """Test Excel export functionality."""
    
    def test_export_excel_requires_pandas(self, export_engine, sample_schema, temp_output_dir):
        """Test Excel export behavior when pandas is not available."""
        sample_schema.format = "excel"
        
        # Mock pandas availability
        with patch('src.syfi.exporters.export_engine.HAS_PANDAS', False):
            with pytest.raises((ImportError, ValueError, RuntimeError)):
                export_engine.export_data(sample_schema, str(temp_output_dir))
    
    @patch('src.syfi.exporters.export_engine.HAS_PANDAS', True)
    @patch('src.syfi.exporters.export_engine.pd')
    def test_export_excel_with_pandas(self, mock_pd, export_engine, sample_schema, temp_output_dir):
        """Test Excel export when pandas is available."""
        sample_schema.format = "excel"
        
        # Mock pandas DataFrame and to_excel method
        mock_df = MagicMock()
        mock_pd.DataFrame.return_value = mock_df
        
        result = export_engine.export_data(sample_schema, str(temp_output_dir))
        
        # Should call pandas DataFrame constructor
        mock_pd.DataFrame.assert_called()
        # Should call to_excel method
        mock_df.to_excel.assert_called()


@pytest.mark.unit
class TestExportEngineDataExtraction:
    """Test data extraction and transformation methods."""
    
    def test_extract_table_data_basic(self, export_engine, temp_database):
        """Test basic table data extraction."""
        table = ExportTable(
            table_name="customers",
            export_name="customers",
            fields=[
                FieldMapping("customer_id", "id"),
                FieldMapping("first_name", "name"),
                FieldMapping("status", "status")
            ]
        )
        
        conn = sqlite3.connect(temp_database)
        data = export_engine._extract_table_data(conn, table)
        conn.close()
        
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check data structure - should have target field names, not source field names
        row = data[0]
        assert isinstance(row, dict)
        assert "id" in row  # target field for customer_id
        assert "name" in row  # target field for first_name
    
    def test_extract_table_data_with_filters(self, export_engine, temp_database):
        """Test table data extraction with filters."""
        table = ExportTable(
            table_name="customers",
            export_name="customers",
            fields=[
                FieldMapping("customer_id", "id"),
                FieldMapping("status", "status")  # Include status field so we can check it
            ],
            filters={"status": "active"}
        )
        
        conn = sqlite3.connect(temp_database)
        data = export_engine._extract_table_data(conn, table)
        conn.close()
        
        # Should only return active customers
        assert len(data) >= 1
        for row in data:
            assert row["status"] == "active"
    
    def test_extract_table_data_with_sorting(self, export_engine, temp_database):
        """Test table data extraction with sorting."""
        table = ExportTable(
            table_name="customers",
            export_name="customers",
            fields=[
                FieldMapping("customer_id", "id"),
                FieldMapping("balance", "balance")
            ],
            sort_by="balance DESC"
        )
        
        conn = sqlite3.connect(temp_database)
        data = export_engine._extract_table_data(conn, table)
        conn.close()
        
        assert len(data) > 1
        
        # Should be sorted by balance descending
        balances = [row["balance"] for row in data]
        assert balances == sorted(balances, reverse=True)
    
    def test_extract_table_data_with_joins(self, export_engine, temp_database):
        """Test table data extraction with joins."""
        table = ExportTable(
            table_name="accounts",
            export_name="accounts_with_customers", 
            fields=[
                FieldMapping("accounts.account_id", "id"),
                FieldMapping("customers.first_name", "customer_name"),
                FieldMapping("accounts.balance", "balance")  # Specify which table's balance
            ],
            joins=["LEFT JOIN customers ON accounts.customer_id = customers.customer_id"]
        )
        
        conn = sqlite3.connect(temp_database)
        data = export_engine._extract_table_data(conn, table)
        conn.close()
        
        assert len(data) > 0
        
        # Should have customer data from join (using target field names)
        row = data[0]
        assert "customer_name" in row  # target field for customers.first_name
        assert row["customer_name"] is not None  # target field name
    
    def test_transform_row_basic(self, export_engine):
        """Test basic row transformation."""
        table = ExportTable(
            table_name="test",
            export_name="test",
            fields=[
                FieldMapping("source_id", "id"),
                FieldMapping("source_name", "name")
            ]
        )
        
        row = {
            "source_id": 123,
            "source_name": "Test Name",
            "extra_field": "ignored"
        }
        
        transformed = export_engine._transform_row(row, table)
        
        assert "id" in transformed
        assert "name" in transformed
        assert transformed["id"] == 123
        assert transformed["name"] == "Test Name"
        assert "extra_field" not in transformed
    
    def test_transform_row_with_transforms(self, export_engine):
        """Test row transformation with data transformers."""
        table = ExportTable(
            table_name="test",
            export_name="test",
            fields=[
                FieldMapping("amount", "currency", "float", None, None, "format_currency"),
                FieldMapping("name", "upper_name", "string", None, None, "uppercase")
            ]
        )
        
        row = {
            "amount": 1234.56,
            "name": "test name"
        }
        
        transformed = export_engine._transform_row(row, table)
        
        assert transformed["currency"] == "$1,234.56"
        assert transformed["upper_name"] == "TEST NAME"
    
    def test_transform_row_with_default_values(self, export_engine):
        """Test row transformation with default values."""
        table = ExportTable(
            table_name="test",
            export_name="test", 
            fields=[
                FieldMapping("missing_field", "with_default", "string", None, "DEFAULT_VALUE"),
                FieldMapping("null_field", "null_with_default", "string", None, "NULL_DEFAULT")
            ]
        )
        
        row = {
            "null_field": None
        }
        
        transformed = export_engine._transform_row(row, table)
        
        assert transformed["with_default"] == "DEFAULT_VALUE"
        assert transformed["null_with_default"] == "NULL_DEFAULT"


@pytest.mark.unit
class TestExportEnginePreview:
    """Test export preview functionality."""
    
    def test_preview_export_basic(self, export_engine, sample_schema):
        """Test basic export preview functionality."""
        preview = export_engine.preview_export(sample_schema, limit=5)
        
        assert isinstance(preview, dict)
        assert "preview" in preview
        assert "total_records" in preview
        
        preview_data = preview["preview"]
        assert "customers" in preview_data
        assert isinstance(preview_data["customers"], list)
        assert len(preview_data["customers"]) <= 5
    
    def test_preview_export_with_limit(self, export_engine, sample_schema):
        """Test export preview with different limits."""
        limits = [1, 3, 10, 100]
        
        for limit in limits:
            preview = export_engine.preview_export(sample_schema, limit=limit)
            
            customers = preview["preview"]["customers"]
            assert len(customers) <= limit
    
    def test_preview_export_multiple_tables(self, export_engine):
        """Test export preview with multiple tables."""
        schema = ExportSchema(
            name="multi_preview",
            description="Multi-table preview test",
            version="1.0",
            format="json",
            tables=[
                ExportTable(
                    table_name="customers",
                    export_name="customers",
                    fields=[FieldMapping("customer_id", "id")]
                ),
                ExportTable(
                    table_name="accounts",
                    export_name="accounts",
                    fields=[FieldMapping("account_id", "id")]
                )
            ]
        )
        
        preview = export_engine.preview_export(schema, limit=3)
        
        preview_data = preview["preview"]
        assert "customers" in preview_data
        assert "accounts" in preview_data
        
        assert len(preview_data["customers"]) <= 3
        assert len(preview_data["accounts"]) <= 3


@pytest.mark.unit
class TestExportEngineErrorHandling:
    """Test error handling in export engine."""
    
    def test_invalid_export_format(self, export_engine, sample_schema, temp_output_dir):
        """Test handling of invalid export format."""
        sample_schema.format = "invalid_format"
        
        with pytest.raises(ValueError) as excinfo:
            export_engine.export_data(sample_schema, str(temp_output_dir))
        
        assert "Unsupported export format" in str(excinfo.value)
    
    def test_invalid_database_path(self):
        """Test handling of invalid database path."""
        engine = ExportEngine("/nonexistent/path/to/database.db")
        
        schema = ExportSchema(
            name="test",
            description="Test",
            version="1.0",
            format="csv",
            tables=[
                ExportTable(
                    table_name="test_table",
                    export_name="test",
                    fields=[FieldMapping("id", "id")]
                )
            ]
        )
        
        with pytest.raises((sqlite3.OperationalError, FileNotFoundError)):
            engine.export_data(schema, "exports")
    
    def test_invalid_table_name(self, export_engine, temp_output_dir):
        """Test handling of invalid table name."""
        schema = ExportSchema(
            name="invalid_table_test",
            description="Test invalid table",
            version="1.0",
            format="csv",
            tables=[
                ExportTable(
                    table_name="nonexistent_table",
                    export_name="test",
                    fields=[FieldMapping("id", "id")]
                )
            ]
        )
        
        with pytest.raises(sqlite3.OperationalError):
            export_engine.export_data(schema, str(temp_output_dir))
    
    def test_invalid_field_name(self, export_engine, temp_output_dir):
        """Test handling of invalid field name."""
        schema = ExportSchema(
            name="invalid_field_test",
            description="Test invalid field",
            version="1.0",
            format="csv",
            tables=[
                ExportTable(
                    table_name="customers",
                    export_name="customers",
                    fields=[FieldMapping("nonexistent_field", "test_field")]
                )
            ]
        )
        
        with pytest.raises(sqlite3.OperationalError):
            export_engine.export_data(schema, str(temp_output_dir))
    
    def test_empty_schema_tables(self, export_engine, temp_output_dir):
        """Test handling of schema with no tables."""
        schema = ExportSchema(
            name="empty_schema",
            description="Empty schema test",
            version="1.0",
            format="csv",
            tables=[]
        )
        
        result = export_engine.export_data(schema, str(temp_output_dir))
        
        # Should handle gracefully
        assert isinstance(result, dict)
        assert "files" in result


@pytest.mark.integration
class TestExportEngineIntegration:
    """Integration tests for ExportEngine with realistic scenarios."""
    
    def test_full_banking_export_workflow(self, temp_output_dir):
        """Test complete banking data export workflow."""
        # Create realistic banking database
        temp_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        db_path = temp_file.name
        temp_file.close()
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create comprehensive banking schema
        cursor.execute('''
            CREATE TABLE customers (
                customer_id INTEGER PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT,
                address TEXT,
                city TEXT,
                state TEXT,
                zip_code TEXT,
                ssn TEXT,
                date_of_birth DATE,
                account_opened DATE,
                credit_score INTEGER,
                annual_income REAL,
                employment_status TEXT,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE accounts (
                account_id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                account_number TEXT UNIQUE,
                account_type TEXT,
                balance REAL DEFAULT 0.0,
                interest_rate REAL,
                opened_date DATE,
                closed_date DATE,
                status TEXT DEFAULT 'active',
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE transactions (
                transaction_id INTEGER PRIMARY KEY,
                account_id INTEGER,
                transaction_type TEXT,
                amount REAL,
                description TEXT,
                transaction_date DATETIME,
                balance_after REAL,
                reference_number TEXT,
                FOREIGN KEY (account_id) REFERENCES accounts (account_id)
            )
        ''')
        
        # Insert comprehensive test data
        customers_data = [
            (1, 'John', 'Doe', 'john.doe@email.com', '555-1234', '123 Main St', 'Anytown', 'CA', '12345', '123-45-6789', '1980-01-15', '2020-01-15', 750, 75000.00, 'employed', 'active'),
            (2, 'Jane', 'Smith', 'jane.smith@email.com', '555-5678', '456 Oak Ave', 'Somewhere', 'NY', '67890', '987-65-4321', '1985-06-20', '2019-03-22', 680, 82000.00, 'employed', 'active'),
            (3, 'Bob', 'Johnson', 'bob.johnson@email.com', '555-9012', '789 Pine St', 'Elsewhere', 'TX', '54321', '456-78-9012', '1975-12-10', '2018-07-08', 720, 95000.00, 'employed', 'active'),
        ]
        
        cursor.executemany(
            'INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            customers_data
        )
        
        accounts_data = [
            (1, 1, 'CHK-001-123', 'checking', 2500.75, 0.01, '2020-01-15', None, 'active'),
            (2, 1, 'SAV-001-124', 'savings', 15000.00, 0.025, '2020-01-15', None, 'active'),
            (3, 2, 'CHK-002-125', 'checking', 1825.50, 0.01, '2019-03-22', None, 'active'),
            (4, 2, 'SAV-002-126', 'savings', 25000.00, 0.025, '2019-03-22', None, 'active'),
            (5, 3, 'CHK-003-127', 'checking', 3750.25, 0.01, '2018-07-08', None, 'active'),
        ]
        
        cursor.executemany(
            'INSERT INTO accounts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            accounts_data
        )
        
        transactions_data = [
            (1, 1, 'deposit', 1000.00, 'Direct Deposit - Salary', '2023-10-01 09:00:00', 2500.75, 'TXN-001'),
            (2, 1, 'withdrawal', -200.00, 'ATM Withdrawal', '2023-10-02 15:30:00', 2300.75, 'TXN-002'),
            (3, 2, 'deposit', 500.00, 'Transfer from Checking', '2023-10-03 10:15:00', 15000.00, 'TXN-003'),
            (4, 3, 'deposit', 2000.00, 'Direct Deposit - Salary', '2023-10-01 09:00:00', 1825.50, 'TXN-004'),
            (5, 4, 'interest', 25.00, 'Monthly Interest', '2023-10-01 00:01:00', 25000.00, 'TXN-005'),
        ]
        
        cursor.executemany(
            'INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            transactions_data
        )
        
        conn.commit()
        conn.close()
        
        # Create comprehensive export schema
        banking_schema = ExportSchema(
            name="comprehensive_banking_export",
            description="Complete banking data export for regulatory compliance",
            version="2.0",
            format="json",
            encoding="utf-8",
            output_options={"pretty_print": True},
            tables=[
                ExportTable(
                    table_name="customers",
                    export_name="customers",
                    fields=[
                        FieldMapping("customer_id", "id", "string"),
                        FieldMapping("first_name", "firstName", "string"),
                        FieldMapping("last_name", "lastName", "string"), 
                        FieldMapping("email", "email", "string"),
                        FieldMapping("phone", "phone", "string"),
                        FieldMapping("annual_income", "annualIncome", "float", "%.2f", 0.0, "format_currency"),
                        FieldMapping("credit_score", "creditScore", "integer", None, 0),
                        FieldMapping("account_opened", "accountOpened", "date", None, None, "format_date_iso"),
                        FieldMapping("status", "status", "string")
                    ],
                    filters={"status": "active"},
                    sort_by="customer_id"
                ),
                ExportTable(
                    table_name="accounts",
                    export_name="accounts",
                    fields=[
                        FieldMapping("account_id", "id", "string"),
                        FieldMapping("customer_id", "customerId", "string"),
                        FieldMapping("account_number", "accountNumber", "string"),
                        FieldMapping("account_type", "type", "string", None, None, "uppercase"),
                        FieldMapping("balance", "currentBalance", "float", "%.2f", 0.0, "format_currency"),
                        FieldMapping("interest_rate", "interestRate", "float", "%.4f", 0.0),
                        FieldMapping("opened_date", "openedDate", "date", None, None, "format_date_iso")
                    ],
                    filters={"status": "active"},
                    sort_by="customer_id, account_type"
                ),
                ExportTable(
                    table_name="transactions",
                    export_name="transactions",
                    fields=[
                        FieldMapping("transaction_id", "id", "string"),
                        FieldMapping("account_id", "accountId", "string"),
                        FieldMapping("transaction_type", "type", "string", None, None, "uppercase"),
                        FieldMapping("amount", "amount", "float", "%.2f", 0.0, "format_currency"),
                        FieldMapping("description", "description", "string"),
                        FieldMapping("transaction_date", "date", "date", None, None, "format_date_iso"),
                        FieldMapping("reference_number", "referenceNumber", "string")
                    ],
                    sort_by="transaction_date DESC"
                )
            ]
        )
        
        # Execute export
        engine = ExportEngine(db_path)
        result = engine.export_data(banking_schema, str(temp_output_dir))
        
        # Verify results
        assert isinstance(result, dict)
        assert "files" in result
        assert "success" in result
        assert result["success"] is True
        
        # Verify JSON file was created
        json_files = list(temp_output_dir.glob("*.json"))
        assert len(json_files) == 1
        
        json_file = json_files[0]
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Verify data structure
        assert "customers" in data
        assert "accounts" in data
        assert "transactions" in data
        
        # Verify customers data
        customers = data["customers"]
        assert len(customers) == 3
        customer = customers[0]
        assert "id" in customer
        assert "firstName" in customer
        assert "annualIncome" in customer
        assert customer["annualIncome"].startswith("$")  # Currency formatting
        
        # Verify accounts data
        accounts = data["accounts"]
        assert len(accounts) == 5
        account = accounts[0]
        assert "accountNumber" in account
        assert "type" in account
        assert account["type"].isupper()  # Uppercase transformation
        assert "currentBalance" in account
        assert account["currentBalance"].startswith("$")  # Currency formatting
        
        # Verify transactions data
        transactions = data["transactions"]
        assert len(transactions) == 5
        transaction = transactions[0]
        assert "type" in transaction
        assert transaction["type"].isupper()  # Uppercase transformation
        assert "amount" in transaction
        assert transaction["amount"].startswith("$")  # Currency formatting
        
        # Cleanup
        Path(db_path).unlink(missing_ok=True)
    
    def test_performance_large_dataset(self):
        """Test export performance with large dataset."""
        # Create database with large dataset
        temp_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        db_path = temp_file.name
        temp_file.close()
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE large_table (
                id INTEGER PRIMARY KEY,
                name TEXT,
                value REAL,
                created_date TEXT
            )
        ''')
        
        # Insert 1000 records
        import random
        large_data = [
            (i, f'Record_{i}', random.uniform(1.0, 1000.0), f'2023-{random.randint(1,12):02d}-{random.randint(1,28):02d}')
            for i in range(1, 1001)
        ]
        
        cursor.executemany('INSERT INTO large_table VALUES (?, ?, ?, ?)', large_data)
        conn.commit()
        conn.close()
        
        # Create export schema
        schema = ExportSchema(
            name="large_export",
            description="Large dataset export test",
            version="1.0",
            format="csv",
            tables=[
                ExportTable(
                    table_name="large_table",
                    export_name="large_data",
                    fields=[
                        FieldMapping("id", "id"),
                        FieldMapping("name", "name"),
                        FieldMapping("value", "value", "float", "%.2f"),
                        FieldMapping("created_date", "date")
                    ]
                )
            ]
        )
        
        # Test export performance
        engine = ExportEngine(db_path)
        
        import time
        start_time = time.time()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = engine.export_data(schema, temp_dir)
        
        end_time = time.time()
        export_time = end_time - start_time
        
        # Should complete within reasonable time (< 10 seconds for 1000 records)
        assert export_time < 10.0
        
        # Verify result
        assert isinstance(result, dict)
        assert "success" in result
        assert result["success"] is True
        
        # Cleanup
        Path(db_path).unlink(missing_ok=True)