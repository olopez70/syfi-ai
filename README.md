# SyFi AI - Synthetic Financial Data Generator

A comprehensive Python library and CLI tool for generating realistic synthetic banking data with natural language configuration.

## Features

- **CLI Interface**: Independent workflow steps for database operations
- **Natural Language Processing**: Configure data generation using plain English
- **Banking Domain Models**: Comprehensive customer, account, and 2. I want a Navigation Bar item named "Bulk Generations". Within Bulk Generations I want sub-menu items called (a) Bulk Generation which creates and runs a bulk generation and (b) Bulk Generation History.
transaction models  
- **SQLite Database**: Persistent storage with proper relational schema
- **Multiple Export Formats**: Pipe-delimited, CSV, JSON output formats
- **Deterministic Generation**: Reproducible results with seed control
- **Class-based Architecture**: Clean, extensible design for easy integration

## CLI Workflow

SyFi AI provides a complete CLI interface for independent execution of banking data generation steps:

### Step 0: Initialize Database
```bash
python syfi_cli.py init --database ./syfi_banking.db
```
Creates a new SQLite database with proper schema for customers, accounts, and transactions.

### Step 1: Create Customers and Accounts
```bash
# Basic customer generation
python syfi_cli.py create-customers --database ./syfi_banking.db --customers 100 --accounts-per-customer 2

# Profile-based customer generation
python syfi_cli.py create-customers --database ./syfi_banking.db --customers 50 --profile "Two income households with 2 adults, 1-4 children, 0-2 pets, mortgage, 1-2 car loans, and 1-4 credit cards"
```
Generates synthetic customer profiles with associated bank accounts. Use the `--profile` option to generate customers matching specific demographic and financial profiles.

### Step 2: Generate Transactions (First Period)
```bash
python syfi_cli.py generate-transactions --database ./syfi_banking.db --start-date 2024-01-01 --end-date 2024-01-31 --transactions-per-day 150
```
Creates realistic banking transactions for a specified time period.

### Step 3: Add More Customers
```bash
# Basic additional customers
python syfi_cli.py add-customers --database ./syfi_banking.db --customers 50

# Profile-based additional customers
python syfi_cli.py add-customers --database ./syfi_banking.db --customers 25 --profile "Single professionals, age 25-40, high income, urban, tech workers"
```
Adds additional customers and accounts to expand the dataset. Use `--profile` to add customers with specific characteristics.

### Step 4: Generate More Transactions (Second Period)
```bash
python syfi_cli.py generate-transactions --database ./syfi_banking.db --start-date 2024-02-01 --end-date 2024-02-29 --transactions-per-day 200
```
Generates transactions for another time period with updated customer base.

### Step 5: Export Banking Data
```bash
python syfi_cli.py export --database ./syfi_banking.db --output-dir ./exports --format pipe --schema banking
```
Exports all banking data to pipe-delimited files with banking schema.

### Check Database Status
```bash
python syfi_cli.py status --database ./syfi_banking.db
```
Shows current database statistics and data summary.

## Installation

```bash
pip install -r requirements.txt
```

## Profile-Based Customer Generation

SyFi AI supports natural language profile descriptions to generate customers with specific characteristics. This allows you to create realistic datasets that match your testing or analysis requirements.

### Profile Description Examples

```bash
# Family households
--profile "Two income households with 2 adults, 1-4 children, 0-2 pets, mortgage, 1-2 car loans, and 1-4 credit cards"

# Young professionals  
--profile "Single professionals, age 25-40, high income, urban, tech workers"

# Retirees
--profile "Retired couples, age 65+, single income, savings-focused, conservative spending"

# Students
--profile "College students, age 18-22, part-time employment, low income, minimal credit"
```

### Profile Features

The profile parser automatically extracts and generates:

**Household Composition:**
- Number of adults (1-2 adults)
- Number of children (0-4 children) 
- Number of pets (0-2 pets)
- Total household size

**Financial Profile:**
- Income ranges based on employment type
- Employment status (dual income, single income, retired, etc.)
- Marital status (married, single, divorced)

**Banking Products:**
- Checking and savings accounts (always included)
- Credit cards (1-4 credit cards based on profile)
- Investment accounts (for higher income profiles)
- Mortgage and car loan indicators

**Profile Storage:**
- Original profile description stored in database
- Structured household data (adults, children, pets)
- Income and employment information
- Profile tags for easy filtering and analysis

### Database Schema for Profiles

The enhanced customer table includes:
- `household_size`, `num_adults`, `num_children`, `num_pets`
- `household_income`, `employment_status`, `marital_status`  
- `profile_description` (original natural language)
- `profile_tags` (JSON array of extracted characteristics)

## Export Formats and Schemas

### Formats
- **pipe**: Pipe-delimited text files (|)
- **csv**: Comma-separated values
- **json**: JavaScript Object Notation

### Schemas
- **standard**: Basic fields for general use
- **banking**: Extended banking-specific fields including household data
- **audit**: Minimal fields for audit purposes

## Python API Usage

```python
from src.syfi import SyFiGenerator
from src.syfi.database import DatabaseManager

# Initialize database
db_manager = DatabaseManager("banking_data.db")
db_manager.initialize_schema()

# Generate customers with profiles
from src.syfi.generators import CustomerGenerator
customer_gen = CustomerGenerator()

# Basic generation
customers, accounts = customer_gen.generate_customers(count=100)

# Profile-based generation
profile_desc = "Two income households with 2 adults, 1-4 children, mortgage and credit cards"
profile_customers, profile_accounts = customer_gen.generate_customers(
    count=50, 
    profile_description=profile_desc
)

db_manager.insert_customers(customers + profile_customers)
db_manager.insert_accounts(accounts + profile_accounts)

# Generate transactions
from src.syfi.generators import TransactionEngine
from datetime import date
transaction_engine = TransactionEngine(db_manager)
transactions = transaction_engine.generate_transactions_for_period(
    start_date=date(2024, 1, 1),
    end_date=date(2024, 1, 31),
    target_per_day=150
)

# Export data
from src.syfi.exporters import DataExporter
from pathlib import Path
exporter = DataExporter(db_manager, Path("./exports"))
exported_files = exporter.export_all(format='pipe', schema='banking')
```

## Configuration Examples

### Natural Language Configuration
```python
generator = SyFiGenerator()
config = generator.parse_requirements(
    "Generate 1000 customers with checking accounts and 6 months of transactions"
)
```

### JSON Configuration
```json
{
    "customers": {
        "count": 1000,
        "demographics": {
            "age_range": [18, 75],
            "locations": ["US", "CA"]
        }
    },
    "accounts": {
        "types": ["checking", "savings", "credit"],
        "distribution": [0.6, 0.3, 0.1]
    },
    "transactions": {
        "duration_months": 6,
        "categories": ["grocery", "gas", "utilities", "entertainment"]
    }
}
```

## Architecture

- **CLI Interface**: `syfi_cli.py` - Complete workflow management
- **Database Layer**: `DatabaseManager` - SQLite operations and schema
- **Data Generation**: `CustomerGenerator`, `TransactionEngine` - Realistic data creation
- **Export System**: `DataExporter` - Multiple format support
- **Models**: `Customer`, `Account`, `Transaction` - Banking domain objects
- **Configuration**: `ConfigurationParser` - Natural language processing

## File Structure

```
syfi-ai/
├── syfi_cli.py              # Main CLI interface
├── src/syfi/
│   ├── __init__.py           # Main SyFiGenerator class
│   ├── database.py           # SQLite database operations
│   ├── generators.py         # Customer and transaction generation
│   ├── exporters.py          # Data export functionality
│   ├── core/
│   │   ├── config.py         # Configuration management
│   │   └── parser.py         # Natural language processing
│   └── models/
│       └── __init__.py       # Banking domain models
├── tests/                    # Unit tests
├── examples/                 # Configuration examples
└── docs/                     # Documentation
```

## Web Interface

SyFi AI includes a comprehensive web-based database browser for exploring generated data:

### Features
- **Customer Search**: Search by ID, name, email, phone, address, and profile attributes
- **Customer Details**: Complete profile information with demographics and financial data  
- **Account Management**: View all customer accounts with balances and transaction counts
- **Account Details**: Transaction history, analytics, and account-specific information
- **Multi-Database Support**: Switch between different database files dynamically

### Starting the Web Interface

```bash
# Using the launcher script
./start_web_browser.sh

# Or manually
source .venv/bin/activate
python web_browser.py

# Or using VS Code task
# Run Task: "Start Web Database Browser"
```

Access the interface at **http://localhost:5000**

### Database Compatibility
The web interface automatically handles different database schemas:
- Legacy 13-column customer tables (backward compatible)
- Enhanced 22-column customer tables with detailed profiles
- Missing column graceful fallbacks for different database versions

See [WEB_INTERFACE.md](WEB_INTERFACE.md) for complete documentation.

## Testing

```bash
python -m pytest tests/ -v
```

## Dependencies

- **click**: CLI framework
- **rich**: Beautiful terminal output
- **sqlalchemy**: Database ORM
- **faker**: Realistic data generation
- **pytest**: Testing framework

## License

MIT License - See LICENSE file for details.