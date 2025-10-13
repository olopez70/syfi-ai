"""
Builder Pattern Implementation for Complex Profile Construction

Provides step-by-step construction of complex profiles with different configurations.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from decimal import Decimal
from datetime import date
import random

from ..models import Profile, ProfileTemplate


class ProfileBuilder(ABC):
    """Abstract builder for constructing profiles."""
    
    @abstractmethod
    def reset(self) -> 'ProfileBuilder':
        """Reset the builder to start fresh."""
        pass
    
    @abstractmethod
    def set_basic_info(self, template: ProfileTemplate, name: str, **kwargs) -> 'ProfileBuilder':
        """Set basic profile information."""
        pass
    
    @abstractmethod
    def add_household_members(self, count: int, **kwargs) -> 'ProfileBuilder':
        """Add household members."""
        pass
    
    @abstractmethod
    def set_income_level(self, income: Decimal, **kwargs) -> 'ProfileBuilder':
        """Set household income level."""
        pass
    
    @abstractmethod
    def add_customer_data(self, **kwargs) -> 'ProfileBuilder':
        """Add customer demographic data."""
        pass
    
    @abstractmethod
    def add_account_structure(self, **kwargs) -> 'ProfileBuilder':
        """Add account structure."""
        pass
    
    @abstractmethod
    def add_transaction_patterns(self, **kwargs) -> 'ProfileBuilder':
        """Add transaction patterns."""
        pass
    
    @abstractmethod
    def build(self) -> Profile:
        """Build and return the final profile."""
        pass


class ConcreteProfileBuilder(ProfileBuilder):
    """Concrete implementation of profile builder."""
    
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed or 12345
        self.profile: Optional[Profile] = None
        self.reset()
    
    def reset(self) -> 'ProfileBuilder':
        """Reset the builder."""
        self.profile = None
        return self
    
    def set_basic_info(self, template: ProfileTemplate, name: str, **kwargs) -> 'ProfileBuilder':
        """Set basic profile information."""
        self.profile = Profile(
            template_id=template.template_id,
            name=name,
            description=kwargs.get('description', f"Profile built from {template.name}"),
            household_type=kwargs.get('household_type', 'family'),
            total_members=kwargs.get('total_members', 1),
            banking_members=kwargs.get('banking_members', 1),
            household_income=kwargs.get('household_income', Decimal('50000')),
            generation_seed=self.seed
        )
        return self
    
    def add_household_members(self, count: int, **kwargs) -> 'ProfileBuilder':
        """Add household members."""
        if self.profile:
            self.profile.total_members = count
            self.profile.banking_members = kwargs.get('banking_members', min(count, 2))
        return self
    
    def set_income_level(self, income: Decimal, **kwargs) -> 'ProfileBuilder':
        """Set household income level."""
        if self.profile:
            self.profile.household_income = income
        return self
    
    def add_customer_data(self, **kwargs) -> 'ProfileBuilder':
        """Add customer demographic data."""
        if self.profile:
            customers_data = kwargs.get('customers_data', [])
            for customer_data in customers_data:
                self.profile.add_customer_data(customer_data)
        return self
    
    def add_account_structure(self, **kwargs) -> 'ProfileBuilder':
        """Add account structure."""
        if self.profile:
            accounts_data = kwargs.get('accounts_data', [])
            for account_data in accounts_data:
                self.profile.add_account_data(account_data)
        return self
    
    def add_transaction_patterns(self, **kwargs) -> 'ProfileBuilder':
        """Add transaction patterns."""
        if self.profile:
            pattern_name = kwargs.get('pattern_name', 'default')
            transaction_profile = kwargs.get('transaction_profile')
            if transaction_profile:
                self.profile.add_transaction_profile(pattern_name, transaction_profile)
        return self
    
    def build(self) -> Profile:
        """Build and return the final profile."""
        if not self.profile:
            raise ValueError("Profile not initialized. Call set_basic_info first.")
        
        result = self.profile
        self.reset()  # Reset for next build
        return result


class ProfileDirector:
    """Director class that knows how to construct specific types of profiles."""
    
    def __init__(self, builder: ProfileBuilder):
        self.builder = builder
    
    def build_young_family_profile(self, template: ProfileTemplate, name: str, 
                                 income_range: tuple = (75000, 125000)) -> Profile:
        """Build a young family profile with predefined characteristics."""
        from ..models import TransactionProfile
        
        random.seed(self.builder.seed)
        
        income = Decimal(str(random.randint(*income_range)))
        
        # Basic profile setup
        self.builder.reset() \
                   .set_basic_info(template, name, household_type='family') \
                   .add_household_members(random.choice([3, 4]), banking_members=2) \
                   .set_income_level(income)
        
        # Add customer data
        customers_data = self._generate_young_family_customers()
        self.builder.add_customer_data(customers_data=customers_data)
        
        # Add account structure
        accounts_data = self._generate_family_accounts()
        self.builder.add_account_structure(accounts_data=accounts_data)
        
        # Add transaction patterns
        tx_profile = self._generate_family_transaction_profile(income)
        self.builder.add_transaction_patterns(
            pattern_name='household',
            transaction_profile=tx_profile
        )
        
        return self.builder.build()
    
    def build_high_income_profile(self, template: ProfileTemplate, name: str,
                                income_range: tuple = (200000, 500000)) -> Profile:
        """Build a high-income profile."""
        import random
        from ..models import TransactionProfile
        
        random.seed(self.builder.seed)
        
        income = Decimal(str(random.randint(*income_range)))
        
        # Basic profile setup
        self.builder.reset() \
                   .set_basic_info(template, name, household_type='family') \
                   .add_household_members(random.choice([3, 4, 5]), banking_members=2) \
                   .set_income_level(income)
        
        # Add customer data
        customers_data = self._generate_high_income_customers()
        self.builder.add_customer_data(customers_data=customers_data)
        
        # Add account structure
        accounts_data = self._generate_high_income_accounts()
        self.builder.add_account_structure(accounts_data=accounts_data)
        
        # Add transaction patterns
        tx_profile = self._generate_high_income_transaction_profile(income)
        self.builder.add_transaction_patterns(
            pattern_name='household',
            transaction_profile=tx_profile
        )
        
        return self.builder.build()
    
    def build_young_single_profile(self, template: ProfileTemplate, name: str,
                                 income_range: tuple = (35000, 70000)) -> Profile:
        """Build a young single professional profile."""
        import random
        from ..models import TransactionProfile
        
        random.seed(self.builder.seed)
        
        income = Decimal(str(random.randint(*income_range)))
        
        # Basic profile setup
        self.builder.reset() \
                   .set_basic_info(template, name, household_type='single') \
                   .add_household_members(1, banking_members=1) \
                   .set_income_level(income)
        
        # Add customer data
        customers_data = self._generate_young_single_customer()
        self.builder.add_customer_data(customers_data=customers_data)
        
        # Add account structure
        accounts_data = self._generate_single_accounts()
        self.builder.add_account_structure(accounts_data=accounts_data)
        
        # Add transaction patterns
        tx_profile = self._generate_single_transaction_profile(income)
        self.builder.add_transaction_patterns(
            pattern_name='individual',
            transaction_profile=tx_profile
        )
        
        return self.builder.build()
    
    def build_business_profile(self, template: ProfileTemplate, name: str,
                             revenue_range: tuple = (500000, 2000000)) -> Profile:
        """Build a business profile."""
        import random
        from ..models import TransactionProfile
        
        random.seed(self.builder.seed)
        
        revenue = Decimal(str(random.randint(*revenue_range)))
        
        # Basic profile setup
        self.builder.reset() \
                   .set_basic_info(template, name, household_type='business') \
                   .add_household_members(1, banking_members=1) \
                   .set_income_level(revenue)
        
        # Add customer data
        customers_data = self._generate_business_customer()
        self.builder.add_customer_data(customers_data=customers_data)
        
        # Add account structure
        accounts_data = self._generate_business_accounts()
        self.builder.add_account_structure(accounts_data=accounts_data)
        
        # Add transaction patterns
        tx_profile = self._generate_business_transaction_profile(revenue)
        self.builder.add_transaction_patterns(
            pattern_name='business',
            transaction_profile=tx_profile
        )
        
        return self.builder.build()
    
    def _generate_young_family_customers(self) -> List[Dict[str, Any]]:
        """Generate young family customer data."""
        import random
        
        first_names_male = ["James", "Michael", "David", "John", "Robert"]
        first_names_female = ["Mary", "Jennifer", "Lisa", "Michelle", "Sarah"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones"]
        employment_options = ["Software Engineer", "Teacher", "Nurse", "Financial Analyst"]
        
        last_name = random.choice(last_names)
        
        return [
            {
                "first_name": random.choice(first_names_male),
                "last_name": last_name,
                "age": random.randint(28, 35),
                "employment_status": random.choice(employment_options),
                "role": "primary",
                "is_banking_customer": True
            },
            {
                "first_name": random.choice(first_names_female),
                "last_name": last_name,
                "age": random.randint(26, 33),
                "employment_status": random.choice(employment_options),
                "role": "spouse",
                "is_banking_customer": True
            }
        ]
    
    def _generate_high_income_customers(self) -> List[Dict[str, Any]]:
        """Generate high-income customer data."""
        import random
        
        first_names = ["Alexander", "Victoria", "Christopher", "Elizabeth"]
        last_names = ["Wellington", "Pemberton", "Ashworth", "Blackwood"]
        high_income_jobs = ["Investment Banker", "Surgeon", "Corporate Lawyer", "VP Engineering"]
        
        last_name = random.choice(last_names)
        
        return [
            {
                "first_name": random.choice(first_names),
                "last_name": last_name,
                "age": random.randint(35, 45),
                "employment_status": random.choice(high_income_jobs),
                "role": "primary",
                "is_banking_customer": True
            },
            {
                "first_name": random.choice(first_names),
                "last_name": last_name,
                "age": random.randint(32, 42),
                "employment_status": random.choice(high_income_jobs),
                "role": "spouse",
                "is_banking_customer": True
            }
        ]
    
    def _generate_young_single_customer(self) -> List[Dict[str, Any]]:
        """Generate young single professional data."""
        import random
        
        first_names = ["Alex", "Jordan", "Taylor", "Casey", "Riley"]
        last_names = ["Chen", "Patel", "Kim", "Rodriguez", "Johnson"]
        young_jobs = ["Junior Developer", "Marketing Coordinator", "Data Analyst"]
        
        return [
            {
                "first_name": random.choice(first_names),
                "last_name": random.choice(last_names),
                "age": random.randint(22, 30),
                "employment_status": random.choice(young_jobs),
                "role": "primary",
                "is_banking_customer": True
            }
        ]
    
    def _generate_business_customer(self) -> List[Dict[str, Any]]:
        """Generate business customer data."""
        import random
        
        business_names = ["Tech Solutions LLC", "Consulting Partners Inc", "Services Corp"]
        business_roles = ["Business Owner", "CEO", "Managing Partner"]
        
        return [
            {
                "first_name": random.choice(["Business", "Corporate", "Enterprise"]),
                "last_name": random.choice(business_names),
                "age": random.randint(30, 55),
                "employment_status": random.choice(business_roles),
                "role": "primary",
                "is_banking_customer": True
            }
        ]
    
    def _generate_family_accounts(self) -> List[Dict[str, Any]]:
        """Generate family account structure."""
        import random
        
        return [
            {
                "account_type": "checking",
                "ownership": "joint",
                "initial_balance": random.randint(2500, 8000),
                "purpose": "primary checking"
            },
            {
                "account_type": "savings",
                "ownership": "joint",
                "initial_balance": random.randint(15000, 45000),
                "purpose": "emergency fund"
            },
            {
                "account_type": "savings",
                "ownership": "joint",
                "initial_balance": random.randint(5000, 20000),
                "purpose": "education fund"
            }
        ]
    
    def _generate_high_income_accounts(self) -> List[Dict[str, Any]]:
        """Generate high-income account structure."""
        import random
        
        return [
            {
                "account_type": "checking",
                "ownership": "joint",
                "initial_balance": random.randint(25000, 75000),
                "purpose": "primary checking"
            },
            {
                "account_type": "savings",
                "ownership": "joint",
                "initial_balance": random.randint(100000, 300000),
                "purpose": "emergency fund"
            },
            {
                "account_type": "savings",
                "ownership": "joint",
                "initial_balance": random.randint(50000, 150000),
                "purpose": "investment fund"
            }
        ]
    
    def _generate_single_accounts(self) -> List[Dict[str, Any]]:
        """Generate single person account structure."""
        import random
        
        return [
            {
                "account_type": "checking",
                "ownership": "individual",
                "initial_balance": random.randint(1000, 5000),
                "purpose": "primary checking"
            },
            {
                "account_type": "savings",
                "ownership": "individual",
                "initial_balance": random.randint(5000, 25000),
                "purpose": "emergency fund"
            }
        ]
    
    def _generate_business_accounts(self) -> List[Dict[str, Any]]:
        """Generate business account structure."""
        import random
        
        return [
            {
                "account_type": "checking",
                "ownership": "business",
                "initial_balance": random.randint(50000, 200000),
                "purpose": "operating account"
            },
            {
                "account_type": "savings",
                "ownership": "business",
                "initial_balance": random.randint(100000, 500000),
                "purpose": "reserve fund"
            }
        ]
    
    def _generate_family_transaction_profile(self, income: Decimal):
        """Generate family transaction patterns."""
        from ..models import TransactionProfile
        
        tx_profile = TransactionProfile()
        
        tx_profile.income_sources = [
            {
                "type": "salary",
                "amount": float(income) * 0.6,
                "frequency": "biweekly",
                "description": "Primary salary"
            },
            {
                "type": "salary",
                "amount": float(income) * 0.4,
                "frequency": "biweekly",
                "description": "Secondary salary"
            }
        ]
        
        monthly_housing = int(float(income) * 0.25 / 12)
        
        tx_profile.spending_categories = {
            "groceries": {"avg_amount": 150, "frequency": "weekly", "variability": "medium"},
            "housing": {"avg_amount": monthly_housing, "frequency": "monthly", "variability": "none"},
            "utilities": {"avg_amount": 250, "frequency": "monthly", "variability": "low"},
            "childcare": {"avg_amount": 800, "frequency": "monthly", "variability": "low"},
            "transportation": {"avg_amount": 120, "frequency": "weekly", "variability": "medium"},
            "entertainment": {"avg_amount": 200, "frequency": "monthly", "variability": "high"},
            "shopping": {"avg_amount": 300, "frequency": "monthly", "variability": "high"}
        }
        
        return tx_profile
    
    def _generate_high_income_transaction_profile(self, income: Decimal):
        """Generate high-income transaction patterns."""
        from ..models import TransactionProfile
        
        tx_profile = TransactionProfile()
        
        tx_profile.income_sources = [
            {
                "type": "salary",
                "amount": float(income) * 0.65,
                "frequency": "biweekly",
                "description": "Executive salary"
            },
            {
                "type": "salary",
                "amount": float(income) * 0.35,
                "frequency": "biweekly",
                "description": "Professional salary"
            }
        ]
        
        monthly_housing = int(float(income) * 0.35 / 12)
        
        tx_profile.spending_categories = {
            "groceries": {"avg_amount": 400, "frequency": "weekly", "variability": "medium"},
            "housing": {"avg_amount": monthly_housing, "frequency": "monthly", "variability": "none"},
            "utilities": {"avg_amount": 500, "frequency": "monthly", "variability": "low"},
            "childcare": {"avg_amount": 2000, "frequency": "monthly", "variability": "low"},
            "transportation": {"avg_amount": 200, "frequency": "weekly", "variability": "medium"},
            "entertainment": {"avg_amount": 800, "frequency": "monthly", "variability": "high"},
            "shopping": {"avg_amount": 1000, "frequency": "monthly", "variability": "high"},
            "travel": {"avg_amount": 3000, "frequency": "monthly", "variability": "high"},
            "luxury": {"avg_amount": 2000, "frequency": "monthly", "variability": "high"}
        }
        
        return tx_profile
    
    def _generate_single_transaction_profile(self, income: Decimal):
        """Generate single person transaction patterns."""
        from ..models import TransactionProfile
        
        tx_profile = TransactionProfile()
        
        tx_profile.income_sources = [
            {
                "type": "salary",
                "amount": float(income),
                "frequency": "biweekly",
                "description": "Primary salary"
            }
        ]
        
        monthly_rent = int(float(income) * 0.30 / 12)
        
        tx_profile.spending_categories = {
            "groceries": {"avg_amount": 75, "frequency": "weekly", "variability": "medium"},
            "rent": {"avg_amount": monthly_rent, "frequency": "monthly", "variability": "none"},
            "utilities": {"avg_amount": 150, "frequency": "monthly", "variability": "low"},
            "transportation": {"avg_amount": 60, "frequency": "weekly", "variability": "medium"},
            "entertainment": {"avg_amount": 300, "frequency": "monthly", "variability": "high"},
            "shopping": {"avg_amount": 200, "frequency": "monthly", "variability": "high"},
            "subscriptions": {"avg_amount": 75, "frequency": "monthly", "variability": "low"}
        }
        
        return tx_profile
    
    def _generate_business_transaction_profile(self, revenue: Decimal):
        """Generate business transaction patterns."""
        from ..models import TransactionProfile
        
        tx_profile = TransactionProfile()
        
        tx_profile.income_sources = [
            {
                "type": "revenue",
                "amount": float(revenue) / 12,  # Monthly revenue
                "frequency": "monthly",
                "description": "Business revenue"
            }
        ]
        
        monthly_expenses = {
            "payroll": int(float(revenue) * 0.4 / 12),
            "rent": int(float(revenue) * 0.1 / 12),
            "supplies": int(float(revenue) * 0.05 / 12),
            "marketing": int(float(revenue) * 0.03 / 12),
            "utilities": int(float(revenue) * 0.02 / 12)
        }
        
        tx_profile.spending_categories = {
            "payroll": {"avg_amount": monthly_expenses["payroll"], 
                       "frequency": "monthly", "variability": "low"},
            "rent": {"avg_amount": monthly_expenses["rent"], 
                    "frequency": "monthly", "variability": "none"},
            "supplies": {"avg_amount": monthly_expenses["supplies"], 
                        "frequency": "monthly", "variability": "medium"},
            "marketing": {"avg_amount": monthly_expenses["marketing"], 
                         "frequency": "monthly", "variability": "high"},
            "utilities": {"avg_amount": monthly_expenses["utilities"], 
                         "frequency": "monthly", "variability": "low"}
        }
        
        return tx_profile