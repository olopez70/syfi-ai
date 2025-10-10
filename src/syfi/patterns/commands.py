"""
Command Pattern Implementation for Export Operations

Provides encapsulated, undoable, and queueable export operations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json


class Command(ABC):
    """Abstract command interface."""
    
    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """Execute the command."""
        pass
    
    @abstractmethod
    def undo(self) -> bool:
        """Undo the command if possible."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get human-readable description of the command."""
        pass


class ExportCommand(Command):
    """Base class for export commands."""
    
    def __init__(self, db_manager, output_path: Path):
        self.db_manager = db_manager
        self.output_path = output_path
        self.executed_at: Optional[datetime] = None
        self.result: Optional[Dict[str, Any]] = None
    
    def undo(self) -> bool:
        """Default undo implementation - removes the created file."""
        if self.output_path.exists():
            try:
                self.output_path.unlink()
                return True
            except Exception:
                return False
        return True


class ExportCustomersCommand(ExportCommand):
    """Command to export customers to various formats."""
    
    def __init__(self, db_manager, output_path: Path, 
                 format_type: str = 'json', filters: Optional[Dict] = None):
        super().__init__(db_manager, output_path)
        self.format_type = format_type.lower()
        self.filters = filters or {}
    
    def execute(self) -> Dict[str, Any]:
        """Execute customer export."""
        self.executed_at = datetime.now()
        
        # Get customers data
        customers = self.db_manager.get_all_customers()
        
        # Apply filters if provided
        if self.filters:
            customers = self._apply_filters(customers)
        
        # Export based on format
        if self.format_type == 'json':
            self._export_json(customers)
        elif self.format_type == 'csv':
            self._export_csv(customers)
        elif self.format_type == 'xml':
            self._export_xml(customers)
        else:
            raise ValueError(f"Unsupported format: {self.format_type}")
        
        self.result = {
            'format': self.format_type,
            'record_count': len(customers),
            'output_file': str(self.output_path),
            'executed_at': self.executed_at.isoformat(),
            'filters_applied': self.filters
        }
        
        return self.result
    
    def _apply_filters(self, customers: List[Dict]) -> List[Dict]:
        """Apply filters to customer data."""
        filtered = customers
        
        if 'min_income' in self.filters:
            filtered = [c for c in filtered 
                       if c.get('household_income', 0) >= self.filters['min_income']]
        
        if 'max_income' in self.filters:
            filtered = [c for c in filtered 
                       if c.get('household_income', float('inf')) <= self.filters['max_income']]
        
        if 'employment_status' in self.filters:
            filtered = [c for c in filtered 
                       if c.get('employment_status') == self.filters['employment_status']]
        
        return filtered
    
    def _export_json(self, customers: List[Dict]) -> None:
        """Export customers to JSON."""
        with open(self.output_path, 'w') as f:
            json.dump({
                'metadata': {
                    'export_type': 'customers',
                    'exported_at': self.executed_at.isoformat(),
                    'record_count': len(customers),
                    'filters': self.filters
                },
                'customers': customers
            }, f, indent=2, default=str)
    
    def _export_csv(self, customers: List[Dict]) -> None:
        """Export customers to CSV."""
        import csv
        
        if not customers:
            return
        
        with open(self.output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=customers[0].keys())
            writer.writeheader()
            writer.writerows(customers)
    
    def _export_xml(self, customers: List[Dict]) -> None:
        """Export customers to XML."""
        import xml.etree.ElementTree as ET
        
        root = ET.Element('customers')
        root.set('exported_at', self.executed_at.isoformat())
        root.set('count', str(len(customers)))
        
        for customer_data in customers:
            customer_elem = ET.SubElement(root, 'customer')
            for key, value in customer_data.items():
                elem = ET.SubElement(customer_elem, key)
                elem.text = str(value) if value is not None else ''
        
        tree = ET.ElementTree(root)
        tree.write(self.output_path, encoding='utf-8', xml_declaration=True)
    
    def get_description(self) -> str:
        """Get command description."""
        filter_desc = f" with filters: {self.filters}" if self.filters else ""
        return f"Export customers to {self.format_type.upper()} format{filter_desc}"


class ExportAccountsCommand(ExportCommand):
    """Command to export accounts data."""
    
    def __init__(self, db_manager, output_path: Path, 
                 format_type: str = 'json', customer_ids: Optional[List[str]] = None):
        super().__init__(db_manager, output_path)
        self.format_type = format_type.lower()
        self.customer_ids = customer_ids
    
    def execute(self) -> Dict[str, Any]:
        """Execute accounts export."""
        self.executed_at = datetime.now()
        
        # Get accounts data
        accounts = self.db_manager.get_all_accounts()
        
        # Filter by customer IDs if provided
        if self.customer_ids:
            accounts = [acc for acc in accounts 
                       if acc.get('customer_id') in self.customer_ids]
        
        # Export based on format
        if self.format_type == 'json':
            self._export_json(accounts)
        elif self.format_type == 'csv':
            self._export_csv(accounts)
        else:
            raise ValueError(f"Unsupported format: {self.format_type}")
        
        self.result = {
            'format': self.format_type,
            'record_count': len(accounts),
            'output_file': str(self.output_path),
            'executed_at': self.executed_at.isoformat(),
            'customer_filter': self.customer_ids
        }
        
        return self.result
    
    def _export_json(self, accounts: List[Dict]) -> None:
        """Export accounts to JSON."""
        with open(self.output_path, 'w') as f:
            json.dump({
                'metadata': {
                    'export_type': 'accounts',
                    'exported_at': self.executed_at.isoformat(),
                    'record_count': len(accounts)
                },
                'accounts': accounts
            }, f, indent=2, default=str)
    
    def _export_csv(self, accounts: List[Dict]) -> None:
        """Export accounts to CSV."""
        import csv
        
        if not accounts:
            return
        
        with open(self.output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=accounts[0].keys())
            writer.writeheader()
            writer.writerows(accounts)
    
    def get_description(self) -> str:
        """Get command description."""
        customer_desc = f" for {len(self.customer_ids)} customers" if self.customer_ids else ""
        return f"Export accounts to {self.format_type.upper()} format{customer_desc}"


class ExportTransactionsCommand(ExportCommand):
    """Command to export transactions data."""
    
    def __init__(self, db_manager, output_path: Path, 
                 format_type: str = 'json', date_range: Optional[tuple] = None,
                 account_ids: Optional[List[str]] = None):
        super().__init__(db_manager, output_path)
        self.format_type = format_type.lower()
        self.date_range = date_range
        self.account_ids = account_ids
    
    def execute(self) -> Dict[str, Any]:
        """Execute transactions export."""
        self.executed_at = datetime.now()
        
        # Get transactions data
        if self.date_range:
            transactions = self.db_manager.get_transactions_for_period(*self.date_range)
        else:
            transactions = self.db_manager.get_all_transactions()
        
        # Filter by account IDs if provided
        if self.account_ids:
            transactions = [tx for tx in transactions 
                           if tx.get('account_id') in self.account_ids]
        
        # Export based on format
        if self.format_type == 'json':
            self._export_json(transactions)
        elif self.format_type == 'csv':
            self._export_csv(transactions)
        else:
            raise ValueError(f"Unsupported format: {self.format_type}")
        
        self.result = {
            'format': self.format_type,
            'record_count': len(transactions),
            'output_file': str(self.output_path),
            'executed_at': self.executed_at.isoformat(),
            'date_range': self.date_range,
            'account_filter': self.account_ids
        }
        
        return self.result
    
    def _export_json(self, transactions: List[Dict]) -> None:
        """Export transactions to JSON."""
        with open(self.output_path, 'w') as f:
            json.dump({
                'metadata': {
                    'export_type': 'transactions',
                    'exported_at': self.executed_at.isoformat(),
                    'record_count': len(transactions),
                    'date_range': self.date_range
                },
                'transactions': transactions
            }, f, indent=2, default=str)
    
    def _export_csv(self, transactions: List[Dict]) -> None:
        """Export transactions to CSV."""
        import csv
        
        if not transactions:
            return
        
        with open(self.output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=transactions[0].keys())
            writer.writeheader()
            writer.writerows(transactions)
    
    def get_description(self) -> str:
        """Get command description."""
        date_desc = f" for period {self.date_range}" if self.date_range else ""
        account_desc = f" for {len(self.account_ids)} accounts" if self.account_ids else ""
        return f"Export transactions to {self.format_type.upper()} format{date_desc}{account_desc}"


class ExportFullDatabaseCommand(ExportCommand):
    """Command to export complete database."""
    
    def __init__(self, db_manager, output_path: Path, format_type: str = 'json'):
        super().__init__(db_manager, output_path)
        self.format_type = format_type.lower()
    
    def execute(self) -> Dict[str, Any]:
        """Execute full database export."""
        self.executed_at = datetime.now()
        
        # Get all data
        customers = self.db_manager.get_all_customers()
        accounts = self.db_manager.get_all_accounts()
        transactions = self.db_manager.get_all_transactions()
        
        if self.format_type == 'json':
            self._export_json(customers, accounts, transactions)
        else:
            raise ValueError(f"Unsupported format for full export: {self.format_type}")
        
        total_records = len(customers) + len(accounts) + len(transactions)
        
        self.result = {
            'format': self.format_type,
            'customers_count': len(customers),
            'accounts_count': len(accounts),
            'transactions_count': len(transactions),
            'total_records': total_records,
            'output_file': str(self.output_path),
            'executed_at': self.executed_at.isoformat()
        }
        
        return self.result
    
    def _export_json(self, customers: List[Dict], accounts: List[Dict], 
                    transactions: List[Dict]) -> None:
        """Export full database to JSON."""
        with open(self.output_path, 'w') as f:
            json.dump({
                'metadata': {
                    'export_type': 'full_database',
                    'exported_at': self.executed_at.isoformat(),
                    'customers_count': len(customers),
                    'accounts_count': len(accounts),
                    'transactions_count': len(transactions)
                },
                'customers': customers,
                'accounts': accounts,
                'transactions': transactions
            }, f, indent=2, default=str)
    
    def get_description(self) -> str:
        """Get command description."""
        return f"Export complete database to {self.format_type.upper()} format"


class MacroCommand(Command):
    """Command that executes multiple commands in sequence."""
    
    def __init__(self, commands: List[Command], description: str):
        self.commands = commands
        self.description = description
        self.executed_commands: List[Command] = []
    
    def execute(self) -> Dict[str, Any]:
        """Execute all commands in sequence."""
        results = []
        
        for command in self.commands:
            try:
                result = command.execute()
                self.executed_commands.append(command)
                results.append(result)
            except Exception as e:
                # Rollback executed commands on error
                self.undo()
                raise e
        
        return {
            'macro_description': self.description,
            'commands_executed': len(results),
            'results': results
        }
    
    def undo(self) -> bool:
        """Undo all executed commands in reverse order."""
        success = True
        
        for command in reversed(self.executed_commands):
            if not command.undo():
                success = False
        
        self.executed_commands.clear()
        return success
    
    def get_description(self) -> str:
        """Get macro command description."""
        return self.description


class CommandInvoker:
    """Invoker that manages command execution and history."""
    
    def __init__(self, max_history: int = 100):
        self.history: List[Command] = []
        self.max_history = max_history
    
    def execute_command(self, command: Command) -> Dict[str, Any]:
        """Execute a command and add to history."""
        result = command.execute()
        
        # Add to history
        self.history.append(command)
        
        # Trim history if needed
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        return result
    
    def undo_last(self) -> bool:
        """Undo the last command."""
        if not self.history:
            return False
        
        last_command = self.history[-1]
        success = last_command.undo()
        
        if success:
            self.history.pop()
        
        return success
    
    def get_history(self) -> List[str]:
        """Get command history descriptions."""
        return [cmd.get_description() for cmd in self.history]
    
    def clear_history(self) -> None:
        """Clear command history."""
        self.history.clear()


class ExportCommandFactory:
    """Factory for creating export commands."""
    
    @staticmethod
    def create_customer_export(db_manager, output_dir: Path, 
                              format_type: str = 'json', 
                              filters: Optional[Dict] = None) -> ExportCustomersCommand:
        """Create customer export command."""
        filename = f"customers_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"
        output_path = output_dir / filename
        return ExportCustomersCommand(db_manager, output_path, format_type, filters)
    
    @staticmethod
    def create_full_export_suite(db_manager, output_dir: Path, 
                               format_type: str = 'json') -> MacroCommand:
        """Create macro command for full export suite."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        commands = [
            ExportCustomersCommand(
                db_manager,
                output_dir / f"customers_{timestamp}.{format_type}",
                format_type
            ),
            ExportAccountsCommand(
                db_manager,
                output_dir / f"accounts_{timestamp}.{format_type}",
                format_type
            ),
            ExportTransactionsCommand(
                db_manager,
                output_dir / f"transactions_{timestamp}.{format_type}",
                format_type
            )
        ]
        
        return MacroCommand(commands, f"Export all data to {format_type.upper()} format")


# Usage Examples

def create_export_workflow(db_manager, output_dir: Path) -> CommandInvoker:
    """Create a pre-configured export workflow."""
    invoker = CommandInvoker()
    
    # Create standard export commands
    customer_export = ExportCommandFactory.create_customer_export(
        db_manager, output_dir, 'json'
    )
    
    full_suite = ExportCommandFactory.create_full_export_suite(
        db_manager, output_dir, 'json'
    )
    
    # Example usage:
    # invoker.execute_command(customer_export)
    # invoker.execute_command(full_suite)
    
    return invoker