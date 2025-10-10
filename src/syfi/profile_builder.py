"""
Profile Builder - Core functionality for building profiles from templates
and generating banking data from profiles.
"""

import random
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional

from .models import (
    ProfileTemplate, Profile, TransactionProfile,
    Customer, Account, Transaction,
    AccountType, TransactionType, TransactionCategory
)
from .database import DatabaseManager
from .generators import CustomerGenerator


class ProfileBuilder:
    """
    Builds detailed profiles from templates and generates banking data.
    """
    
    def __init__(self, db_manager: DatabaseManager, seed: Optional[int] = None):
        """
        Initialize ProfileBuilder.
        
        Args:
            db_manager: DatabaseManager instance for data storage
            seed: Random seed for reproducible generation
        """
        self.db_manager = db_manager
        self.seed = seed or random.randint(1000, 9999)
        
    def save_profile_template(self, template: ProfileTemplate) -> str:
        """
        Save profile template to database.
        
        Args:
            template: ProfileTemplate to save
            
        Returns:
            The template ID
        """
        # Determine entity type and category from template
        entity_type = "personal"  # Default
        category = "Personal"     # Default
        complexity = "Medium"     # Default
        
        if "business" in template.description.lower() or "restaurant" in template.description.lower() or "supermarket" in template.description.lower():
            entity_type = "business"
            category = "Business"
            complexity = "High" if "supermarket" in template.description.lower() else "Medium"
        elif "non-profit" in template.description.lower() or "nonprofit" in template.description.lower():
            entity_type = "non-profit"
            category = "Non-profit" 
            complexity = "Medium"
        
        # Extract typical accounts and transactions from description
        typical_accounts = ["Checking Account", "Savings Account"]
        typical_transactions = ["Regular deposits", "Bill payments", "Transfers"]
        
        if entity_type == "business":
            typical_accounts = ["Business Checking", "Business Savings", "Business Credit"]
            typical_transactions = ["Revenue deposits", "Vendor payments", "Payroll", "Equipment purchases"]
        elif entity_type == "non-profit":
            typical_accounts = ["Operating Account", "Grant Account", "Restricted Funds"]
            typical_transactions = ["Grant deposits", "Program expenses", "Administrative costs", "Fundraising"]
        
        # Determine icon and color
        icon = "🏠"  # Default family
        color = "primary"
        
        if "restaurant" in template.description.lower():
            icon = "🍽️"
            color = "success"
        elif "supermarket" in template.description.lower():
            icon = "🛒"
            color = "warning"
        elif "non-profit" in template.description.lower():
            icon = "❤️"
            color = "info"
        
        # Estimate income range
        income_range = "$50k - $150k"
        if entity_type == "business":
            income_range = "$500k - $5M" if "supermarket" in template.description.lower() else "$200k - $1M"
        elif entity_type == "non-profit":
            income_range = "$1M - $5M"
        
        return self.db_manager.insert_profile_template(
            template_id=template.template_id,
            name=template.name,
            description=template.description,
            entity_type=entity_type,
            category=category,
            complexity_level=complexity,
            icon=icon,
            color=color,
            typical_income_range=income_range,
            typical_accounts=typical_accounts,
            typical_transactions=typical_transactions,
            tags=template.tags if hasattr(template, 'tags') else [],
            metadata={}
        )

    def build_profile(self, template: ProfileTemplate, profile_name: str, **kwargs) -> Profile:
        """
        Build a detailed profile from a template.
        
        Args:
            template: ProfileTemplate to build from
            profile_name: Name for the generated profile
            **kwargs: Additional profile parameters
            
        Returns:
            Generated Profile with customers, accounts, and transaction patterns
        """
        # Set random seed for reproducible generation
        random.seed(self.seed)
        
        # Save template to database if not already saved
        self.save_profile_template(template)
        
        # Create base profile
        profile = Profile(
            template_id=template.template_id,
            name=profile_name,
            description=kwargs.get('description', f"Generated profile based on {template.name}"),
            household_type=kwargs.get('household_type', 'family'),
            total_members=kwargs.get('total_members', random.choice([3, 4])),  # 2 adults + 1-2 children
            banking_members=kwargs.get('banking_members', 2),  # Both adults are banking customers
            household_income=kwargs.get('household_income', Decimal(str(random.randint(85000, 150000)))),
            generation_seed=self.seed
        )
        
        # Save profile to database
        self._save_profile_to_database(profile)
        
        # Generate customer data based on template
        self._generate_customer_data(profile, template)
        
        # Generate account data based on template
        self._generate_account_data(profile, template)
        
        # Generate transaction profile based on template
        self._generate_transaction_profile(profile, template)
        
        return profile
        
    def _save_profile_to_database(self, profile: Profile) -> str:
        """Save profile instance to database."""
        return self.db_manager.insert_profile(
            profile_id=profile.profile_id,
            template_id=profile.template_id,
            name=profile.name,
            description=profile.description,
            parameters={
                "household_type": profile.household_type,
                "total_members": profile.total_members,
                "banking_members": profile.banking_members,
                "household_income": str(profile.household_income),
                "generation_seed": profile.generation_seed
            }
        )
    
    def _generate_customer_data(self, profile: Profile, template: ProfileTemplate) -> None:
        """Generate customer data for the profile based on template."""
        
        # Generate realistic customer demographics
        ages = [random.randint(28, 35), random.randint(26, 33)]
        first_names = [
            random.choice(["James", "Michael", "David", "John", "Robert", "Christopher", "Matthew"]),
            random.choice(["Mary", "Jennifer", "Lisa", "Michelle", "Sarah", "Jessica", "Ashley"])
        ]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
        last_name = random.choice(last_names)
        
        # Create customer data
        employment_options = [
            "Software Engineer", "Nurse", "Teacher", "Financial Analyst", 
            "Marketing Manager", "Project Manager", "Data Analyst", "Healthcare Professional"
        ]
        
        for i, (age, first_name) in enumerate(zip(ages, first_names)):
            profile.add_customer_data({
                "first_name": first_name,
                "last_name": last_name,
                "age": age,
                "employment_status": random.choice(employment_options),
                "role": "primary" if i == 0 else "spouse",
                "is_banking_customer": True
            })
    
    def _generate_account_data(self, profile: Profile, template: ProfileTemplate) -> None:
        """Generate account data for the profile based on template."""
        
        # Standard account structure for young professional families
        accounts_data = [
            {
                "account_type": "checking",
                "ownership": "joint",
                "primary_user": "both",
                "initial_balance": random.randint(2500, 8000),
                "purpose": "primary checking"
            },
            {
                "account_type": "savings",
                "ownership": "joint", 
                "primary_user": "both",
                "initial_balance": random.randint(15000, 45000),
                "purpose": "emergency fund"
            },
            {
                "account_type": "savings",
                "ownership": "joint",
                "primary_user": "both", 
                "initial_balance": random.randint(5000, 20000),
                "purpose": "children education fund"
            }
        ]
        
        for account_data in accounts_data:
            profile.add_account_data(account_data)
    
    def _generate_transaction_profile(self, profile: Profile, template: ProfileTemplate) -> None:
        """Generate transaction profile for the profile based on template."""
        
        tx_profile = TransactionProfile()
        
        # Income sources - split between primary and secondary earners
        tx_profile.income_sources = [
            {
                "type": "salary",
                "amount": float(profile.household_income) * 0.6,
                "frequency": "biweekly",
                "description": "Primary salary direct deposit"
            },
            {
                "type": "salary", 
                "amount": float(profile.household_income) * 0.4,
                "frequency": "biweekly",
                "description": "Secondary salary direct deposit"
            }
        ]
        
        # Spending categories based on household income and size
        monthly_mortgage = int(float(profile.household_income) * 0.25 / 12)  # 25% of income
        
        tx_profile.spending_categories = {
            "groceries": {"avg_amount": 150 + (profile.total_members * 25), "frequency": "weekly", "variability": "medium"},
            "gas": {"avg_amount": 80, "frequency": "weekly", "variability": "low"},
            "utilities": {"avg_amount": 200 + (profile.total_members * 50), "frequency": "monthly", "variability": "low"},
            "mortgage": {"avg_amount": monthly_mortgage, "frequency": "monthly", "variability": "none"},
            "childcare": {"avg_amount": 600 + ((profile.total_members - 2) * 200), "frequency": "monthly", "variability": "low"},
            "restaurant": {"avg_amount": 35 + (profile.total_members * 10), "frequency": "weekly", "variability": "high"},
            "entertainment": {"avg_amount": 80 + (profile.total_members * 20), "frequency": "monthly", "variability": "medium"},
            "shopping": {"avg_amount": 150 + (profile.total_members * 50), "frequency": "monthly", "variability": "high"}
        }
        
        profile.add_transaction_profile("household", tx_profile)


class BankingDataGenerator:
    """
    Generates actual banking data (customers, accounts, transactions) from profiles.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize BankingDataGenerator.
        
        Args:
            db_manager: DatabaseManager instance for data storage
        """
        self.db_manager = db_manager
    
    def generate_banking_data(self, profile: Profile, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Generate complete banking data from a profile for a date range.
        
        Args:
            profile: Profile to generate data from
            start_date: Start date for transaction generation
            end_date: End date for transaction generation
            
        Returns:
            Dictionary containing generated customers, accounts, transactions
        """
        # Generate customers based on profile data
        customers = self._generate_customers(profile)
        
        # Generate accounts based on profile data
        accounts = self._generate_accounts(profile, customers)
        
        # Store customers and accounts in database
        self.db_manager.insert_customers(customers)
        self.db_manager.insert_accounts(accounts)
        
        # Link profile to customers (use first customer as primary)
        if customers:
            self.db_manager.link_profile_to_customer(profile.profile_id, customers[0].customer_id)
        
        # Generate transactions for the date range
        transactions = self._generate_transactions(profile, accounts, start_date, end_date)
        
        return {
            "customers": customers,
            "accounts": accounts, 
            "transactions": transactions,
            "profile": profile
        }
    
    def _generate_customers(self, profile: Profile) -> List[Customer]:
        """Generate Customer objects from profile data."""
        customers = []
        
        for customer_data in profile.customers_data:
            customer = Customer(
                first_name=customer_data["first_name"],
                last_name=customer_data["last_name"],
                company_name=customer_data.get("company_name", ""),
                employment_status=customer_data["employment_status"],
                household_income=profile.household_income,
                household_size=profile.total_members
            )
            customers.append(customer)
        
        return customers
    
    def _generate_accounts(self, profile: Profile, customers: List[Customer]) -> List[Account]:
        """Generate Account objects from profile data."""
        accounts = []
        
        for customer in customers:
            for account_data in profile.accounts_data:
                account = Account(
                    customer_id=customer.customer_id,
                    account_type=AccountType(account_data["account_type"]),
                    balance=Decimal(str(account_data["initial_balance"])),
                    available_balance=Decimal(str(account_data["initial_balance"]))
                )
                accounts.append(account)
        
        return accounts
    
    def _generate_transactions(self, profile: Profile, accounts: List[Account], 
                             start_date: date, end_date: date) -> List[Transaction]:
        """Generate realistic transactions for the date range."""
        
        transactions = []
        random.seed(profile.generation_seed + 100)  # Offset seed for transactions
        
        # Get transaction profile
        tx_profile = profile.transaction_profiles.get("household")
        if not tx_profile:
            return transactions
        
        # Find primary checking account
        checking_accounts = [acc for acc in accounts if acc.account_type == AccountType.CHECKING]
        if not checking_accounts:
            return transactions
        
        primary_account = checking_accounts[0]
        current_balance = primary_account.balance
        
        # Generate transactions for each day in the date range
        current_date = start_date
        
        while current_date <= end_date:
            day_transactions = []
            
            # Salary deposits (biweekly, on Fridays)
            if current_date.weekday() == 4:  # Friday
                week_number = current_date.isocalendar()[1]
                if week_number % 2 == 1:  # Every other week
                    for income_source in tx_profile.income_sources:
                        amount = Decimal(str(income_source["amount"] / 26))  # Biweekly
                        current_balance += amount
                        
                        transaction = Transaction(
                            account_id=primary_account.account_id,
                            transaction_type=TransactionType.DEPOSIT,
                            amount=amount,
                            description=income_source["description"],
                            category=TransactionCategory.SALARY,
                            transaction_date=datetime.combine(current_date, datetime.min.time()),
                            balance_after=current_balance
                        )
                        day_transactions.append(transaction)
            
            # Monthly bills (first few days of month)
            if current_date.day <= 5:
                monthly_expenses = ["mortgage", "utilities", "childcare"]
                for expense in monthly_expenses:
                    if expense in tx_profile.spending_categories:
                        category_data = tx_profile.spending_categories[expense]
                        amount = Decimal(str(category_data["avg_amount"]))
                        current_balance -= amount
                        
                        transaction = Transaction(
                            account_id=primary_account.account_id,
                            transaction_type=TransactionType.PAYMENT,
                            amount=-amount,  # Negative for expenses
                            description=f"{expense.title()} payment",
                            category=TransactionCategory.UTILITIES if expense == "utilities" else TransactionCategory.OTHER,
                            merchant_name=f"{expense.title()} Company",
                            transaction_date=datetime.combine(current_date, datetime.min.time()),
                            balance_after=current_balance
                        )
                        day_transactions.append(transaction)
            
            # Weekly expenses (groceries, gas)
            if current_date.weekday() == 5:  # Saturday for groceries
                if "groceries" in tx_profile.spending_categories:
                    category_data = tx_profile.spending_categories["groceries"]
                    # Add some variability
                    base_amount = category_data["avg_amount"]
                    amount = Decimal(str(base_amount + random.randint(-30, 50)))
                    current_balance -= amount
                    
                    transaction = Transaction(
                        account_id=primary_account.account_id,
                        transaction_type=TransactionType.PAYMENT,
                        amount=-amount,
                        description="Grocery shopping",
                        category=TransactionCategory.GROCERY,
                        merchant_name=random.choice(["SuperMart", "Fresh Foods", "Family Grocers"]),
                        transaction_date=datetime.combine(current_date, datetime.min.time()),
                        balance_after=current_balance
                    )
                    day_transactions.append(transaction)
            
            # Gas (twice per week)
            if current_date.weekday() in [1, 4]:  # Tuesday and Friday
                if "gas" in tx_profile.spending_categories:
                    category_data = tx_profile.spending_categories["gas"]
                    amount = Decimal(str(category_data["avg_amount"] / 2 + random.randint(-10, 15)))
                    current_balance -= amount
                    
                    transaction = Transaction(
                        account_id=primary_account.account_id,
                        transaction_type=TransactionType.PAYMENT,
                        amount=-amount,
                        description="Gas purchase",
                        category=TransactionCategory.GAS,
                        merchant_name=random.choice(["Shell", "BP", "Exxon"]),
                        transaction_date=datetime.combine(current_date, datetime.min.time()),
                        balance_after=current_balance
                    )
                    day_transactions.append(transaction)
            
            # Random dining and shopping (2-3 times per week)
            if random.random() < 0.4:  # 40% chance per day
                expense_type = random.choice(["restaurant", "shopping", "entertainment"])
                if expense_type in tx_profile.spending_categories:
                    category_data = tx_profile.spending_categories[expense_type]
                    base_amount = category_data["avg_amount"] / 4  # Weekly amount
                    amount = Decimal(str(base_amount + random.randint(-20, 40)))
                    current_balance -= amount
                    
                    merchants = {
                        "restaurant": ["Olive Garden", "McDonald's", "Local Cafe", "Pizza Palace"],
                        "shopping": ["Target", "Amazon", "Local Store", "Online Retailer"],
                        "entertainment": ["Movie Theater", "Streaming Service", "Concert Venue"]
                    }
                    
                    categories = {
                        "restaurant": TransactionCategory.RESTAURANT,
                        "shopping": TransactionCategory.SHOPPING,
                        "entertainment": TransactionCategory.ENTERTAINMENT
                    }
                    
                    transaction = Transaction(
                        account_id=primary_account.account_id,
                        transaction_type=TransactionType.PAYMENT,
                        amount=-amount,
                        description=f"{expense_type.title()} purchase",
                        category=categories[expense_type],
                        merchant_name=random.choice(merchants[expense_type]),
                        transaction_date=datetime.combine(current_date, datetime.min.time()),
                        balance_after=current_balance
                    )
                    day_transactions.append(transaction)
            
            transactions.extend(day_transactions)
            current_date += timedelta(days=1)
        
        # Store transactions in database
        if transactions:
            self.db_manager.insert_transactions(transactions)
            
            # Update account balance
            primary_account.balance = current_balance
            primary_account.available_balance = current_balance
            self.db_manager.insert_accounts([primary_account])  # Update account
        
        return transactions


def create_young_professional_template() -> ProfileTemplate:
    """
    Create a standard profile template for young professional families.
    
    Returns:
        ProfileTemplate for young professional families
    """
    return ProfileTemplate(
        name="Young Professional Families",
        description="""
        Young professional couples (ages 28-35) with 1-2 young children, 
        living in suburban areas. Both partners work in professional roles 
        (technology, healthcare, finance, education). Combined household income 
        between $85,000-$150,000. Recently purchased their first home with a 
        mortgage. They have checking and savings accounts, use credit cards 
        responsibly, and are beginning to invest for retirement and children's 
        education. They shop at grocery stores weekly, use streaming services, 
        eat out occasionally, and have regular childcare expenses.
        """,
        category="household",
        complexity_level="medium",
        created_by="SyFi Application",
        tags=["families", "professionals", "suburban", "homeowners"]
    )