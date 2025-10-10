"""
Strategy Pattern Implementation for Profile Building

Allows different profile building strategies to be used interchangeably.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from decimal import Decimal
import random

from ..models import Profile, ProfileTemplate


class ProfileBuildingStrategy(ABC):
    """Abstract strategy for building profiles from templates."""
    
    @abstractmethod
    def build_profile(self, template: ProfileTemplate, profile_name: str, 
                     seed: int, **kwargs) -> Profile:
        """Build a profile using this strategy."""
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Get the name of this strategy."""
        pass


class StandardFamilyStrategy(ProfileBuildingStrategy):
    """Standard strategy for family profile building."""
    
    def build_profile(self, template: ProfileTemplate, profile_name: str, 
                     seed: int, **kwargs) -> Profile:
        random.seed(seed)
        
        profile = Profile(
            template_id=template.template_id,
            name=profile_name,
            description=kwargs.get('description', f"Generated profile based on {template.name}"),
            household_type=kwargs.get('household_type', 'family'),
            total_members=kwargs.get('total_members', random.choice([3, 4])),
            banking_members=kwargs.get('banking_members', 2),
            household_income=kwargs.get('household_income', 
                                      Decimal(str(random.randint(85000, 150000)))),
            generation_seed=seed
        )
        
        # Add family-specific profile data
        self._add_family_data(profile, template, seed)
        
        return profile
    
    def _add_family_data(self, profile: Profile, template: ProfileTemplate, seed: int):
        """Add family-specific customer and account data."""
        random.seed(seed)
        
        # Generate customer data
        ages = [random.randint(28, 35), random.randint(26, 33)]
        first_names = [
            random.choice(["James", "Michael", "David", "John", "Robert"]),
            random.choice(["Mary", "Jennifer", "Lisa", "Michelle", "Sarah"])
        ]
        last_name = random.choice(["Smith", "Johnson", "Williams", "Brown"])
        
        for i, (age, first_name) in enumerate(zip(ages, first_names)):
            profile.add_customer_data({
                "first_name": first_name,
                "last_name": last_name,
                "age": age,
                "employment_status": random.choice([
                    "Software Engineer", "Teacher", "Nurse", "Financial Analyst"
                ]),
                "role": "primary" if i == 0 else "spouse",
                "is_banking_customer": True
            })
        
        # Generate account data
        accounts_data = [
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
                "purpose": "children education fund"
            }
        ]
        
        for account_data in accounts_data:
            profile.add_account_data(account_data)
        
        # Generate transaction profile
        self._add_transaction_profile(profile)
    
    def _add_transaction_profile(self, profile: Profile):
        """Add family transaction patterns."""
        from ..models import TransactionProfile
        
        tx_profile = TransactionProfile()
        
        # Family income sources
        tx_profile.income_sources = [
            {
                "type": "salary",
                "amount": float(profile.household_income) * 0.6,
                "frequency": "biweekly",
                "description": "Primary salary"
            },
            {
                "type": "salary", 
                "amount": float(profile.household_income) * 0.4,
                "frequency": "biweekly",
                "description": "Secondary salary"
            }
        ]
        
        # Family spending categories
        monthly_mortgage = int(float(profile.household_income) * 0.25 / 12)
        
        tx_profile.spending_categories = {
            "groceries": {"avg_amount": 150 + (profile.total_members * 25), 
                         "frequency": "weekly", "variability": "medium"},
            "gas": {"avg_amount": 80, "frequency": "weekly", "variability": "low"},
            "utilities": {"avg_amount": 200 + (profile.total_members * 50), 
                         "frequency": "monthly", "variability": "low"},
            "mortgage": {"avg_amount": monthly_mortgage, 
                        "frequency": "monthly", "variability": "none"},
            "childcare": {"avg_amount": 600 + ((profile.total_members - 2) * 200), 
                         "frequency": "monthly", "variability": "low"},
            "restaurant": {"avg_amount": 35 + (profile.total_members * 10), 
                          "frequency": "weekly", "variability": "high"},
            "entertainment": {"avg_amount": 80 + (profile.total_members * 20), 
                            "frequency": "monthly", "variability": "medium"},
            "shopping": {"avg_amount": 150 + (profile.total_members * 50), 
                        "frequency": "monthly", "variability": "high"}
        }
        
        profile.add_transaction_profile("household", tx_profile)
    
    def get_strategy_name(self) -> str:
        return "standard_family"


class HighIncomeStrategy(ProfileBuildingStrategy):
    """Strategy for high-income profile building."""
    
    def build_profile(self, template: ProfileTemplate, profile_name: str, 
                     seed: int, **kwargs) -> Profile:
        random.seed(seed)
        
        profile = Profile(
            template_id=template.template_id,
            name=profile_name,
            description=kwargs.get('description', f"High-income profile based on {template.name}"),
            household_type=kwargs.get('household_type', 'family'),
            total_members=kwargs.get('total_members', random.choice([3, 4])),
            banking_members=kwargs.get('banking_members', 2),
            household_income=kwargs.get('household_income', 
                                      Decimal(str(random.randint(200000, 500000)))),  # Higher income
            generation_seed=seed
        )
        
        self._add_high_income_data(profile, template, seed)
        
        return profile
    
    def _add_high_income_data(self, profile: Profile, template: ProfileTemplate, seed: int):
        """Add high-income specific profile data."""
        random.seed(seed)
        
        # High-income employment
        high_income_jobs = [
            "Senior Software Engineer", "Investment Banker", "Surgeon", 
            "Corporate Lawyer", "Management Consultant", "VP of Engineering"
        ]
        
        # Generate customer data with high-income characteristics
        for i in range(2):
            profile.add_customer_data({
                "first_name": random.choice(["Alexander", "Victoria", "Christopher", "Elizabeth"]),
                "last_name": random.choice(["Wellington", "Pemberton", "Ashworth", "Blackwood"]),
                "age": random.randint(35, 45),  # Slightly older
                "employment_status": random.choice(high_income_jobs),
                "role": "primary" if i == 0 else "spouse",
                "is_banking_customer": True
            })
        
        # High-income account structure
        accounts_data = [
            {
                "account_type": "checking",
                "ownership": "joint",
                "initial_balance": random.randint(25000, 75000),  # Higher balances
                "purpose": "primary checking"
            },
            {
                "account_type": "savings",
                "ownership": "joint", 
                "initial_balance": random.randint(100000, 300000),  # Substantial savings
                "purpose": "emergency fund"
            },
            {
                "account_type": "savings",
                "ownership": "joint",
                "initial_balance": random.randint(50000, 150000),
                "purpose": "investment fund"
            }
        ]
        
        for account_data in accounts_data:
            profile.add_account_data(account_data)
        
        self._add_high_income_transaction_profile(profile)
    
    def _add_high_income_transaction_profile(self, profile: Profile):
        """Add high-income transaction patterns."""
        from ..models import TransactionProfile
        
        tx_profile = TransactionProfile()
        
        # Higher income sources
        tx_profile.income_sources = [
            {
                "type": "salary",
                "amount": float(profile.household_income) * 0.65,
                "frequency": "biweekly",
                "description": "Executive salary"
            },
            {
                "type": "salary", 
                "amount": float(profile.household_income) * 0.35,
                "frequency": "biweekly",
                "description": "Professional salary"
            }
        ]
        
        # High-income spending patterns
        monthly_mortgage = int(float(profile.household_income) * 0.35 / 12)  # Higher housing costs
        
        tx_profile.spending_categories = {
            "groceries": {"avg_amount": 300 + (profile.total_members * 50), 
                         "frequency": "weekly", "variability": "medium"},
            "gas": {"avg_amount": 120, "frequency": "weekly", "variability": "low"},
            "utilities": {"avg_amount": 400 + (profile.total_members * 75), 
                         "frequency": "monthly", "variability": "low"},
            "mortgage": {"avg_amount": monthly_mortgage, 
                        "frequency": "monthly", "variability": "none"},
            "childcare": {"avg_amount": 1500 + ((profile.total_members - 2) * 500), 
                         "frequency": "monthly", "variability": "low"},
            "restaurant": {"avg_amount": 100 + (profile.total_members * 25), 
                          "frequency": "weekly", "variability": "high"},
            "entertainment": {"avg_amount": 300 + (profile.total_members * 50), 
                            "frequency": "monthly", "variability": "high"},
            "shopping": {"avg_amount": 500 + (profile.total_members * 100), 
                        "frequency": "monthly", "variability": "high"},
            "travel": {"avg_amount": 2000, "frequency": "monthly", "variability": "high"},
            "luxury": {"avg_amount": 1000, "frequency": "monthly", "variability": "high"}
        }
        
        profile.add_transaction_profile("household", tx_profile)
    
    def get_strategy_name(self) -> str:
        return "high_income"


class YoungSingleStrategy(ProfileBuildingStrategy):
    """Strategy for young single professional profiles."""
    
    def build_profile(self, template: ProfileTemplate, profile_name: str, 
                     seed: int, **kwargs) -> Profile:
        random.seed(seed)
        
        profile = Profile(
            template_id=template.template_id,
            name=profile_name,
            description=kwargs.get('description', f"Young professional profile based on {template.name}"),
            household_type=kwargs.get('household_type', 'single'),
            total_members=kwargs.get('total_members', 1),
            banking_members=kwargs.get('banking_members', 1),
            household_income=kwargs.get('household_income', 
                                      Decimal(str(random.randint(45000, 85000)))),
            generation_seed=seed
        )
        
        self._add_young_single_data(profile, template, seed)
        
        return profile
    
    def _add_young_single_data(self, profile: Profile, template: ProfileTemplate, seed: int):
        """Add young single professional data."""
        random.seed(seed)
        
        # Young professional jobs
        young_professional_jobs = [
            "Junior Software Developer", "Marketing Coordinator", "Financial Analyst", 
            "Graphic Designer", "Data Analyst", "Sales Representative"
        ]
        
        profile.add_customer_data({
            "first_name": random.choice(["Alex", "Jordan", "Taylor", "Casey", "Riley"]),
            "last_name": random.choice(["Chen", "Patel", "Kim", "Rodriguez", "Johnson"]),
            "age": random.randint(22, 30),
            "employment_status": random.choice(young_professional_jobs),
            "role": "primary",
            "is_banking_customer": True
        })
        
        # Simple account structure for single person
        accounts_data = [
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
        
        for account_data in accounts_data:
            profile.add_account_data(account_data)
        
        self._add_young_single_transaction_profile(profile)
    
    def _add_young_single_transaction_profile(self, profile: Profile):
        """Add young single transaction patterns."""
        from ..models import TransactionProfile
        
        tx_profile = TransactionProfile()
        
        # Single income source
        tx_profile.income_sources = [
            {
                "type": "salary",
                "amount": float(profile.household_income),
                "frequency": "biweekly",
                "description": "Primary salary"
            }
        ]
        
        # Young single spending patterns
        monthly_rent = int(float(profile.household_income) * 0.30 / 12)
        
        tx_profile.spending_categories = {
            "groceries": {"avg_amount": 75, "frequency": "weekly", "variability": "medium"},
            "gas": {"avg_amount": 50, "frequency": "weekly", "variability": "low"},
            "utilities": {"avg_amount": 150, "frequency": "monthly", "variability": "low"},
            "rent": {"avg_amount": monthly_rent, "frequency": "monthly", "variability": "none"},
            "restaurant": {"avg_amount": 60, "frequency": "weekly", "variability": "high"},
            "entertainment": {"avg_amount": 200, "frequency": "monthly", "variability": "high"},
            "shopping": {"avg_amount": 150, "frequency": "monthly", "variability": "high"},
            "subscriptions": {"avg_amount": 50, "frequency": "monthly", "variability": "low"}
        }
        
        profile.add_transaction_profile("individual", tx_profile)
    
    def get_strategy_name(self) -> str:
        return "young_single"


class ProfileStrategyRegistry:
    """Registry for profile building strategies."""
    
    _strategies: Dict[str, ProfileBuildingStrategy] = {}
    
    @classmethod
    def register_strategy(cls, strategy: ProfileBuildingStrategy):
        """Register a new strategy."""
        cls._strategies[strategy.get_strategy_name()] = strategy
    
    @classmethod
    def get_strategy(cls, name: str) -> ProfileBuildingStrategy:
        """Get strategy by name."""
        if name not in cls._strategies:
            raise ValueError(f"Unknown strategy: {name}")
        return cls._strategies[name]
    
    @classmethod
    def list_strategies(cls) -> list[str]:
        """List available strategy names."""
        return list(cls._strategies.keys())


# Register built-in strategies
ProfileStrategyRegistry.register_strategy(StandardFamilyStrategy())
ProfileStrategyRegistry.register_strategy(HighIncomeStrategy())
ProfileStrategyRegistry.register_strategy(YoungSingleStrategy())