"""
Banking domain data models for SyFi AI.

This module provides clean access to all banking models through organized submodules.
Import models directly from this package for convenience.
"""

# Import all enums
from .enums import (
    AccountType,
    TransactionType,
    TransactionCategory
)

# Import core models
from .customer import Customer
from .account import Account  
from .transaction import Transaction

# Import profile models
from .profile import (
    ProfileTemplate,
    TransactionProfile,
    Profile
)

# Export all model classes for clean imports
__all__ = [
    # Enums
    'AccountType',
    'TransactionType', 
    'TransactionCategory',
    
    # Core Models
    'Customer',
    'Account',
    'Transaction',
    
    # Profile Models
    'ProfileTemplate',
    'TransactionProfile',
    'Profile'
]