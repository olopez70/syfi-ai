"""
Factory Method Pattern Implementation for SyFi AI Data Generation

Provides extensible data generation through abstract factories.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from decimal import Decimal
import random

from ..models import Customer, Account, Transaction, Profile, ProfileTemplate
from ..models import AccountType, TransactionType, TransactionCategory


class DataGeneratorFactory(ABC):
    """Abstract factory for creating domain-specific data generators."""
    
    @abstractmethod
    def create_customer_generator(self) -> 'CustomerGeneratorInterface':
        pass
    
    @abstractmethod
    def create_account_generator(self) -> 'AccountGeneratorInterface':
        pass
    
    @abstractmethod
    def create_transaction_generator(self) -> 'TransactionGeneratorInterface':
        pass


class CustomerGeneratorInterface(ABC):
    """Abstract interface for customer generation strategies."""
    
    @abstractmethod
    def generate_customers(self, profile: Profile, template: ProfileTemplate) -> List[Customer]:
        pass


class AccountGeneratorInterface(ABC):
    """Abstract interface for account generation strategies."""
    
    @abstractmethod
    def generate_accounts(self, customers: List[Customer], profile: Profile) -> List[Account]:
        pass


class TransactionGeneratorInterface(ABC):
    """Abstract interface for transaction generation strategies."""
    
    @abstractmethod
    def generate_transactions(self, accounts: List[Account], profile: Profile, 
                            start_date, end_date) -> List[Transaction]:
        pass


# Concrete Implementations

class FamilyDataGeneratorFactory(DataGeneratorFactory):
    """Concrete factory for family-oriented banking data."""
    
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed or random.randint(1000, 9999)
    
    def create_customer_generator(self) -> CustomerGeneratorInterface:
        return FamilyCustomerGenerator(self.seed)
    
    def create_account_generator(self) -> AccountGeneratorInterface:
        return JointAccountGenerator(self.seed)
    
    def create_transaction_generator(self) -> TransactionGeneratorInterface:
        return FamilyTransactionGenerator(self.seed)


class BusinessDataGeneratorFactory(DataGeneratorFactory):
    """Concrete factory for business-oriented banking data."""
    
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed or random.randint(1000, 9999)
    
    def create_customer_generator(self) -> CustomerGeneratorInterface:
        return BusinessCustomerGenerator(self.seed)
    
    def create_account_generator(self) -> AccountGeneratorInterface:
        return BusinessAccountGenerator(self.seed)
    
    def create_transaction_generator(self) -> TransactionGeneratorInterface:
        return BusinessTransactionGenerator(self.seed)


class FamilyCustomerGenerator(CustomerGeneratorInterface):
    """Generates family-oriented customers."""
    
    def __init__(self, seed: int):
        self.seed = seed
    
    def generate_customers(self, profile: Profile, template: ProfileTemplate) -> List[Customer]:
        random.seed(self.seed)
        customers = []
        
        # Generate family members with realistic demographics
        ages = [random.randint(28, 35), random.randint(26, 33)]
        first_names = [
            random.choice(["James", "Michael", "David", "John", "Robert"]),
            random.choice(["Mary", "Jennifer", "Lisa", "Michelle", "Sarah"])
        ]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones"]
        last_name = random.choice(last_names)
        
        employment_options = [
            "Software Engineer", "Nurse", "Teacher", "Financial Analyst", 
            "Marketing Manager", "Project Manager"
        ]
        
        for i, (age, first_name) in enumerate(zip(ages, first_names)):
            customer = Customer(
                first_name=first_name,
                last_name=last_name,
                employment_status=random.choice(employment_options),
                household_income=profile.household_income,
                household_size=profile.total_members
            )
            customers.append(customer)
        
        return customers


class BusinessCustomerGenerator(CustomerGeneratorInterface):
    """Generates business-oriented customers."""
    
    def __init__(self, seed: int):
        self.seed = seed
    
    def generate_customers(self, profile: Profile, template: ProfileTemplate) -> List[Customer]:
        random.seed(self.seed)
        customers = []
        
        # Generate business owners/managers
        business_roles = ["CEO", "CFO", "Business Owner", "Operations Manager"]
        
        for i in range(profile.banking_members):
            customer = Customer(
                first_name=random.choice(["Alex", "Jordan", "Casey", "Taylor"]),
                last_name=random.choice(["Enterprises", "LLC", "Corp", "Inc"]),
                employment_status=random.choice(business_roles),
                household_income=profile.household_income,
                household_size=1  # Business entity
            )
            customers.append(customer)
        
        return customers


class JointAccountGenerator(AccountGeneratorInterface):
    """Generates joint family accounts."""
    
    def __init__(self, seed: int):
        self.seed = seed
    
    def generate_accounts(self, customers: List[Customer], profile: Profile) -> List[Account]:
        random.seed(self.seed)
        accounts = []
        
        # Create joint accounts for family
        for customer in customers:
            # Each customer gets checking, savings, education savings
            account_types = [
                (AccountType.CHECKING, random.randint(2500, 8000)),
                (AccountType.SAVINGS, random.randint(15000, 45000)),
                (AccountType.SAVINGS, random.randint(5000, 20000))  # Education fund
            ]
            
            for account_type, balance in account_types:
                account = Account(
                    customer_id=customer.customer_id,
                    account_type=account_type,
                    balance=Decimal(str(balance)),
                    available_balance=Decimal(str(balance))
                )
                accounts.append(account)
        
        return accounts


class BusinessAccountGenerator(AccountGeneratorInterface):
    """Generates business accounts."""
    
    def __init__(self, seed: int):
        self.seed = seed
    
    def generate_accounts(self, customers: List[Customer], profile: Profile) -> List[Account]:
        random.seed(self.seed)
        accounts = []
        
        # Create business-oriented accounts
        for customer in customers:
            account_types = [
                (AccountType.CHECKING, random.randint(25000, 100000)),  # Operating account
                (AccountType.SAVINGS, random.randint(50000, 200000))    # Reserve fund
            ]
            
            for account_type, balance in account_types:
                account = Account(
                    customer_id=customer.customer_id,
                    account_type=account_type,
                    balance=Decimal(str(balance)),
                    available_balance=Decimal(str(balance))
                )
                accounts.append(account)
        
        return accounts


class FamilyTransactionGenerator(TransactionGeneratorInterface):
    """Generates family-oriented transactions."""
    
    def __init__(self, seed: int):
        self.seed = seed
    
    def generate_transactions(self, accounts: List[Account], profile: Profile, 
                            start_date, end_date) -> List[Transaction]:
        # Implementation would go here - family spending patterns
        # Groceries, utilities, childcare, etc.
        return []  # Placeholder


class BusinessTransactionGenerator(TransactionGeneratorInterface):
    """Generates business-oriented transactions."""
    
    def __init__(self, seed: int):
        self.seed = seed
    
    def generate_transactions(self, accounts: List[Account], profile: Profile, 
                            start_date, end_date) -> List[Transaction]:
        # Implementation would go here - business spending patterns
        # Payroll, supplies, rent, revenue, etc.
        return []  # Placeholder


# Factory Registry for extensibility
class GeneratorFactoryRegistry:
    """Registry for data generator factories."""
    
    _factories: Dict[str, DataGeneratorFactory] = {}
    
    @classmethod
    def register_factory(cls, name: str, factory: DataGeneratorFactory):
        """Register a new factory."""
        cls._factories[name] = factory
    
    @classmethod
    def create_factory(cls, name: str, **kwargs) -> DataGeneratorFactory:
        """Create factory by name."""
        if name not in cls._factories:
            raise ValueError(f"Unknown factory: {name}")
        return cls._factories[name](**kwargs)
    
    @classmethod
    def list_factories(cls) -> List[str]:
        """List available factory names."""
        return list(cls._factories.keys())


# Register built-in factories
GeneratorFactoryRegistry.register_factory("family", FamilyDataGeneratorFactory)
GeneratorFactoryRegistry.register_factory("business", BusinessDataGeneratorFactory)