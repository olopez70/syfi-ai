"""
Profile models for SyFi AI banking system.

This module defines profile-related dataclasses for customer profiling and templating.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, List, Any
import uuid


@dataclass
class ProfileTemplate:
    """
    Represents a natural language template for creating banking customer profiles.
    
    Contains a user-provided description that describes a banking customer or group 
    of customers (e.g. household or network). This template is used to generate 
    one or more detailed Profiles.
    """
    
    template_id: str = field(default_factory=lambda: f"TMPL_{str(uuid.uuid4().hex[:8]).upper()}")
    name: str = ""
    description: str = ""
    created_date: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    
    # Template metadata and tags for organization
    tags: List[str] = field(default_factory=list)
    category: str = ""  # e.g., "household", "individual", "business", "network"
    complexity_level: str = "medium"  # "simple", "medium", "complex"
    
    # Usage tracking
    usage_count: int = 0
    last_used_date: Optional[datetime] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'created_date': self.created_date.isoformat(),
            'created_by': self.created_by,
            'tags': self.tags,
            'category': self.category,
            'complexity_level': self.complexity_level,
            'usage_count': self.usage_count,
            'last_used_date': self.last_used_date.isoformat() if self.last_used_date else None,
            'metadata': self.metadata
        }


@dataclass
class TransactionProfile:
    """
    Represents transaction patterns and behaviors for a customer.
    
    Contains information about how a customer typically conducts banking activities,
    including income patterns, spending habits, and transaction frequencies.
    """
    
    profile_id: str = field(default_factory=lambda: f"TXPF_{str(uuid.uuid4().hex[:8]).upper()}")
    
    # Income patterns
    income_sources: List[Dict[str, Any]] = field(default_factory=list)  
    # e.g., [{"type": "salary", "amount": 5000, "frequency": "monthly", "description": "direct deposit"}]
    
    # Spending patterns
    spending_categories: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # e.g., {"groceries": {"avg_amount": 150, "frequency": "weekly", "variability": "low"}}
    
    # Transaction timing and behavior
    transaction_frequency: Dict[str, Any] = field(default_factory=dict)
    seasonal_patterns: Dict[str, Any] = field(default_factory=dict)
    
    # Payment methods and preferences
    preferred_payment_methods: List[str] = field(default_factory=list)
    
    # Additional behavioral data
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'profile_id': self.profile_id,
            'income_sources': self.income_sources,
            'spending_categories': self.spending_categories,
            'transaction_frequency': self.transaction_frequency,
            'seasonal_patterns': self.seasonal_patterns,
            'preferred_payment_methods': self.preferred_payment_methods,
            'metadata': self.metadata
        }


@dataclass
class Profile:
    """
    Represents a detailed banking customer profile generated from a ProfileTemplate.
    
    Contains comprehensive information about customers, their relationships, accounts,
    and transaction patterns. Has sufficient detail to generate Customer, Account, 
    and Transaction records.
    """
    
    profile_id: str = field(default_factory=lambda: f"PROF_{str(uuid.uuid4().hex[:8]).upper()}")
    template_id: Optional[str] = None  # Reference to the ProfileTemplate used
    name: str = ""
    description: str = ""
    created_date: datetime = field(default_factory=datetime.now)
    
    # Household/Group Information
    household_type: str = "individual"  # "individual", "household", "family", "business"
    total_members: int = 1
    banking_members: int = 1  # Members who are actual banking customers
    
    # Customer Information (semi-structured)
    customers_data: List[Dict[str, Any]] = field(default_factory=list)
    # Each dict contains customer details like name, age, role, employment, etc.
    
    # Account Information (semi-structured)
    accounts_data: List[Dict[str, Any]] = field(default_factory=list)
    # Each dict contains account details like type, ownership, balances, terms, etc.
    
    # Transaction Profiles for each customer
    transaction_profiles: Dict[str, "TransactionProfile"] = field(default_factory=dict)
    # Key is customer identifier, value is their TransactionProfile
    
    # Relationships and dependencies
    customer_relationships: Dict[str, Any] = field(default_factory=dict)
    # e.g., joint accounts, authorized users, beneficiaries, etc.
    
    # Financial characteristics
    household_income: Optional[Decimal] = None
    total_assets: Optional[Decimal] = None
    total_liabilities: Optional[Decimal] = None
    credit_profile: Dict[str, Any] = field(default_factory=dict)
    
    # Life events and timeline
    life_events: List[Dict[str, Any]] = field(default_factory=list)
    # e.g., marriage, home purchase, job changes, etc.
    
    # Generation parameters
    generation_seed: Optional[int] = None  # For reproducible generation
    generation_parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Tracking and metadata
    is_active: bool = True
    last_generated_date: Optional[datetime] = None
    generation_count: int = 0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_customer_data(self, customer_data: Dict[str, Any]) -> None:
        """Add customer data to the profile."""
        self.customers_data.append(customer_data)
    
    def add_account_data(self, account_data: Dict[str, Any]) -> None:
        """Add account data to the profile."""
        self.accounts_data.append(account_data)
    
    def add_transaction_profile(self, customer_id: str, tx_profile: TransactionProfile) -> None:
        """Add a transaction profile for a customer."""
        self.transaction_profiles[customer_id] = tx_profile
    
    def get_banking_customers(self) -> List[Dict[str, Any]]:
        """Get list of customers who are actual banking customers."""
        return [customer for customer in self.customers_data 
                if customer.get('is_banking_customer', True)]
    
    def get_joint_accounts(self) -> List[Dict[str, Any]]:
        """Get list of joint accounts."""
        return [account for account in self.accounts_data 
                if account.get('ownership_type') == 'joint']
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'profile_id': self.profile_id,
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'created_date': self.created_date.isoformat(),
            'household_type': self.household_type,
            'total_members': self.total_members,
            'banking_members': self.banking_members,
            'customers_data': self.customers_data,
            'accounts_data': self.accounts_data,
            'transaction_profiles': {k: v.to_dict() for k, v in self.transaction_profiles.items()},
            'customer_relationships': self.customer_relationships,
            'household_income': str(self.household_income) if self.household_income else None,
            'total_assets': str(self.total_assets) if self.total_assets else None,
            'total_liabilities': str(self.total_liabilities) if self.total_liabilities else None,
            'credit_profile': self.credit_profile,
            'life_events': self.life_events,
            'generation_seed': self.generation_seed,
            'generation_parameters': self.generation_parameters,
            'is_active': self.is_active,
            'last_generated_date': self.last_generated_date.isoformat() if self.last_generated_date else None,
            'generation_count': self.generation_count,
            'tags': self.tags,
            'metadata': self.metadata
        }