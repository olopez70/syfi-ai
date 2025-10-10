"""
Transaction model for SyFi AI banking system.

This module defines the Transaction dataclass representing banking transactions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
import uuid

from .enums import TransactionType, TransactionCategory


@dataclass
class Transaction:
    """Represents a banking transaction."""
    
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    account_id: str = ""
    transaction_type: TransactionType = TransactionType.DEBIT
    amount: Decimal = field(default_factory=lambda: Decimal('0.00'))
    currency: str = "USD"
    description: str = ""
    category: TransactionCategory = TransactionCategory.OTHER
    merchant_name: Optional[str] = None
    merchant_category: Optional[str] = None
    transaction_date: datetime = field(default_factory=datetime.now)
    posted_date: Optional[datetime] = None
    reference_number: Optional[str] = None
    balance_after: Optional[Decimal] = None
    
    # For transfers and related transactions
    related_account_id: Optional[str] = None
    related_transaction_id: Optional[str] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization processing."""
        if self.posted_date is None:
            self.posted_date = self.transaction_date
            
        if self.reference_number is None:
            self.reference_number = f"TXN{uuid.uuid4().hex[:8].upper()}"
    
    def is_debit(self) -> bool:
        """Check if transaction is a debit."""
        return self.transaction_type in [
            TransactionType.DEBIT, 
            TransactionType.WITHDRAWAL, 
            TransactionType.PAYMENT,
            TransactionType.FEE
        ]
    
    def is_credit(self) -> bool:
        """Check if transaction is a credit."""
        return self.transaction_type in [
            TransactionType.CREDIT,
            TransactionType.DEPOSIT
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'transaction_id': self.transaction_id,
            'account_id': self.account_id,
            'transaction_type': self.transaction_type.value,
            'amount': float(self.amount),
            'currency': self.currency,
            'description': self.description,
            'category': self.category.value,
            'merchant_name': self.merchant_name,
            'merchant_category': self.merchant_category,
            'transaction_date': self.transaction_date.isoformat(),
            'posted_date': self.posted_date.isoformat() if self.posted_date else None,
            'reference_number': self.reference_number,
            'balance_after': float(self.balance_after) if self.balance_after else None,
            'related_account_id': self.related_account_id,
            'related_transaction_id': self.related_transaction_id,
            'metadata': self.metadata
        }