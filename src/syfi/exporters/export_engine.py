"""
Export Engine - Handles data export using configurable schemas
"""
import os
import csv
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import sqlite3
from io import StringIO, BytesIO

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

from .schema_loader import ExportSchema, ExportTable, FieldMapping, DataTransformers


class ExportEngine:
    """Handles data export using configurable schemas"""
    
    def __init__(self, database_path: str):
        self.database_path = database_path
        self.transformers = DataTransformers()
        
    def export_data(self, schema: ExportSchema, output_dir: str = "exports") -> Dict[str, Any]:
        """Export data according to schema configuration"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if schema.format == 'csv':
            return self._export_csv(schema, output_path, timestamp)
        elif schema.format == 'json':
            return self._export_json(schema, output_path, timestamp)
        elif schema.format == 'xml':
            return self._export_xml(schema, output_path, timestamp)
        elif schema.format == 'excel':
            return self._export_excel(schema, output_path, timestamp)
        elif schema.format == 'sql':
            return self._export_sql(schema, output_path, timestamp)
        else:
            raise ValueError(f"Unsupported export format: {schema.format}")
    
    def _export_csv(self, schema: ExportSchema, output_path: Path, timestamp: str) -> Dict[str, Any]:
        """Export data as CSV files"""
        files_created = []
        
        with sqlite3.connect(self.database_path) as conn:
            for table in schema.tables:
                # Generate filename
                filename = f"{table.export_name}_{schema.name}_{timestamp}.csv"
                filepath = output_path / filename
                
                # Get data
                data = self._extract_table_data(conn, table)
                
                # Write CSV
                with open(filepath, 'w', newline='', encoding=schema.encoding) as csvfile:
                    if not data:
                        # Empty file with headers
                        if schema.include_headers:
                            fieldnames = [field.target_field for field in table.fields]
                            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=schema.delimiter)
                            writer.writeheader()
                        files_created.append({
                            'filename': filename,
                            'path': str(filepath),
                            'table': table.export_name,
                            'rows': 0
                        })
                        continue
                    
                    # Write data
                    fieldnames = [field.target_field for field in table.fields]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=schema.delimiter)
                    
                    if schema.include_headers:
                        writer.writeheader()
                    
                    for row in data:
                        transformed_row = self._transform_row(row, table)
                        writer.writerow(transformed_row)
                
                files_created.append({
                    'filename': filename,
                    'path': str(filepath),
                    'table': table.export_name,
                    'rows': len(data)
                })
        
        return {
            'success': True,
            'format': 'csv',
            'files': files_created,
            'schema': schema.name
        }
    
    def _export_json(self, schema: ExportSchema, output_path: Path, timestamp: str) -> Dict[str, Any]:
        """Export data as JSON files"""
        files_created = []
        
        with sqlite3.connect(self.database_path) as conn:
            # Single file with all tables
            if schema.output_options.get('single_file', False):
                filename = f"{schema.name}_{timestamp}.json"
                filepath = output_path / filename
                
                export_data = {}
                total_rows = 0
                
                for table in schema.tables:
                    data = self._extract_table_data(conn, table)
                    transformed_data = [self._transform_row(row, table) for row in data]
                    export_data[table.export_name] = transformed_data
                    total_rows += len(data)
                
                with open(filepath, 'w', encoding=schema.encoding) as jsonfile:
                    json.dump(export_data, jsonfile, indent=2, default=str)
                
                files_created.append({
                    'filename': filename,
                    'path': str(filepath),
                    'table': 'all_tables',
                    'rows': total_rows
                })
            else:
                # Separate file for each table
                for table in schema.tables:
                    filename = f"{table.export_name}_{schema.name}_{timestamp}.json"
                    filepath = output_path / filename
                    
                    data = self._extract_table_data(conn, table)
                    transformed_data = [self._transform_row(row, table) for row in data]
                    
                    with open(filepath, 'w', encoding=schema.encoding) as jsonfile:
                        json.dump(transformed_data, jsonfile, indent=2, default=str)
                    
                    files_created.append({
                        'filename': filename,
                        'path': str(filepath),
                        'table': table.export_name,
                        'rows': len(data)
                    })
        
        return {
            'success': True,
            'format': 'json',
            'files': files_created,
            'schema': schema.name
        }
    
    def _export_xml(self, schema: ExportSchema, output_path: Path, timestamp: str) -> Dict[str, Any]:
        """Export data as XML files"""
        files_created = []
        
        with sqlite3.connect(self.database_path) as conn:
            for table in schema.tables:
                filename = f"{table.export_name}_{schema.name}_{timestamp}.xml"
                filepath = output_path / filename
                
                # Create XML structure
                root = ET.Element(table.export_name)
                root.set('schema', schema.name)
                root.set('exported_at', datetime.now().isoformat())
                
                data = self._extract_table_data(conn, table)
                
                for row in data:
                    transformed_row = self._transform_row(row, table)
                    row_elem = ET.SubElement(root, 'record')
                    
                    for field_name, field_value in transformed_row.items():
                        field_elem = ET.SubElement(row_elem, field_name)
                        field_elem.text = str(field_value) if field_value is not None else ''
                
                # Write XML file
                tree = ET.ElementTree(root)
                tree.write(filepath, encoding=schema.encoding, xml_declaration=True)
                
                files_created.append({
                    'filename': filename,
                    'path': str(filepath),
                    'table': table.export_name,
                    'rows': len(data)
                })
        
        return {
            'success': True,
            'format': 'xml',
            'files': files_created,
            'schema': schema.name
        }
    
    def _export_excel(self, schema: ExportSchema, output_path: Path, timestamp: str) -> Dict[str, Any]:
        """Export data as Excel file (requires pandas)"""
        if not HAS_PANDAS:
            raise ImportError("pandas is required for Excel export. Install with: pip install pandas openpyxl")
        
        filename = f"{schema.name}_{timestamp}.xlsx"
        filepath = output_path / filename
        
        files_created = []
        total_rows = 0
        
        with sqlite3.connect(self.database_path) as conn:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                for table in schema.tables:
                    data = self._extract_table_data(conn, table)
                    
                    if data:
                        # Transform data
                        transformed_data = [self._transform_row(row, table) for row in data]
                        df = pd.DataFrame(transformed_data)
                        
                        # Write to sheet
                        sheet_name = table.export_name[:31]  # Excel sheet name limit
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        
                        total_rows += len(data)
                    else:
                        # Empty sheet with headers
                        fieldnames = [field.target_field for field in table.fields]
                        df = pd.DataFrame(columns=fieldnames)
                        sheet_name = table.export_name[:31]
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        files_created.append({
            'filename': filename,
            'path': str(filepath),
            'table': 'all_tables',
            'rows': total_rows
        })
        
        return {
            'success': True,
            'format': 'excel',
            'files': files_created,
            'schema': schema.name
        }
    
    def _export_sql(self, schema: ExportSchema, output_path: Path, timestamp: str) -> Dict[str, Any]:
        """Export data as SQL INSERT statements"""
        files_created = []
        
        with sqlite3.connect(self.database_path) as conn:
            for table in schema.tables:
                filename = f"{table.export_name}_{schema.name}_{timestamp}.sql"
                filepath = output_path / filename
                
                data = self._extract_table_data(conn, table)
                
                with open(filepath, 'w', encoding=schema.encoding) as sqlfile:
                    # Write header comment
                    sqlfile.write(f"-- Export: {schema.name}\n")
                    sqlfile.write(f"-- Table: {table.export_name}\n")
                    sqlfile.write(f"-- Generated: {datetime.now().isoformat()}\n\n")
                    
                    if not data:
                        sqlfile.write(f"-- No data found for table {table.export_name}\n")
                        files_created.append({
                            'filename': filename,
                            'path': str(filepath),
                            'table': table.export_name,
                            'rows': 0
                        })
                        continue
                    
                    # Generate CREATE TABLE statement
                    field_definitions = []
                    for field in table.fields:
                        sql_type = self._get_sql_type(field.data_type)
                        field_definitions.append(f"    {field.target_field} {sql_type}")
                    
                    sqlfile.write(f"CREATE TABLE IF NOT EXISTS {table.export_name} (\n")
                    sqlfile.write(",\n".join(field_definitions))
                    sqlfile.write("\n);\n\n")
                    
                    # Generate INSERT statements
                    fieldnames = [field.target_field for field in table.fields]
                    fields_str = ", ".join(fieldnames)
                    
                    for row in data:
                        transformed_row = self._transform_row(row, table)
                        values = []
                        for field_name in fieldnames:
                            value = transformed_row.get(field_name)
                            if value is None:
                                values.append("NULL")
                            elif isinstance(value, str):
                                # Escape single quotes
                                escaped_value = value.replace("'", "''")
                                values.append(f"'{escaped_value}'")
                            else:
                                values.append(str(value))
                        
                        values_str = ", ".join(values)
                        sqlfile.write(f"INSERT INTO {table.export_name} ({fields_str}) VALUES ({values_str});\n")
                
                files_created.append({
                    'filename': filename,
                    'path': str(filepath),
                    'table': table.export_name,
                    'rows': len(data)
                })
        
        return {
            'success': True,
            'format': 'sql',
            'files': files_created,
            'schema': schema.name
        }
    
    def _extract_table_data(self, conn: sqlite3.Connection, table: ExportTable) -> List[Dict[str, Any]]:
        """Extract data from database table according to configuration"""
        # Build SELECT statement
        field_selections = []
        for field in table.fields:
            if field.source_field != field.target_field:
                # Quote target field names to handle spaces and special characters
                quoted_target = f'"{field.target_field}"'
                field_selections.append(f"{field.source_field} as {quoted_target}")
            else:
                field_selections.append(field.source_field)
        
        fields_str = ", ".join(field_selections)
        
        # Base query
        query = f"SELECT {fields_str} FROM {table.table_name}"
        
        # Add JOINs if specified
        if table.joins:
            for join in table.joins:
                query += f" {join}"
        
        # Add WHERE conditions
        if table.filters:
            conditions = []
            for field, value in table.filters.items():
                if isinstance(value, str):
                    conditions.append(f"{field} = '{value}'")
                else:
                    conditions.append(f"{field} = {value}")
            
            if conditions:
                query += f" WHERE {' AND '.join(conditions)}"
        
        # Add ORDER BY
        if table.sort_by:
            query += f" ORDER BY {table.sort_by}"
        
        # Execute query
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Get column names
        columns = [description[0] for description in cursor.description]
        
        # Fetch data
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        return [dict(zip(columns, row)) for row in rows]
    
    def _transform_row(self, row: Dict[str, Any], table: ExportTable) -> Dict[str, Any]:
        """Transform row data according to field mappings"""
        transformed = {}
        
        for field in table.fields:
            # Use target_field as key since SQL aliasing changes the column names in the result
            value = row.get(field.target_field, field.default_value)
            
            # Apply transformation if specified
            if field.transform and hasattr(self.transformers, field.transform):
                transform_func = getattr(self.transformers, field.transform)
                value = transform_func(value)
            
            # Apply format if specified
            if field.format and value is not None:
                if field.data_type == 'date' and field.format:
                    try:
                        from datetime import datetime
                        if isinstance(value, str):
                            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                            value = dt.strftime(field.format)
                    except:
                        pass
                elif field.data_type in ['float', 'integer'] and field.format:
                    try:
                        if field.data_type == 'float':
                            value = format(float(value), field.format)
                        else:
                            value = format(int(value), field.format)
                    except:
                        pass
            
            transformed[field.target_field] = value
        
        return transformed
    
    def _get_sql_type(self, data_type: str) -> str:
        """Convert field data type to SQL type"""
        type_mapping = {
            'string': 'TEXT',
            'integer': 'INTEGER',
            'float': 'REAL',
            'boolean': 'BOOLEAN',
            'date': 'TEXT'  # Store as ISO string
        }
        return type_mapping.get(data_type, 'TEXT')
    
    def preview_export(self, schema: ExportSchema, limit: int = 10) -> Dict[str, Any]:
        """Preview export data without creating files"""
        preview_data = {}
        
        with sqlite3.connect(self.database_path) as conn:
            for table in schema.tables:
                data = self._extract_table_data(conn, table)
                
                # Limit rows for preview
                limited_data = data[:limit]
                transformed_data = [self._transform_row(row, table) for row in limited_data]
                
                preview_data[table.export_name] = {
                    'fields': [field.target_field for field in table.fields],
                    'sample_data': transformed_data,
                    'total_rows_available': len(data)
                }
        
        return {
            'success': True,
            'schema': schema.name,
            'preview': preview_data
        }