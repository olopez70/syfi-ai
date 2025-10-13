# Database Schema Management Framework

## Overview

This document describes the comprehensive database schema management framework implemented to prevent database schema alignment issues that were causing runtime errors throughout the SyFi AI system.

## Problem Statement

During Issue #5 test coverage improvements, many failures were caused by:
- **Hardcoded Database Queries**: Direct SQL with assumed column names (`status` vs `is_active`)
- **Missing Table Handling**: Code assuming tables exist without verification
- **Schema Variations**: Different database configurations causing runtime errors
- **No Graceful Degradation**: Components crashing instead of handling missing schema elements

## Solution Architecture

### 1. Schema Versioning System (`src/syfi/schema_management/schema_manager.py`)

```python
class SchemaVersion(Enum):
    V1_0_BASIC = "1.0_basic"          # customers + accounts (minimal)
    V1_1_STANDARD = "1.1_standard"    # + transactions
    V1_2_ENHANCED = "1.2_enhanced"    # + optional columns (status, profile_description)
```

**Key Features:**
- **Automatic Detection**: Analyzes existing database to determine schema version
- **Compatibility Validation**: Checks required vs available tables/columns
- **Migration Planning**: Identifies missing components for upgrades
- **Version Definitions**: Structured schema requirements for each version

### 2. Schema-Aware Database Operations (`src/syfi/schema_management/schema_aware_db.py`)

```python
class SchemaAwareConnection:
    def table_exists(self, table_name: str) -> bool
    def column_exists(self, table: str, column: str) -> bool
    def safe_execute(self, query: str, params=None, fallback_result=None)
    def safe_count(self, table: str, condition=None, params=None) -> int
    def adaptive_query(self, query_template: str, table: str, 
                      required_columns: List[str], optional_columns: Dict[str, Any] = None)
```

**Key Features:**
- **Existence Checking**: Verify tables/columns before operations
- **Safe Execution**: Graceful handling of missing schema elements
- **Query Adaptation**: Build queries that work with available schema
- **Caching**: Performance optimization for repeated schema checks

### 3. Schema-Aware Metrics Calculator

```python
class SchemaAwareMetricsCalculator:
    def calculate_account_status(self) -> Dict[str, int]:
        # Tries multiple fallback strategies:
        # 1. Use 'status' column if available
        # 2. Use 'is_active' column if available  
        # 3. Use balance > 0 as proxy for active
        # 4. Default all accounts to active
```

## Implementation Patterns

### Required Development Practices

1. **Always Check Table Existence**
```python
if db.table_exists('accounts'):
    # Perform operations
else:
    # Provide fallback or skip gracefully
```

2. **Validate Column Availability**
```python
status_column = 'status' if db.column_exists('accounts', 'status') else 'is_active'
```

3. **Use Adaptive Queries**
```python
query = db.adaptive_query(
    "SELECT {columns} FROM {table}",
    'accounts',
    required_columns=['account_id'],
    optional_columns={'status': "'unknown'"}
)
```

4. **Provide Graceful Fallbacks**
```python
def get_account_metrics():
    if not db.table_exists('accounts'):
        return {'total': 0, 'active': 0, 'inactive': 0}
    # ... continue with operations
```

### Migration Pattern for Existing Components

```python
# Before (brittle)
cursor.execute("SELECT status FROM accounts WHERE account_id = ?", (id,))

# After (schema-aware) 
from src.syfi.schema_management import SchemaAwareConnection
db = SchemaAwareConnection(db_path)
if db.column_exists('accounts', 'status'):
    result = db.safe_execute("SELECT status FROM accounts WHERE account_id = ?", (id,))
else:
    # Fallback logic for missing column
```

## Testing Strategy

### Multi-Schema Test Coverage (`tests/database/test_schema_management.py`)

- **Schema Detection Tests**: Verify correct version identification
- **Compatibility Validation**: Test missing table/column detection  
- **Safe Operations**: Confirm graceful handling of missing elements
- **Adaptive Queries**: Validate query building with various schemas
- **Fallback Strategies**: Test all fallback paths in metrics calculations

### Test Database Configurations

1. **Empty Database**: No tables (V1.0_BASIC detected)
2. **Minimal Schema**: customers + accounts only
3. **Standard Schema**: + transactions table
4. **Enhanced Schema**: + optional columns (status, profile_description)
5. **Mixed Configurations**: Missing specific columns or tables

## Integration Guidelines

### For New Components

```python
from src.syfi.schema_management import SchemaAwareConnection, get_schema_manager

class NewComponent:
    def __init__(self, db_path: str):
        self.db = SchemaAwareConnection(db_path)
        self.schema_manager = get_schema_manager(db_path)
        self._validate_minimum_schema()
    
    def _validate_minimum_schema(self):
        # Check for required components
        required_schema = SCHEMA_DEFINITIONS[SchemaVersion.V1_0_BASIC]
        issues = self.schema_manager.validate_schema_compatibility(required_schema)
        
        if issues['missing_tables']:
            raise RuntimeError(f"Missing required tables: {issues['missing_tables']}")
```

### For Existing Components

1. **Wrap Existing Classes**: Use `LegacyComponentMigrationHelper.wrap_existing_component()`
2. **Replace Direct Queries**: Migrate hardcoded SQL to schema-aware patterns
3. **Add Validation**: Include schema compatibility checks
4. **Test Multi-Schema**: Validate against different database configurations

## Benefits Achieved

### ✅ **Prevents Runtime Errors**
- No more crashes from missing tables/columns
- Graceful degradation when schema elements unavailable
- Safe operations with comprehensive error handling

### ✅ **Enables Schema Evolution** 
- Backward compatibility with existing databases
- Forward compatibility for new schema versions
- Systematic migration path planning

### ✅ **Improves Testing Reliability**
- Tests work with any valid database configuration  
- No schema-dependent test failures
- Comprehensive coverage of schema variations

### ✅ **Supports Development Workflow**
- Clear guidelines for database-accessing code
- Automated validation and compatibility checking
- Integration examples and migration helpers

## Usage Examples

### Schema Detection and Validation

```python
from src.syfi.schema_management import get_schema_manager, SCHEMA_DEFINITIONS, SchemaVersion

# Detect current database schema
manager = get_schema_manager("path/to/database.sqlite")
current_version = manager.get_current_schema_version()
print(f"Database schema: {current_version.name}")

# Validate compatibility
required_schema = SCHEMA_DEFINITIONS[SchemaVersion.V1_2_ENHANCED]
issues = manager.validate_schema_compatibility(required_schema)

if issues['missing_tables']:
    print(f"Missing tables: {issues['missing_tables']}")
if issues['missing_columns']:
    print(f"Missing columns: {issues['missing_columns']}")
```

### Safe Database Operations

```python
from src.syfi.schema_management import SchemaAwareConnection

db = SchemaAwareConnection("path/to/database.sqlite")

# Safe counting
total_accounts = db.safe_count('accounts')  # Returns 0 if table missing

# Conditional operations
if db.table_exists('transactions'):
    transactions = db.safe_execute("SELECT * FROM transactions LIMIT 10")
else:
    print("Transactions table not available")

# Adaptive queries
query = db.adaptive_query(
    "SELECT {columns} FROM customers",
    'customers',
    required_columns=['customer_id', 'first_name', 'last_name'],
    optional_columns={'email': 'NULL', 'profile_description': 'NULL'}
)
```

## Future Enhancements

1. **Automatic Migration**: Tools to upgrade databases to newer schema versions
2. **Performance Optimization**: Enhanced caching and query optimization
3. **Schema Documentation**: Automatic generation of schema documentation
4. **Validation Rules**: Custom validation rules for specific business logic

## Conclusion

The database schema management framework provides a robust foundation for handling database schema variations throughout the SyFi AI system. It prevents runtime errors, enables graceful degradation, and supports systematic schema evolution while maintaining backward compatibility.

**Key Implementation**: All database-accessing components should use `SchemaAwareConnection` instead of direct SQLite operations, and follow the established patterns for schema validation and graceful fallbacks.