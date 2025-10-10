"""
Data generators for SyFi AI.

This module provides generators for creating realistic synthetic banking data
including customers, accounts, and transactions.
"""

import random
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
import json
import hashlib
from faker import Faker
import uuid

from .models import (
    Customer, Account, Transaction, 
    AccountType, TransactionType, TransactionCategory
)
from .core.profile_parser import CustomerProfileParser, ProfileInfo

class CustomerGenerator:
    """
    Generates synthetic customer data with realistic patterns.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize customer generator.
        
        Args:
            seed: Random seed for reproducible generation
        """
        if seed:
            random.seed(seed)
            Faker.seed(seed)
        
        self.fake = Faker()
        self.profile_parser = CustomerProfileParser()
        
        # Account type probabilities for realistic distribution
        self.account_type_weights = {
            AccountType.CHECKING: 0.95,   # Almost everyone has checking
            AccountType.SAVINGS: 0.75,    # Most people have savings
            AccountType.CREDIT: 0.60,     # Many people have credit cards
            AccountType.INVESTMENT: 0.25  # Some have investment accounts
        }
    
    def generate_customers(self, count: int, accounts_per_customer: int = 2, 
                          profile_description: Optional[str] = None) -> Tuple[List[Customer], List[Account]]:
        """
        Generate synthetic customers with accounts.
        
        Args:
            count: Number of customers to generate
            accounts_per_customer: Average number of accounts per customer
            profile_description: Natural language description of customer profile
            
        Returns:
            Tuple of (customers, accounts) lists
        """
        customers = []
        accounts = []
        
        # Parse profile if provided
        profile_info = None
        if profile_description:
            profile_info = self.profile_parser.parse_profile(profile_description)
        
        for i in range(count):
            # Generate customer
            if profile_info:
                customer = self._generate_profile_based_customer(profile_info, profile_description)
            else:
                customer = self._generate_single_customer()
            customers.append(customer)
            
            # Generate accounts for this customer
            if profile_info:
                customer_accounts = self._generate_profile_based_accounts(customer, profile_info)
            else:
                num_accounts = max(1, random.randint(1, accounts_per_customer * 2))
                customer_accounts = self._generate_accounts_for_customer(customer, num_accounts)
            accounts.extend(customer_accounts)
        
        return customers, accounts
    
    def _generate_accounts_for_customer(self, customer: Customer, num_accounts: int) -> List[Account]:
        """Generate accounts for a single customer."""
        accounts = []
        
        # Select account types based on weights and preferences
        selected_types = self._select_account_types(num_accounts)
        
        for i, account_type in enumerate(selected_types):
            account = self._create_account(customer, account_type, i)
            accounts.append(account)
        
        return accounts

    def generate_accounts_for_customers(self, customers: List[Customer], 
                                      avg_accounts: int = 2) -> List[Account]:
        """
        Generate bank accounts for existing customers.
        
        Args:
            customers: List of Customer objects
            avg_accounts: Average number of accounts per customer
            
        Returns:
            List of Account objects
        """
        accounts = []
        
        for customer in customers:
            # Determine number of accounts (1-4, weighted toward avg)
            num_accounts = max(1, int(random.normalvariate(avg_accounts, 0.8)))
            num_accounts = min(4, num_accounts)  # Cap at 4 accounts
            
            # Select account types based on weights and preferences
            selected_types = self._select_account_types(num_accounts)
            
            for i, account_type in enumerate(selected_types):
                account = self._create_account(customer, account_type, i)
                accounts.append(account)
        
        return accounts
    
    def _select_account_types(self, num_accounts: int) -> List[AccountType]:
        """Select realistic combination of account types for a customer."""
        # Start with checking (almost everyone has one)
        types = [AccountType.CHECKING]
        
        # Add additional types based on weights
        remaining_types = [
            AccountType.SAVINGS,
            AccountType.CREDIT, 
            AccountType.INVESTMENT
        ]
        
        for account_type in remaining_types:
            if len(types) >= num_accounts:
                break
                
            # Use weighted probability
            if random.random() < self.account_type_weights[account_type]:
                types.append(account_type)
        
        # If we need more accounts, add duplicates with different purposes
        while len(types) < num_accounts:
            # Add another checking or savings account
            if random.random() < 0.7:
                types.append(AccountType.CHECKING)  # Joint account, business, etc.
            else:
                types.append(AccountType.SAVINGS)   # Emergency fund, etc.
        
        return types[:num_accounts]
    
    def _create_account(self, customer: Customer, account_type: AccountType, 
                       sequence: int) -> Account:
        """Create a single account for a customer."""
        
        # Generate realistic initial balances based on account type
        balance = self._generate_initial_balance(account_type)
        
        # Generate account number (simplified format)
        account_num = f"{account_type.value.upper()[:3]}{random.randint(100000, 999999)}"
        
        account = Account(
            account_id=f"ACCT{uuid.uuid4().hex[:8].upper()}",
            customer_id=customer.customer_id,
            account_number=account_num,
            account_type=account_type,
            balance=balance,
            available_balance=balance,
            created_date=datetime.now()
        )
        
        # Set account-specific attributes
        if account_type == AccountType.CREDIT:
            # Credit cards have credit limits and start with zero balance
            credit_limit = Decimal(random.choice([1000, 2500, 5000, 10000, 15000]))
            account.balance = Decimal('0.00')
            account.available_balance = credit_limit
            
        elif account_type == AccountType.SAVINGS:
            # Savings accounts might have interest rates
            account.metadata = {"interest_rate": round(random.uniform(0.01, 2.5), 3)}
        
        return account
    
    def _generate_single_customer(self) -> Customer:
        """Generate a single customer with basic information."""
        profile = self.fake.profile()
        
        return Customer(
            first_name=profile['name'].split()[0],
            last_name=profile['name'].split()[-1],
            email=profile['mail'],
            phone=self.fake.phone_number(),
            date_of_birth=profile['birthdate'],
            address=self.fake.street_address(),
            city=self.fake.city(),
            state=self.fake.state_abbr(),
            zip_code=self.fake.zipcode(),
            ssn_hash=hashlib.sha256(self.fake.ssn().encode()).hexdigest()[:16],
            created_date=datetime.now()
        )
    
    def _generate_profile_based_customer(self, profile_info: ProfileInfo, description: str) -> Customer:
        """Generate a customer based on profile information."""
        profile = self.fake.profile()
        
        # Generate household composition
        num_adults = random.randint(*profile_info.num_adults_range)
        num_children = random.randint(*profile_info.num_children_range)
        num_pets = random.randint(*profile_info.num_pets_range)
        household_size = num_adults + num_children
        
        # Generate income based on profile
        household_income = None
        if profile_info.income_range[0] and profile_info.income_range[1]:
            min_income = profile_info.income_range[0]
            max_income = profile_info.income_range[1]
            household_income = Decimal(random.randint(int(min_income), int(max_income)))
        
        # Select employment and marital status
        employment_status = random.choice(profile_info.employment_statuses) if profile_info.employment_statuses else 'employed'
        marital_status = random.choice(profile_info.marital_statuses) if profile_info.marital_statuses else 'single'
        
        return Customer(
            first_name=profile['name'].split()[0],
            last_name=profile['name'].split()[-1],
            email=profile['mail'],
            phone=self.fake.phone_number(),
            date_of_birth=profile['birthdate'],
            address=self.fake.street_address(),
            city=self.fake.city(),
            state=self.fake.state_abbr(),
            zip_code=self.fake.zipcode(),
            ssn_hash=hashlib.sha256(self.fake.ssn().encode()).hexdigest()[:16],
            created_date=datetime.now(),
            
            # Household information
            household_size=household_size,
            num_adults=num_adults,
            num_children=num_children,
            num_pets=num_pets,
            household_income=household_income,
            employment_status=employment_status,
            marital_status=marital_status,
            
            # Profile information
            profile_description=description,
            profile_tags=profile_info.tags,
            metadata={
                'has_mortgage': profile_info.has_mortgage,
                'has_car_loan': profile_info.has_car_loan,
                'has_credit_cards': profile_info.has_credit_cards,
                'car_loan_range': profile_info.car_loan_range,
                'credit_card_range': profile_info.credit_card_range,
                'external_accounts': profile_info.external_accounts
            }
        )
    
    def _generate_profile_based_accounts(self, customer: Customer, profile_info: ProfileInfo) -> List[Account]:
        """Generate accounts based on customer profile information."""
        accounts = []
        
        # Always start with a checking account
        accounts.append(self._create_account(customer, AccountType.CHECKING, 1))
        
        # Add savings account (most families have one)
        accounts.append(self._create_account(customer, AccountType.SAVINGS, 2))
        
        # Add credit cards based on profile
        if profile_info.has_credit_cards:
            num_cards = random.randint(*profile_info.credit_card_range)
            for i in range(num_cards):
                accounts.append(self._create_account(customer, AccountType.CREDIT, len(accounts) + 1))
        
        # Higher income families might have investment accounts
        if customer.household_income and customer.household_income > Decimal('75000'):
            if random.random() < 0.3:  # 30% chance for higher income families
                accounts.append(self._create_account(customer, AccountType.INVESTMENT, len(accounts) + 1))
        
        return accounts
    
    def _generate_initial_balance(self, account_type: AccountType) -> Decimal:
        """Generate realistic initial balance based on account type."""
        
        if account_type == AccountType.CHECKING:
            # Checking accounts: $500 - $15,000, weighted toward lower amounts
            balance = random.lognormvariate(8.5, 1.2)  # Log-normal distribution
            return Decimal(str(round(min(15000, max(500, balance)), 2)))
        
        elif account_type == AccountType.SAVINGS:
            # Savings accounts: $1,000 - $50,000, higher than checking
            balance = random.lognormvariate(9.2, 1.0)
            return Decimal(str(round(min(50000, max(1000, balance)), 2)))
        
        elif account_type == AccountType.CREDIT:
            # Credit accounts start at zero
            return Decimal('0.00')
        
        elif account_type == AccountType.INVESTMENT:
            # Investment accounts: $5,000 - $100,000
            balance = random.lognormvariate(10.0, 0.8)
            return Decimal(str(round(min(100000, max(5000, balance)), 2)))
        
        else:
            return Decimal('1000.00')  # Default

class TransactionEngine:
    """
    Generates realistic synthetic banking transactions.
    
    Creates transactions that follow realistic banking patterns including
    timing, amounts, categories, and merchant information.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize transaction engine.
        
        Args:
            seed: Random seed for reproducible generation
        """
        if seed:
            random.seed(seed)
            Faker.seed(seed)
        
        self.faker = Faker()
        
        # Transaction patterns and weights
        self.transaction_patterns = {
            TransactionCategory.SALARY: {
                'frequency': 'monthly',
                'amount_range': (2500, 8000),
                'transaction_type': TransactionType.DEPOSIT,
                'timing': 'business_hours'
            },
            TransactionCategory.GROCERY: {
                'frequency': 'weekly', 
                'amount_range': (25, 200),
                'transaction_type': TransactionType.DEBIT,
                'timing': 'weekend_evening'
            },
            TransactionCategory.GAS: {
                'frequency': 'weekly',
                'amount_range': (30, 80),
                'transaction_type': TransactionType.DEBIT,
                'timing': 'commute_hours'
            },
            TransactionCategory.RESTAURANT: {
                'frequency': 'frequent',
                'amount_range': (15, 150),
                'transaction_type': TransactionType.DEBIT,
                'timing': 'meal_times'
            },
            TransactionCategory.UTILITIES: {
                'frequency': 'monthly',
                'amount_range': (80, 350),
                'transaction_type': TransactionType.DEBIT,
                'timing': 'business_hours'
            },
            TransactionCategory.ATM: {
                'frequency': 'occasional',
                'amount_range': (20, 200),
                'transaction_type': TransactionType.WITHDRAWAL,
                'timing': 'any'
            }
        }
        
        # Merchant name templates by category
        self.merchant_templates = {
            TransactionCategory.GROCERY: [
                "Safeway #{}",
                "Kroger Store {}",
                "Whole Foods Market",
                "Target #{}",
                "Walmart Supercenter",
                "Trader Joe's"
            ],
            TransactionCategory.GAS: [
                "Shell Station #{}",
                "Chevron #{}",
                "BP Gas Station",
                "Exxon Mobil",
                "Arco #{}",
                "Costco Gas"
            ],
            TransactionCategory.RESTAURANT: [
                "McDonald's #{}",
                "Starbucks #{}",
                "Subway #{}",
                "Chipotle Mexican Grill",
                "Olive Garden",
                "Local Cafe"
            ]
        }
    
    def generate_transactions_for_period(self, accounts: List[Dict[str, Any]], 
                                       start_date: date, end_date: date,
                                       avg_transactions_per_day: int = 50) -> List[Transaction]:
        """
        Generate transactions for all accounts within specified period.
        
        Args:
            accounts: List of account dictionaries from database
            start_date: Start date for transaction generation
            end_date: End date for transaction generation
            avg_transactions_per_day: Average number of transactions per day
            
        Returns:
            List of Transaction objects
        """
        transactions = []
        total_days = (end_date - start_date).days + 1
        
        # Calculate transactions per account per day
        if not accounts:
            return transactions
        
        transactions_per_account_per_day = avg_transactions_per_day / len(accounts)
        
        # Generate transactions for each day
        current_date = start_date
        while current_date <= end_date:
            daily_transactions = self._generate_daily_transactions(
                accounts, current_date, transactions_per_account_per_day
            )
            transactions.extend(daily_transactions)
            current_date += timedelta(days=1)
        
        return transactions
    
    def _generate_daily_transactions(self, accounts: List[Dict[str, Any]], 
                                   transaction_date: date,
                                   avg_transactions: float) -> List[Transaction]:
        """Generate transactions for a specific day."""
        transactions = []
        
        # Determine number of transactions for the day
        num_transactions = max(0, int(random.normalvariate(avg_transactions, avg_transactions * 0.3)))
        
        for _ in range(num_transactions):
            # Select random account
            account = random.choice(accounts)
            
            # Select transaction category based on day of week and time
            category = self._select_transaction_category(transaction_date)
            
            # Generate transaction
            transaction = self._create_transaction(account, category, transaction_date)
            transactions.append(transaction)
        
        return transactions
    
    def _select_transaction_category(self, transaction_date: date) -> TransactionCategory:
        """Select appropriate transaction category based on date/time patterns."""
        
        # Weekend patterns
        if transaction_date.weekday() >= 5:  # Saturday, Sunday
            weekend_categories = [
                TransactionCategory.GROCERY,
                TransactionCategory.RESTAURANT,
                TransactionCategory.ENTERTAINMENT,
                TransactionCategory.SHOPPING
            ]
            return random.choice(weekend_categories)
        
        # Weekday patterns
        weekday_categories = [
            TransactionCategory.GAS,
            TransactionCategory.RESTAURANT,
            TransactionCategory.GROCERY,
            TransactionCategory.ATM
        ]
        
        # Monthly transactions (salary, utilities) - occur around month boundaries
        if transaction_date.day <= 3 or transaction_date.day >= 28:
            if random.random() < 0.3:
                return random.choice([
                    TransactionCategory.SALARY,
                    TransactionCategory.UTILITIES
                ])
        
        return random.choice(weekday_categories)
    
    def _create_transaction(self, account: Dict[str, Any], 
                          category: TransactionCategory,
                          transaction_date: date) -> Transaction:
        """Create a single transaction."""
        
        # Get transaction pattern for category
        pattern = self.transaction_patterns.get(category, {
            'amount_range': (10, 100),
            'transaction_type': TransactionType.DEBIT,
            'timing': 'any'
        })
        
        # Generate amount within range
        min_amount, max_amount = pattern['amount_range']
        amount = Decimal(str(round(random.uniform(min_amount, max_amount), 2)))
        
        # Generate transaction time based on pattern
        transaction_time = self._generate_transaction_time(
            transaction_date, pattern.get('timing', 'any')
        )
        
        # Generate merchant name
        merchant_name = self._generate_merchant_name(category)
        
        # Create description
        description = f"{merchant_name}" if merchant_name else f"{category.value.title()} Transaction"
        
        transaction = Transaction(
            transaction_id=f"TXN{uuid.uuid4().hex[:10].upper()}",
            account_id=account['account_id'],
            transaction_type=pattern['transaction_type'],
            amount=amount,
            description=description,
            category=category,
            merchant_name=merchant_name,
            merchant_category=category.value,
            transaction_date=transaction_time,
            posted_date=transaction_time,
            reference_number=f"REF{random.randint(100000, 999999)}"
        )
        
        return transaction
    
    def _generate_transaction_time(self, transaction_date: date, timing: str) -> datetime:
        """Generate realistic transaction time based on timing pattern."""
        
        if timing == 'business_hours':
            # 9 AM - 5 PM
            hour = random.randint(9, 17)
            minute = random.randint(0, 59)
        elif timing == 'meal_times':
            # Breakfast (7-9), Lunch (11-14), Dinner (17-21)
            meal_periods = [(7, 9), (11, 14), (17, 21)]
            period = random.choice(meal_periods)
            hour = random.randint(period[0], period[1])
            minute = random.randint(0, 59)
        elif timing == 'weekend_evening':
            # 5 PM - 9 PM
            hour = random.randint(17, 21)
            minute = random.randint(0, 59)
        elif timing == 'commute_hours':
            # 7-9 AM or 5-7 PM
            if random.random() < 0.5:
                hour = random.randint(7, 9)
            else:
                hour = random.randint(17, 19)
            minute = random.randint(0, 59)
        else:
            # Any time during business day
            hour = random.randint(6, 23)
            minute = random.randint(0, 59)
        
        return datetime.combine(
            transaction_date, 
            datetime.min.time().replace(hour=hour, minute=minute)
        )
    
    def _generate_merchant_name(self, category: TransactionCategory) -> Optional[str]:
        """Generate realistic merchant name for transaction category."""
        
        if category not in self.merchant_templates:
            return None
        
        templates = self.merchant_templates[category]
        template = random.choice(templates)
        
        # Fill in template with random numbers if needed
        if '{}' in template:
            store_number = random.randint(1001, 9999)
            return template.format(store_number)
        
        return template

# Export generator classes
__all__ = ['CustomerGenerator', 'TransactionEngine']