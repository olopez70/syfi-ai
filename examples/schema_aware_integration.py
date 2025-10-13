"""
Example integration of schema management into existing profiling components.

This demonstrates how to refactor existing database code to use schema-aware patterns.
"""

from pathlib import Path
from src.syfi.schema_management.schema_aware_db import SchemaAwareConnection
from src.syfi.schema_management.schema_manager import get_schema_manager, SCHEMA_DEFINITIONS, SchemaVersion


class SchemaAwareProfileAnalyzer:
    """
    Example of integrating schema management into profiling components.
    
    This shows the pattern for refactoring existing components to be schema-aware.
    """
    
    def __init__(self, db_path: str):
        """Initialize with schema validation."""
        self.db_path = Path(db_path)
        self.db = SchemaAwareConnection(db_path)
        self.schema_manager = get_schema_manager(db_path)
        
        # Validate compatibility on initialization
        self._validate_schema_compatibility()
    
    def _validate_schema_compatibility(self):
        """Validate database schema before operations."""
        # Check for minimum required schema
        required_schema = SCHEMA_DEFINITIONS[SchemaVersion.V1_0_BASIC]
        issues = self.schema_manager.validate_schema_compatibility(required_schema)
        
        if issues['missing_tables']:
            raise RuntimeError(
                f"Missing required tables: {issues['missing_tables']}. "
                f"Please ensure database contains at least: customers, accounts"
            )
    
    def get_customer_profiles(self):
        """Get customer profiles with schema-aware column access."""
        if not self.db.table_exists('customers'):
            return []
        
        # Build adaptive query based on available columns
        base_columns = ['customer_id', 'first_name', 'last_name']
        optional_columns = {
            'email': 'NULL',
            'profile_description': 'NULL'
        }
        
        query = self.db.adaptive_query(
            "SELECT {columns} FROM customers",
            'customers',
            required_columns=base_columns,
            optional_columns=optional_columns
        )
        
        if not query:
            return []
        
        results = self.db.safe_execute(query)
        return [dict(zip(['customer_id', 'first_name', 'last_name', 'email', 'profile_description'], row)) 
                for row in (results or [])]
    
    def get_account_metrics(self):
        """Calculate account metrics with schema fallbacks."""
        if not self.db.table_exists('accounts'):
            return {
                'total_accounts': 0,
                'total_balance': 0.0,
                'average_balance': 0.0,
                'account_status_breakdown': {'active': 0, 'inactive': 0, 'total': 0}
            }
        
        # Basic metrics that work with any schema version
        total_accounts = self.db.safe_count('accounts')
        
        # Balance calculations with safe column access
        balance_query = None
        if self.db.column_exists('accounts', 'balance'):
            balance_query = "SELECT SUM(balance), AVG(balance) FROM accounts"
        
        if balance_query:
            balance_results = self.db.safe_execute(balance_query)
            total_balance = balance_results[0][0] if balance_results and balance_results[0][0] else 0.0
            average_balance = balance_results[0][1] if balance_results and balance_results[0][1] else 0.0
        else:
            total_balance = 0.0
            average_balance = 0.0
        
        # Status breakdown using schema-aware calculation
        from src.syfi.schema_management.schema_aware_db import SchemaAwareMetricsCalculator
        calculator = SchemaAwareMetricsCalculator(self.db)
        status_breakdown = calculator.calculate_account_status()
        
        return {
            'total_accounts': total_accounts,
            'total_balance': total_balance,
            'average_balance': average_balance,
            'account_status_breakdown': status_breakdown
        }
    
    def get_transaction_summary(self):
        """Get transaction summary with graceful table handling."""
        if not self.db.table_exists('transactions'):
            return {
                'total_transactions': 0,
                'transaction_volume': 0.0,
                'transaction_types': {}
            }
        
        total_transactions = self.db.safe_count('transactions')
        
        # Volume calculation
        volume_query = None
        if self.db.column_exists('transactions', 'amount'):
            volume_query = "SELECT SUM(ABS(amount)) FROM transactions"
        
        transaction_volume = 0.0
        if volume_query:
            volume_results = self.db.safe_execute(volume_query)
            transaction_volume = volume_results[0][0] if volume_results and volume_results[0][0] else 0.0
        
        # Transaction types breakdown
        types_breakdown = {}
        if self.db.column_exists('transactions', 'transaction_type'):
            types_query = "SELECT transaction_type, COUNT(*) FROM transactions GROUP BY transaction_type"
            types_results = self.db.safe_execute(types_query)
            if types_results:
                types_breakdown = {row[0]: row[1] for row in types_results}
        
        return {
            'total_transactions': total_transactions,
            'transaction_volume': transaction_volume,
            'transaction_types': types_breakdown
        }
    
    def generate_comprehensive_report(self):
        """Generate complete profile report with all available data."""
        # Detect current schema version for reporting
        current_version = self.schema_manager.get_current_schema_version()
        
        report = {
            'database_info': {
                'path': str(self.db_path),
                'schema_version': current_version.value,
                'schema_name': current_version.name
            },
            'customer_profiles': self.get_customer_profiles(),
            'account_metrics': self.get_account_metrics(),
            'transaction_summary': self.get_transaction_summary()
        }
        
        # Add schema compatibility warnings
        enhanced_schema = SCHEMA_DEFINITIONS[SchemaVersion.V1_2_ENHANCED]
        compatibility_issues = self.schema_manager.validate_schema_compatibility(enhanced_schema)
        
        if compatibility_issues['missing_tables'] or compatibility_issues['missing_columns']:
            report['schema_warnings'] = {
                'missing_tables': compatibility_issues['missing_tables'],
                'missing_columns': compatibility_issues['missing_columns'],
                'recommendation': 'Consider upgrading to enhanced schema for full feature support'
            }
        
        return report


class LegacyComponentMigrationHelper:
    """
    Helper for migrating existing components to schema-aware patterns.
    
    Provides common migration patterns and utilities.
    """
    
    @staticmethod
    def wrap_existing_component(component_class, db_path: str):
        """
        Wrap an existing component class with schema awareness.
        
        Args:
            component_class: Original component class
            db_path: Database path
        
        Returns:
            Enhanced component instance with schema management
        """
        # Create the original component
        original_component = component_class(db_path)
        
        # Add schema management attributes
        original_component.schema_manager = get_schema_manager(db_path)
        original_component.schema_aware_db = SchemaAwareConnection(db_path)
        
        # Replace direct database access methods
        original_component._safe_execute = original_component.schema_aware_db.safe_execute
        original_component._safe_count = original_component.schema_aware_db.safe_count
        original_component._table_exists = original_component.schema_aware_db.table_exists
        original_component._column_exists = original_component.schema_aware_db.column_exists
        
        return original_component
    
    @staticmethod
    def migrate_hardcoded_queries(queries: dict, db: SchemaAwareConnection) -> dict:
        """
        Migrate hardcoded SQL queries to schema-aware versions.
        
        Args:
            queries: Dict of query names to SQL strings
            db: Schema-aware database connection
            
        Returns:
            Dict of migrated queries
        """
        migrated = {}
        
        for name, query in queries.items():
            # Example migration patterns
            if 'status' in query and not db.column_exists('accounts', 'status'):
                # Replace status column with is_active or default handling
                if db.column_exists('accounts', 'is_active'):
                    migrated[name] = query.replace('status', 'is_active')
                else:
                    # Use default active status
                    migrated[name] = query.replace(
                        "WHERE status = 'active'", 
                        "WHERE 1=1"  # All accounts considered active
                    )
            else:
                migrated[name] = query
        
        return migrated
    
    @staticmethod
    def create_compatibility_shim(db_path: str):
        """
        Create a compatibility shim for legacy code.
        
        Returns a database connection that handles common schema variations.
        """
        db = SchemaAwareConnection(db_path)
        
        class CompatibilityShim:
            def __init__(self, schema_aware_db):
                self._db = schema_aware_db
            
            def execute(self, query, params=None):
                """Execute with automatic schema adaptation."""
                # Common adaptations
                adapted_query = query
                
                # Handle status vs is_active
                if 'accounts.status' in query and not self._db.column_exists('accounts', 'status'):
                    if self._db.column_exists('accounts', 'is_active'):
                        adapted_query = query.replace('accounts.status', 'accounts.is_active')
                    else:
                        # Default to active for all accounts
                        adapted_query = query.replace(
                            "accounts.status = 'active'", 
                            "1=1"
                        )
                
                return self._db.safe_execute(adapted_query, params)
            
            def count(self, table, condition=None, params=None):
                """Safe counting with existence checks."""
                return self._db.safe_count(table, condition, params)
        
        return CompatibilityShim(db)


# Example usage and migration guide
if __name__ == "__main__":
    # Example 1: Using the new schema-aware analyzer
    analyzer = SchemaAwareProfileAnalyzer("path/to/database.sqlite")
    report = analyzer.generate_comprehensive_report()
    print("Database Report:", report)
    
    # Example 2: Migrating existing component
    # from old_module import LegacyProfileAnalyzer
    # migrated_analyzer = LegacyComponentMigrationHelper.wrap_existing_component(
    #     LegacyProfileAnalyzer, "path/to/database.sqlite"
    # )
    
    # Example 3: Using compatibility shim for legacy code
    compat_db = LegacyComponentMigrationHelper.create_compatibility_shim("path/to/database.sqlite")
    # Legacy code can now use compat_db.execute() safely