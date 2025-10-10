# Profile and ProfileTemplate Models Documentation

## Overview

The Profile and ProfileTemplate models extend the SyFi banking system to support AI-driven customer profile generation. These models enable the creation of detailed, realistic banking scenarios from natural language descriptions.

## Model Architecture

### ProfileTemplate
A `ProfileTemplate` contains a natural language description provided by the user that describes a banking customer or group of customers (e.g., household, business network).

**Key Fields:**
- `template_id`: Unique identifier for the template
- `name`: Short descriptive name
- `description`: Natural language description of the customer scenario
- `category`: Type of scenario ("household", "individual", "business", "network")
- `complexity_level`: Complexity indicator ("simple", "medium", "complex")
- `usage_count`: How many times this template has been used
- `tags`: List of descriptive tags for organization

### Profile
A `Profile` is generated from a `ProfileTemplate` and contains detailed characteristics of customers, accounts, and transaction patterns. It has sufficient information to create Customer, Account, and Transaction records.

**Key Fields:**
- `profile_id`: Unique identifier for the profile
- `template_id`: Reference to the source ProfileTemplate
- `household_type`: Type of household ("individual", "household", "family", "business")
- `total_members`: Total number of people in the household/group
- `banking_members`: Number of people who are actual banking customers
- `customers_data`: List of detailed customer information (semi-structured)
- `accounts_data`: List of detailed account information (semi-structured)
- `transaction_profiles`: Dictionary mapping customers to their TransactionProfile objects
- `customer_relationships`: Relationships between customers and accounts
- `credit_profile`: Credit and financial characteristics

### TransactionProfile
A `TransactionProfile` describes the transaction patterns and behaviors for a specific customer within a Profile.

**Key Fields:**
- `income_sources`: List of income patterns (salary, business, etc.)
- `spending_categories`: Dictionary of spending patterns by category
- `transaction_frequency`: Timing and frequency patterns
- `preferred_payment_methods`: List of preferred payment methods

## Example Usage

### 1. Creating a ProfileTemplate

```python
from src.syfi.models import ProfileTemplate

template = ProfileTemplate(
    name="Suburban Median Income Household",
    description="""A suburban household of approximately median US income, 
    and moderate spending. The bank provides the households primary banking 
    needs which include checking accounts, savings accounts, credit cards, 
    and mortgage.""",
    category="household",
    complexity_level="medium",
    tags=["suburban", "median_income", "family", "mortgage"]
)
```

### 2. Creating a Detailed Profile

```python
from src.syfi.models import Profile, TransactionProfile
from decimal import Decimal

profile = Profile(
    template_id=template.template_id,
    name="Doe Family Household Profile",
    household_type="family",
    total_members=6,
    banking_members=3,
    household_income=Decimal('85000')
)

# Add customer data
profile.add_customer_data({
    "customer_key": "john_doe",
    "first_name": "John",
    "last_name": "Doe",
    "age": 48,
    "role": "father",
    "employment": "salaried_employee",
    "annual_income": Decimal('55000'),
    "is_banking_customer": True
})

# Add account data
profile.add_account_data({
    "account_key": "joint_checking",
    "account_type": "checking",
    "ownership_type": "joint",
    "owners": ["john_doe", "jane_doe"],
    "balance": Decimal('3500.00')
})

# Add transaction profile
john_tx_profile = TransactionProfile()
john_tx_profile.income_sources = [{
    "type": "salary",
    "amount": Decimal('2291.67'),
    "frequency": "bi_monthly",
    "description": "Direct deposit salary"
}]
profile.add_transaction_profile("john_doe", john_tx_profile)
```

### 3. Generating Customer Records

```python
from src.syfi.models import Customer

# Generate actual Customer records from Profile data
customers = []
for customer_data in profile.get_banking_customers():
    customer = Customer(
        first_name=customer_data["first_name"],
        last_name=customer_data["last_name"],
        date_of_birth=customer_data.get("date_of_birth"),
        employment_status=customer_data.get("employment", ""),
        household_income=profile.household_income
    )
    customers.append(customer)
```

## Database Integration

The models can be stored in SQLite using the provided `ProfileDatabase` utility:

```python
from examples.profile_database import ProfileDatabase

# Initialize database
profile_db = ProfileDatabase("data/syfi_banking.db")

# Save template and profile
profile_db.save_template(template)
profile_db.save_profile(profile)

# Load from database
loaded_template = profile_db.load_template(template.template_id)
loaded_profile = profile_db.load_profile(profile.profile_id)

# List all templates and profiles
all_templates = profile_db.list_templates()
all_profiles = profile_db.list_profiles()
```

## Data Structure Examples

### Customer Data Structure
```python
customer_data = {
    "customer_key": "john_doe",
    "first_name": "John",
    "last_name": "Doe",
    "age": 48,
    "role": "father",
    "employment": "salaried_employee",
    "employer": "Tech Corporation",
    "annual_income": Decimal('55000'),
    "is_banking_customer": True,
    "date_of_birth": date(1977, 3, 15)
}
```

### Account Data Structure
```python
account_data = {
    "account_key": "joint_checking",
    "account_type": "checking",
    "ownership_type": "joint",
    "owners": ["john_doe", "jane_doe"],
    "balance": Decimal('3500.00'),
    "interest_rate": Decimal('0.01'),
    "monthly_fee": Decimal('0.00'),
    "description": "Primary household checking account"
}
```

### Transaction Profile Structure
```python
transaction_profile = {
    "income_sources": [
        {
            "type": "salary",
            "amount": Decimal('2291.67'),
            "frequency": "bi_monthly",
            "description": "Direct deposit salary",
            "account": "joint_checking"
        }
    ],
    "spending_categories": {
        "mortgage": {
            "avg_amount": Decimal('1773.40'),
            "frequency": "monthly",
            "variability": "none"
        },
        "groceries": {
            "avg_amount": Decimal('150.00'),
            "frequency": "weekly",
            "variability": "medium"
        }
    },
    "preferred_payment_methods": ["debit_card", "auto_pay", "check"]
}
```

## Integration with Existing Models

The Profile models work seamlessly with existing Customer, Account, and Transaction models:

1. **ProfileTemplate** → Natural language input
2. **Profile** → Detailed structured data
3. **Customer, Account, Transaction** → Generated banking records

This hierarchy allows for:
- Template reuse across multiple profile generations
- Consistent data structures for database storage
- Easy generation of realistic banking scenarios
- Flexible customer and household modeling

## Use Cases

1. **Testing and Development**: Generate realistic test data for banking applications
2. **Demo Scenarios**: Create compelling demo data for presentations
3. **Stress Testing**: Generate large numbers of realistic customer profiles
4. **Training Data**: Create diverse datasets for machine learning models
5. **Customer Simulation**: Model different types of banking customers and behaviors

## Files

- `src/syfi/models/__init__.py`: Model definitions
- `examples/profile_example.py`: Comprehensive example showing model usage
- `examples/profile_database.py`: Database integration utilities
- `docs/PROFILE_MODELS.md`: This documentation file

The Profile and ProfileTemplate models provide a powerful foundation for generating realistic banking scenarios from natural language descriptions, enabling sophisticated customer modeling and data generation capabilities.