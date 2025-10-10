#!/usr/bin/env python3
"""
Example demonstrating the Profile and ProfileTemplate models.

This example shows how to create a ProfileTemplate from a natural language description,
then generate a detailed Profile that contains enough information to create Customer,
Account, and Transaction records.
"""

from decimal import Decimal
from datetime import datetime, date
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.syfi.models import (
    ProfileTemplate, Profile, TransactionProfile,
    Customer, Account, Transaction,
    AccountType, TransactionType, TransactionCategory
)

def create_example_profile_template():
    """Create an example ProfileTemplate based on the suburban household description."""
    
    template = ProfileTemplate(
        name="Suburban Median Income Household",
        description="""A suburban household of approximately median US income, and moderate spending. 
        The bank provides the households primary banking needs which include but are not limited to 
        checking accounts, savings accounts, credit cards, and mortgage. Over time the household may 
        upgrade or switch to new accounts offered by the bank.""",
        created_by="system",
        category="household",
        complexity_level="medium",
        tags=["suburban", "median_income", "family", "mortgage", "moderate_spending"]
    )
    
    return template

def create_detailed_profile_from_template(template: ProfileTemplate):
    """Create a detailed Profile based on the ProfileTemplate."""
    
    profile = Profile(
        template_id=template.template_id,
        name="Doe Family Household Profile",
        description="Detailed profile for the Doe family suburban household",
        household_type="family",
        total_members=6,  # 2 adults + 3 children + 1 dog
        banking_members=3,  # John, Jane, Linda
        household_income=Decimal('85000'),  # Approximate median US household income
        generation_seed=12345
    )
    
    # Add customer data for family members
    customers_data = [
        {
            "customer_key": "john_doe",
            "first_name": "John",
            "last_name": "Doe", 
            "age": 48,
            "role": "father",
            "employment": "salaried_employee",
            "employer": "Tech Corporation",
            "annual_income": Decimal('55000'),
            "is_banking_customer": True,
            "date_of_birth": date(1977, 3, 15),
            "ssn_last_4": "1234"
        },
        {
            "customer_key": "jane_doe",
            "first_name": "Jane",
            "last_name": "Doe",
            "age": 46,
            "role": "mother", 
            "employment": "sole_proprietor",
            "business": "Jane's Dog Grooming",
            "annual_income": Decimal('30000'),
            "is_banking_customer": True,
            "date_of_birth": date(1979, 7, 22),
            "ssn_last_4": "5678"
        },
        {
            "customer_key": "linda_doe",
            "first_name": "Linda",
            "last_name": "Doe",
            "age": 15,
            "role": "daughter",
            "employment": "student",
            "is_banking_customer": True,
            "date_of_birth": date(2010, 12, 3),
            "account_type": "teen_checking"
        },
        {
            "customer_key": "samuel_doe", 
            "first_name": "Samuel",
            "last_name": "Doe",
            "age": 12,
            "role": "son",
            "employment": "student",
            "is_banking_customer": False
        },
        {
            "customer_key": "oscar_doe",
            "first_name": "Oscar", 
            "last_name": "Doe",
            "age": 8,
            "role": "son",
            "employment": "student",
            "is_banking_customer": False
        }
    ]
    
    for customer_data in customers_data:
        profile.add_customer_data(customer_data)
    
    # Add account data
    accounts_data = [
        {
            "account_key": "joint_checking",
            "account_type": "checking",
            "ownership_type": "joint",
            "owners": ["john_doe", "jane_doe"],
            "primary_owner": "john_doe",
            "balance": Decimal('3500.00'),
            "interest_rate": Decimal('0.01'),
            "monthly_fee": Decimal('0.00'),
            "description": "Primary household checking account"
        },
        {
            "account_key": "joint_savings",
            "account_type": "savings", 
            "ownership_type": "joint",
            "owners": ["john_doe", "jane_doe"],
            "primary_owner": "john_doe",
            "balance": Decimal('15000.00'),
            "interest_rate": Decimal('2.5'),
            "monthly_fee": Decimal('0.00'),
            "description": "Emergency fund and savings"
        },
        {
            "account_key": "jane_checking",
            "account_type": "checking",
            "ownership_type": "individual", 
            "owners": ["jane_doe"],
            "balance": Decimal('2800.00'),
            "interest_rate": Decimal('0.01'),
            "monthly_fee": Decimal('5.00'),
            "description": "Jane's business checking account"
        },
        {
            "account_key": "linda_teen_checking",
            "account_type": "teen_checking",
            "ownership_type": "individual",
            "owners": ["linda_doe"],
            "balance": Decimal('150.00'),
            "interest_rate": Decimal('0.00'),
            "monthly_fee": Decimal('0.00'),
            "description": "Linda's teen checking account"
        },
        {
            "account_key": "mortgage",
            "account_type": "mortgage_loan",
            "ownership_type": "joint", 
            "owners": ["john_doe", "jane_doe"],
            "original_amount": Decimal('350000.00'),
            "current_balance": Decimal('245000.00'),  # After 11 years of payments
            "interest_rate": Decimal('4.5'),
            "term_years": 30,
            "years_remaining": 19,
            "monthly_payment": Decimal('1773.40'),
            "description": "Primary residence mortgage"
        },
        {
            "account_key": "credit_card_1",
            "account_type": "credit_card",
            "ownership_type": "joint",
            "owners": ["john_doe", "jane_doe"],
            "credit_limit": Decimal('15000.00'),
            "current_balance": Decimal('0.00'),  # Paid off monthly
            "interest_rate": Decimal('19.0'),
            "annual_fee": Decimal('0.00'),
            "description": "Primary rewards credit card - paid monthly"
        },
        {
            "account_key": "credit_card_2", 
            "account_type": "credit_card",
            "ownership_type": "joint",
            "owners": ["john_doe", "jane_doe"],
            "credit_limit": Decimal('25000.00'),
            "current_balance": Decimal('15000.00'),  # Carrying balance
            "interest_rate": Decimal('27.0'),
            "minimum_payment": Decimal('450.00'),
            "description": "Second credit card - carrying balance"
        }
    ]
    
    for account_data in accounts_data:
        profile.add_account_data(account_data)
    
    # Create transaction profiles for each banking customer
    
    # John's transaction profile
    john_tx_profile = TransactionProfile()
    john_tx_profile.income_sources = [
        {
            "type": "salary",
            "amount": Decimal('2291.67'),  # Monthly after taxes
            "frequency": "bi_monthly",  # Twice per month
            "description": "Direct deposit salary",
            "account": "joint_checking",
            "timing": "15th and last day of month"
        }
    ]
    john_tx_profile.spending_categories = {
        "mortgage": {"avg_amount": Decimal('1773.40'), "frequency": "monthly", "variability": "none"},
        "utilities": {"avg_amount": Decimal('180.00'), "frequency": "monthly", "variability": "low"},
        "insurance": {"avg_amount": Decimal('320.00'), "frequency": "monthly", "variability": "none"},
        "gas": {"avg_amount": Decimal('120.00'), "frequency": "weekly", "variability": "medium"}
    }
    john_tx_profile.preferred_payment_methods = ["debit_card", "auto_pay", "check"]
    profile.add_transaction_profile("john_doe", john_tx_profile)
    
    # Jane's transaction profile  
    jane_tx_profile = TransactionProfile()
    jane_tx_profile.income_sources = [
        {
            "type": "business_revenue",
            "amount": Decimal('2500.00'),  # Monthly average
            "frequency": "variable", 
            "description": "Dog grooming business income",
            "account": "jane_checking",
            "payment_methods": ["cash", "check", "venmo", "paypal", "zelle", "apple_pay"]
        }
    ]
    jane_tx_profile.spending_categories = {
        "business_supplies": {"avg_amount": Decimal('200.00'), "frequency": "monthly", "variability": "medium"},
        "groceries": {"avg_amount": Decimal('150.00'), "frequency": "weekly", "variability": "medium"},
        "transfer_to_joint": {"avg_amount": Decimal('2000.00'), "frequency": "monthly", "variability": "low"}
    }
    jane_tx_profile.preferred_payment_methods = ["mobile_payment", "debit_card", "cash"]
    jane_tx_profile.transaction_frequency = {
        "transfer_to_joint": "first_week_of_month",
        "business_income": "throughout_month",
        "business_expenses": "as_needed"
    }
    profile.add_transaction_profile("jane_doe", jane_tx_profile)
    
    # Linda's transaction profile
    linda_tx_profile = TransactionProfile()
    linda_tx_profile.income_sources = [
        {
            "type": "allowance",
            "amount": Decimal('50.00'),
            "frequency": "weekly",
            "description": "Weekly allowance from parents",
            "account": "linda_teen_checking"
        }
    ]
    linda_tx_profile.spending_categories = {
        "entertainment": {"avg_amount": Decimal('25.00'), "frequency": "weekly", "variability": "high"},
        "food": {"avg_amount": Decimal('15.00'), "frequency": "weekly", "variability": "medium"},
        "clothing": {"avg_amount": Decimal('40.00'), "frequency": "monthly", "variability": "high"}
    }
    linda_tx_profile.preferred_payment_methods = ["debit_card", "mobile_payment"]
    profile.add_transaction_profile("linda_doe", linda_tx_profile)
    
    # Define customer relationships
    profile.customer_relationships = {
        "joint_accounts": {
            "joint_checking": ["john_doe", "jane_doe"],
            "joint_savings": ["john_doe", "jane_doe"],
            "mortgage": ["john_doe", "jane_doe"],
            "credit_card_1": ["john_doe", "jane_doe"], 
            "credit_card_2": ["john_doe", "jane_doe"]
        },
        "authorized_users": {
            "credit_card_1": ["jane_doe"],  # Jane authorized on John's card
        },
        "dependencies": {
            "linda_doe": ["john_doe", "jane_doe"]  # Linda depends on parents
        }
    }
    
    # Add life events that affect banking behavior
    profile.life_events = [
        {
            "event": "home_purchase",
            "date": "2014-01-15",
            "description": "Purchased primary residence with mortgage",
            "impact": "Added mortgage account, increased monthly expenses"
        },
        {
            "event": "business_start",
            "date": "2018-06-01", 
            "description": "Jane started dog grooming business",
            "impact": "Added business checking account, variable income"
        },
        {
            "event": "teen_account",
            "date": "2023-09-01",
            "description": "Opened teen checking for Linda", 
            "impact": "Added teen account, teaching financial responsibility"
        }
    ]
    
    # Credit profile information
    profile.credit_profile = {
        "john_credit_score": 750,
        "jane_credit_score": 720,
        "payment_history": "excellent",
        "credit_utilization": 60,  # $15k balance on $40k total limits
        "length_of_history": "15+ years"
    }
    
    profile.tags = ["suburban", "family", "moderate_income", "mortgage_holders", "small_business"]
    
    return profile

def demonstrate_customer_generation(profile: Profile):
    """Demonstrate how to generate actual Customer records from Profile data."""
    
    print("=== Generated Customer Records ===")
    customers = []
    
    for customer_data in profile.get_banking_customers():
        customer = Customer(
            first_name=customer_data["first_name"],
            last_name=customer_data["last_name"],
            date_of_birth=customer_data.get("date_of_birth"),
            employment_status=customer_data.get("employment", ""),
            household_income=profile.household_income,
            household_size=profile.total_members,
            num_adults=2,
            num_children=3,
            num_pets=1,
            profile_description=f"Generated from profile: {profile.name}"
        )
        customers.append(customer)
        print(f"Customer: {customer.full_name} (ID: {customer.customer_id})")
        print(f"  Age: {customer_data['age']}, Role: {customer_data['role']}")
        print(f"  Employment: {customer_data.get('employment', 'N/A')}")
        print()
    
    return customers

def demonstrate_account_generation(profile: Profile, customers: list):
    """Demonstrate how to generate actual Account records from Profile data."""
    
    print("=== Generated Account Records ===")
    accounts = []
    
    # Create a mapping of customer keys to customer IDs
    customer_map = {}
    for i, customer_data in enumerate(profile.get_banking_customers()):
        customer_map[customer_data["customer_key"]] = customers[i].customer_id
    
    for account_data in profile.accounts_data:
        # Determine primary customer for account
        primary_owner = account_data.get("primary_owner") or account_data["owners"][0]
        customer_id = customer_map.get(primary_owner, customers[0].customer_id)
        
        # Map account types
        account_type_map = {
            "checking": AccountType.CHECKING,
            "savings": AccountType.SAVINGS,
            "teen_checking": AccountType.CHECKING,
            "credit_card": AccountType.CREDIT,
            "mortgage_loan": AccountType.LOAN
        }
        
        # Get balance from either "balance" or "current_balance" field
        balance = account_data.get("balance") or account_data.get("current_balance", Decimal('0.00'))
        
        account = Account(
            account_type=account_type_map.get(account_data["account_type"], AccountType.CHECKING),
            customer_id=customer_id,
            balance=balance,
            available_balance=balance
        )
        
        accounts.append(account)
        print(f"Account: {account.account_number} ({account_data['account_type']})")
        print(f"  Owner: {primary_owner} -> {customer_id}")
        print(f"  Balance: ${account.balance}")
        if account_data.get("interest_rate"):
            print(f"  Interest Rate: {account_data['interest_rate']}%")
        print()
    
    return accounts

def main():
    """Main demonstration function."""
    
    print("Profile and ProfileTemplate Model Demonstration")
    print("=" * 50)
    
    # Step 1: Create ProfileTemplate
    print("1. Creating ProfileTemplate from natural language description...")
    template = create_example_profile_template()
    print(f"Template: {template.name}")
    print(f"Description: {template.description}")
    print()
    
    # Step 2: Generate detailed Profile
    print("2. Generating detailed Profile from template...")
    profile = create_detailed_profile_from_template(template)
    print(f"Profile: {profile.name}")
    print(f"Household type: {profile.household_type}")
    print(f"Total members: {profile.total_members}")
    print(f"Banking members: {profile.banking_members}")
    print(f"Household income: ${profile.household_income}")
    print()
    
    # Step 3: Show detailed profile structure
    print("3. Profile Structure Details...")
    print(f"Customers: {len(profile.customers_data)} people")
    for customer in profile.customers_data:
        banking_status = "Banking Customer" if customer.get("is_banking_customer") else "Non-banking"
        print(f"  - {customer['first_name']} {customer['last_name']} ({customer['age']} yo, {customer['role']}) - {banking_status}")
    
    print(f"\nAccounts: {len(profile.accounts_data)} accounts")
    for account in profile.accounts_data:
        owners = ", ".join(account["owners"])
        balance = account.get("balance", account.get("current_balance", "N/A"))
        print(f"  - {account['account_type']} ({account['ownership_type']}) - Owners: {owners} - Balance: ${balance}")
    
    print(f"\nTransaction Profiles: {len(profile.transaction_profiles)} profiles")
    for customer_key, tx_profile in profile.transaction_profiles.items():
        income_count = len(tx_profile.income_sources)
        spending_count = len(tx_profile.spending_categories)
        print(f"  - {customer_key}: {income_count} income sources, {spending_count} spending categories")
    
    print()
    
    # Step 4: Generate actual records
    print("4. Generating actual Customer and Account records...")
    customers = demonstrate_customer_generation(profile)
    accounts = demonstrate_account_generation(profile, customers)
    
    # Step 5: Show conversion to dict (for storage/API)
    print("5. Profile serialization example...")
    profile_dict = profile.to_dict()
    print(f"Profile dict keys: {list(profile_dict.keys())}")
    print(f"Profile dict size: {len(str(profile_dict))} characters")
    print()
    
    print("Demonstration complete!")
    print("This Profile now contains sufficient information to generate:")
    print("- 3 Customer records (John, Jane, Linda)")
    print("- 7 Account records (checking, savings, credit cards, mortgage)")
    print("- Hundreds of Transaction records based on transaction profiles")

if __name__ == "__main__":
    main()