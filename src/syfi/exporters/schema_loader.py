"""
Export Schema Loader - Handles loading and validation of export configuration schemas
"""
import os
import yaml
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FieldMapping:
    """Defines how a database field maps to export format"""
    source_field: str  # Database field name
    target_field: str  # Export field name
    data_type: str = "string"  # string, integer, float, boolean, date
    format: Optional[str] = None  # Date format, number format, etc.
    default_value: Optional[Any] = None  # Default if null/missing
    transform: Optional[str] = None  # Transformation function name


@dataclass
class ExportTable:
    """Configuration for exporting a single table"""
    table_name: str  # Database table name
    export_name: str  # Name in export file
    fields: List[FieldMapping]  # Field mappings
    filters: Optional[Dict[str, Any]] = None  # SQL WHERE conditions
    joins: Optional[List[str]] = None  # JOIN statements if needed
    sort_by: Optional[str] = None  # ORDER BY field


@dataclass
class ExportSchema:
    """Complete export configuration schema"""
    name: str  # Schema name
    description: str  # Human readable description
    version: str  # Schema version
    format: str  # Output format: csv, json, xml, excel, sql
    encoding: str = "utf-8"  # File encoding
    delimiter: str = ","  # For CSV format
    include_headers: bool = True  # For CSV/Excel
    tables: List[ExportTable] = None  # Tables to export
    output_options: Dict[str, Any] = None  # Format-specific options


class ExportSchemaLoader:
    """Loads and validates export schemas from YAML and Python files"""
    
    def __init__(self, schema_directory: str = "export_configs"):
        self.schema_directory = Path(schema_directory)
        self.loaded_schemas: Dict[str, ExportSchema] = {}
        
    def load_all_schemas(self) -> Dict[str, ExportSchema]:
        """Load all available export schemas"""
        schemas = {}
        
        if not self.schema_directory.exists():
            return schemas
            
        # Load YAML schemas
        for yaml_file in self.schema_directory.glob("*.yaml"):
            try:
                schema = self.load_yaml_schema(yaml_file)
                schemas[schema.name] = schema
            except Exception as e:
                print(f"Error loading YAML schema {yaml_file}: {e}")
                
        # Load Python schemas
        for py_file in self.schema_directory.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            try:
                schema = self.load_python_schema(py_file)
                if schema:
                    schemas[schema.name] = schema
            except Exception as e:
                print(f"Error loading Python schema {py_file}: {e}")
                
        self.loaded_schemas = schemas
        return schemas
    
    def load_yaml_schema(self, file_path: Path) -> ExportSchema:
        """Load export schema from YAML file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        return self._parse_schema_dict(data)
    
    def load_python_schema(self, file_path: Path) -> Optional[ExportSchema]:
        """Load export schema from Python file"""
        import importlib.util
        
        spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Look for EXPORT_SCHEMA variable
        if hasattr(module, 'EXPORT_SCHEMA'):
            schema_dict = module.EXPORT_SCHEMA
            return self._parse_schema_dict(schema_dict)
        
        return None
    
    def _parse_schema_dict(self, data: Dict[str, Any]) -> ExportSchema:
        """Parse schema dictionary into ExportSchema object"""
        # Parse field mappings
        tables = []
        for table_data in data.get('tables', []):
            fields = []
            for field_data in table_data.get('fields', []):
                field = FieldMapping(**field_data)
                fields.append(field)
            
            table = ExportTable(
                table_name=table_data['table_name'],
                export_name=table_data['export_name'],
                fields=fields,
                filters=table_data.get('filters'),
                joins=table_data.get('joins'),
                sort_by=table_data.get('sort_by')
            )
            tables.append(table)
        
        schema = ExportSchema(
            name=data['name'],
            description=data['description'],
            version=data['version'],
            format=data['format'],
            encoding=data.get('encoding', 'utf-8'),
            delimiter=data.get('delimiter', ','),
            include_headers=data.get('include_headers', True),
            tables=tables,
            output_options=data.get('output_options', {})
        )
        
        return schema
    
    def get_schema(self, schema_name: str) -> Optional[ExportSchema]:
        """Get a specific schema by name"""
        if not self.loaded_schemas:
            self.load_all_schemas()
        return self.loaded_schemas.get(schema_name)
    
    def list_schemas(self) -> List[Dict[str, str]]:
        """List all available schemas with basic info"""
        if not self.loaded_schemas:
            self.load_all_schemas()
            
        return [
            {
                'name': schema.name,
                'description': schema.description,
                'version': schema.version,
                'format': schema.format
            }
            for schema in self.loaded_schemas.values()
        ]
    
    def validate_schema(self, schema: ExportSchema) -> List[str]:
        """Validate export schema for completeness and consistency"""
        errors = []
        
        if not schema.name:
            errors.append("Schema name is required")
        
        if not schema.format:
            errors.append("Export format is required")
        elif schema.format not in ['csv', 'json', 'xml', 'excel', 'sql']:
            errors.append(f"Unsupported format: {schema.format}")
        
        if not schema.tables:
            errors.append("At least one table configuration is required")
        
        for table in schema.tables or []:
            if not table.table_name:
                errors.append(f"Table name is required for export '{table.export_name}'")
            
            if not table.fields:
                errors.append(f"At least one field mapping is required for table '{table.table_name}'")
            
            for field in table.fields or []:
                if not field.source_field:
                    errors.append(f"Source field name is required in table '{table.table_name}'")
                if not field.target_field:
                    errors.append(f"Target field name is required for field '{field.source_field}' in table '{table.table_name}'")
        
        return errors


# Data transformation functions
class DataTransformers:
    """Collection of data transformation functions for export"""
    
    @staticmethod
    def format_currency(value: Any) -> str:
        """Format numeric value as currency"""
        try:
            return f"${float(value):,.2f}"
        except (ValueError, TypeError):
            return "$0.00"
    
    @staticmethod
    def format_date_iso(value: Any) -> str:
        """Format date as ISO string"""
        from datetime import datetime
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, str):
            return value
        return ""
    
    @staticmethod
    def format_date_us(value: Any) -> str:
        """Format date as MM/DD/YYYY"""
        from datetime import datetime
        if isinstance(value, datetime):
            return value.strftime("%m/%d/%Y")
        elif isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return dt.strftime("%m/%d/%Y")
            except:
                return value
        return ""
    
    @staticmethod
    def uppercase(value: Any) -> str:
        """Convert to uppercase"""
        return str(value).upper() if value else ""
    
    @staticmethod
    def lowercase(value: Any) -> str:
        """Convert to lowercase"""
        return str(value).lower() if value else ""
    
    @staticmethod
    def full_name(first_name: Any, last_name: Any) -> str:
        """Combine first and last name"""
        parts = [str(part).strip() for part in [first_name, last_name] if part]
        return " ".join(parts)