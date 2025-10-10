# SyFi AI Examples

This directory contains example scripts demonstrating the SyFi AI banking data generation system using the clean ProfileBuilder API.

## Available Examples

### clean_api_demo.py ⭐ **START HERE**
**Simple demonstration** of the clean SyFi AI API:
```python
# 1. Create template
template = create_young_professional_template()

# 2. Build profile  
builder = ProfileBuilder(seed=2025)
profile = builder.build_profile(template, "The Smith Family")

# 3. Generate banking data
data_generator = BankingDataGenerator(db_manager)
result = data_generator.generate_banking_data(profile, start_date, end_date)
```

### example_complete_workflow.py 🚀 **COMPREHENSIVE**
**Complete end-to-end demonstration** showing the full SyFi AI workflow:
- Create profile templates using `create_young_professional_template()`
- Use `ProfileBuilder` to generate detailed customer profiles 
- Use `BankingDataGenerator` to create customers, accounts, and transactions
- Store data in SQLite database and query results
- Generate comprehensive reports and analytics

### profile_example.py
Legacy example showing how to create customer profiles (older API).

### profile_database.py  
Legacy example demonstrating database operations (older API).

## Running Examples

Make sure you're in the project root directory and run:

```bash
# Quick API demo (recommended first) - 30 seconds
python examples/clean_api_demo.py

# Complete workflow - comprehensive demo
python examples/example_complete_workflow.py

# Legacy examples
python examples/profile_example.py
python examples/profile_database.py
```

## Clean API Overview

SyFi AI now provides a clean, easy-to-use API:

### Core Classes
- **`ProfileBuilder`** - Builds detailed profiles from templates
- **`BankingDataGenerator`** - Generates banking data from profiles  
- **`create_young_professional_template()`** - Built-in template function

### Basic Workflow
1. Create or use a profile template
2. Use ProfileBuilder to generate profiles
3. Use BankingDataGenerator to create banking data
4. Query and analyze the results

## What You'll See

The complete workflow example generates:
- **3 family profiles** with realistic household data
- **6 customers** (spouses in each family)
- **18 accounts** (checking + savings for each customer)
- **147 transactions** covering all of January 2025
- **Detailed reports** with transaction analytics

All data is stored in SQLite databases and can be explored with the web interface or SQL queries.