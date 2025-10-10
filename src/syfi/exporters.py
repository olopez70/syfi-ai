"""
Data exporters for SyFi AI.

This module provides export functionality for synthetic banking data
including pipe-delimited, CSV, JSON, and other formats.
"""

import csv
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

from .database import DatabaseManager

class DataExporter:
    """
    Exports synthetic banking data to various file formats.
    
    Supports multiple export formats and schemas for different use cases.
    """
    
    def __init__(self, database_manager: DatabaseManager, output_dir: Path):
        """
        Initialize data exporter.
        
        Args:
            database_manager: DatabaseManager instance for data access
            output_dir: Directory for exported files
        """
        self.db_manager = database_manager
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Define export schemas
        self.schemas = {
            'standard': {
                'customers': ['customer_id', 'first_name', 'last_name', 'email', 
                            'phone', 'date_of_birth', 'created_date'],
                'accounts': ['account_id', 'customer_id', 'account_number', 
                           'account_type', 'balance', 'currency', 'created_date'],
                'transactions': ['transaction_id', 'account_id', 'transaction_type', 
                               'amount', 'description', 'category', 'merchant_name',
                               'transaction_date', 'posted_date']
            },
            'banking': {
                'customers': ['customer_id', 'first_name', 'last_name', 'email',
                            'phone', 'date_of_birth', 'city', 'state', 'zip_code'],
                'accounts': ['account_id', 'customer_id', 'account_number',
                           'account_type', 'balance', 'available_balance', 
                           'currency', 'opened_date', 'is_active'],
                'transactions': ['transaction_id', 'account_id', 'transaction_type',
                               'amount', 'currency', 'description', 'category',
                               'merchant_name', 'merchant_category', 'transaction_date',
                               'posted_date', 'reference_number', 'balance_after']
            },
            'audit': {
                'customers': ['customer_id', 'first_name', 'last_name', 'email',
                            'created_date', 'metadata'],
                'accounts': ['account_id', 'customer_id', 'account_number',
                           'account_type', 'balance', 'created_date', 'is_active',
                           'metadata'],
                'transactions': ['transaction_id', 'account_id', 'transaction_type',
                               'amount', 'description', 'transaction_date',
                               'posted_date', 'reference_number', 'metadata']
            }
        }
    
    def export_customers(self, format: str = 'pipe', schema: str = 'standard') -> Optional[Path]:
        """
        Export customers data to file.
        
        Args:
            format: Export format ('pipe', 'csv', 'json')
            schema: Export schema ('standard', 'banking', 'audit')
            
        Returns:
            Path to exported file
        """
        customers = self.db_manager.get_all_customers()
        if not customers:
            return None
        
        # Filter columns based on schema
        columns = self.schemas[schema]['customers']
        filtered_data = [
            {col: row.get(col) for col in columns if col in row}
            for row in customers
        ]
        
        # Export based on format
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'pipe':
            filename = f'customers_{schema}_{timestamp}.txt'
            file_path = self.output_dir / filename
            self._export_pipe_delimited(filtered_data, file_path, columns)
            
        elif format == 'csv':
            filename = f'customers_{schema}_{timestamp}.csv'
            file_path = self.output_dir / filename
            self._export_csv(filtered_data, file_path, columns)
            
        elif format == 'json':
            filename = f'customers_{schema}_{timestamp}.json'
            file_path = self.output_dir / filename
            self._export_json(filtered_data, file_path)
        
        return file_path
    
    def export_accounts(self, format: str = 'pipe', schema: str = 'standard') -> Optional[Path]:
        """
        Export accounts data to file.
        
        Args:
            format: Export format ('pipe', 'csv', 'json')
            schema: Export schema ('standard', 'banking', 'audit')
            
        Returns:
            Path to exported file
        """
        accounts = self.db_manager.get_all_accounts()
        if not accounts:
            return None
        
        # Filter columns based on schema
        columns = self.schemas[schema]['accounts']
        filtered_data = [
            {col: row.get(col) for col in columns if col in row}
            for row in accounts
        ]
        
        # Export based on format
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'pipe':
            filename = f'accounts_{schema}_{timestamp}.txt'
            file_path = self.output_dir / filename
            self._export_pipe_delimited(filtered_data, file_path, columns)
            
        elif format == 'csv':
            filename = f'accounts_{schema}_{timestamp}.csv'
            file_path = self.output_dir / filename
            self._export_csv(filtered_data, file_path, columns)
            
        elif format == 'json':
            filename = f'accounts_{schema}_{timestamp}.json'
            file_path = self.output_dir / filename
            self._export_json(filtered_data, file_path)
        
        return file_path
    
    def export_transactions(self, format: str = 'pipe', schema: str = 'standard',
                           start_date: Optional[str] = None, 
                           end_date: Optional[str] = None) -> Optional[Path]:
        """
        Export transactions data to file.
        
        Args:
            format: Export format ('pipe', 'csv', 'json')
            schema: Export schema ('standard', 'banking', 'audit')
            start_date: Optional start date filter (YYYY-MM-DD)
            end_date: Optional end date filter (YYYY-MM-DD)
            
        Returns:
            Path to exported file
        """
        # Get transactions (with optional date filtering)
        if start_date and end_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            transactions = self.db_manager.get_transactions_for_period(start, end)
        else:
            # Get all transactions
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions ORDER BY transaction_date")
            transactions = [dict(row) for row in cursor.fetchall()]
        
        if not transactions:
            return None
        
        # Filter columns based on schema
        columns = self.schemas[schema]['transactions']
        filtered_data = [
            {col: row.get(col) for col in columns if col in row}
            for row in transactions
        ]
        
        # Export based on format
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        date_suffix = f"_{start_date}_to_{end_date}" if start_date and end_date else ""
        
        if format == 'pipe':
            filename = f'transactions_{schema}{date_suffix}_{timestamp}.txt'
            file_path = self.output_dir / filename
            self._export_pipe_delimited(filtered_data, file_path, columns)
            
        elif format == 'csv':
            filename = f'transactions_{schema}{date_suffix}_{timestamp}.csv'
            file_path = self.output_dir / filename
            self._export_csv(filtered_data, file_path, columns)
            
        elif format == 'json':
            filename = f'transactions_{schema}{date_suffix}_{timestamp}.json'
            file_path = self.output_dir / filename
            self._export_json(filtered_data, file_path)
        
        return file_path
    
    def _export_pipe_delimited(self, data: List[Dict[str, Any]], 
                              file_path: Path, columns: List[str]):
        """Export data as pipe-delimited file."""
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            # Write header
            f.write('|'.join(columns) + '\n')
            
            # Write data rows
            for row in data:
                values = []
                for col in columns:
                    value = row.get(col, '')
                    # Convert to string and escape pipes
                    if value is None:
                        value = ''
                    else:
                        value = str(value).replace('|', '\\|')
                    values.append(value)
                
                f.write('|'.join(values) + '\n')
    
    def _export_csv(self, data: List[Dict[str, Any]], 
                   file_path: Path, columns: List[str]):
        """Export data as CSV file."""
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            
            for row in data:
                # Filter row to only include schema columns
                filtered_row = {col: row.get(col, '') for col in columns}
                writer.writerow(filtered_row)
    
    def _export_json(self, data: List[Dict[str, Any]], file_path: Path):
        """Export data as JSON file."""
        # Convert datetime objects to strings for JSON serialization
        serializable_data = []
        for row in data:
            serializable_row = {}
            for key, value in row.items():
                if isinstance(value, datetime):
                    serializable_row[key] = value.isoformat()
                else:
                    serializable_row[key] = value
            serializable_data.append(serializable_row)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, indent=2, default=str)
    
    def generate_export_summary(self) -> Path:
        """
        Generate a summary report of the exported data.
        
        Returns:
            Path to summary file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary_file = self.output_dir / f'export_summary_{timestamp}.txt'
        
        # Gather statistics
        customers_count = self.db_manager.count_customers()
        accounts_count = self.db_manager.count_accounts()
        transactions_count = self.db_manager.count_transactions()
        date_range = self.db_manager.get_transaction_date_range()
        
        # Calculate database size
        db_size = Path(self.db_manager.db_path).stat().st_size / 1024  # KB
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("SyFi AI - Export Summary Report\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Database: {self.db_manager.db_path}\n")
            f.write(f"Output Directory: {self.output_dir.absolute()}\n\n")
            
            f.write("Data Statistics:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total Customers: {customers_count:,}\n")
            f.write(f"Total Accounts: {accounts_count:,}\n")
            f.write(f"Total Transactions: {transactions_count:,}\n")
            
            if date_range:
                f.write(f"Transaction Period: {date_range[0]} to {date_range[1]}\n")
            
            if customers_count > 0:
                f.write(f"Avg Accounts per Customer: {accounts_count/customers_count:.1f}\n")
            
            f.write(f"Database Size: {db_size:.1f} KB\n\n")
            
            f.write("Export Configuration:\n")
            f.write("-" * 25 + "\n")
            f.write("Available Schemas: standard, banking, audit\n")
            f.write("Available Formats: pipe, csv, json\n\n")
            
            f.write("Schema Definitions:\n")
            f.write("-" * 20 + "\n")
            for schema_name, schema_def in self.schemas.items():
                f.write(f"\n{schema_name.upper()} Schema:\n")
                for table_name, columns in schema_def.items():
                    f.write(f"  {table_name}: {', '.join(columns)}\n")
            
            # List exported files
            exported_files = list(self.output_dir.glob('*_{}.txt'.format(timestamp.split('_')[0])))
            exported_files.extend(list(self.output_dir.glob('*_{}.csv'.format(timestamp.split('_')[0]))))
            exported_files.extend(list(self.output_dir.glob('*_{}.json'.format(timestamp.split('_')[0]))))
            
            if exported_files:
                f.write(f"\nExported Files (this session):\n")
                f.write("-" * 35 + "\n")
                for file_path in sorted(exported_files):
                    size_kb = file_path.stat().st_size / 1024
                    f.write(f"  {file_path.name} ({size_kb:.1f} KB)\n")
        
        return summary_file
    
    def export_all(self, format: str = 'pipe', schema: str = 'standard') -> Dict[str, Path]:
        """
        Export all data types (customers, accounts, transactions).
        
        Args:
            format: Export format ('pipe', 'csv', 'json')
            schema: Export schema ('standard', 'banking', 'audit')
            
        Returns:
            Dictionary mapping data type to exported file path
        """
        exported_files = {}
        
        # Export customers
        customers_file = self.export_customers(format=format, schema=schema)
        if customers_file:
            exported_files['customers'] = customers_file
        
        # Export accounts
        accounts_file = self.export_accounts(format=format, schema=schema)
        if accounts_file:
            exported_files['accounts'] = accounts_file
        
        # Export transactions
        transactions_file = self.export_transactions(format=format, schema=schema)
        if transactions_file:
            exported_files['transactions'] = transactions_file
        
        # Generate summary
        summary_file = self.generate_export_summary()
        exported_files['summary'] = summary_file
        
        return exported_files

# Export the DataExporter class
__all__ = ['DataExporter']