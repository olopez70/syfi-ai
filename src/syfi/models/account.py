"""
Account model for SyFi AI banking system.

This module defines the Account dataclass representing bank accounts.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any
import uuid

from .enums import AccountType


@dataclass  
class Account:
    """Represents a bank account."""
    
    account_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    account_number: str = field(default_factory=lambda: f"ACC{uuid.uuid4().hex[:10].upper()}")
    account_type: AccountType = AccountType.CHECKING
    customer_id: str = ""
    balance: Decimal = field(default_factory=lambda: Decimal('0.00'))
    available_balance: Decimal = field(default_factory=lambda: Decimal('0.00'))
    currency: str = "USD"
    created_date: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    
    def __post_init__(self):
        """Post-initialization processing."""
        if self.available_balance == Decimal('0.00'):
            self.available_balance = self.balance
    
    def can_debit(self, amount: Decimal) -> bool:
        """Check if account can be debited for the given amount."""
        if self.account_type == AccountType.CREDIT:
            # Credit accounts have different logic
            return True
        return self.available_balance >= amount
    
    def debit(self, amount: Decimal) -> bool:
        """Debit the account. Returns True if successful."""
        if not self.can_debit(amount):
            return False
        
        self.balance -= amount
        self.available_balance -= amount
        return True
    
    def credit(self, amount: Decimal) -> None:
        """Credit the account."""
        self.balance += amount
        self.available_balance += amount
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'account_id': self.account_id,
            'account_number': self.account_number,
            'account_type': self.account_type.value,
            'customer_id': self.customer_id,
            'balance': float(self.balance),
            'available_balance': float(self.available_balance),
            'currency': self.currency,
            'created_date': self.created_date.isoformat(),
            'is_active': self.is_active
        }