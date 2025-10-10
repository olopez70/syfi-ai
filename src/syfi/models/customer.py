"""
Customer model for SyFi AI banking system.

This module defines the Customer dataclass representing bank customers.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict, List, Any
import uuid


@dataclass
class Customer:
    """Represents a bank customer."""
    
    customer_id: str = field(default_factory=lambda: f"CUST{str(uuid.uuid4().hex[:6]).upper().zfill(6)}")
    first_name: str = ""
    last_name: str = ""
    company_name: str = ""  # For business entities
    email: str = ""
    phone: str = ""
    date_of_birth: Optional[date] = None
    created_date: datetime = field(default_factory=datetime.now)
    
    # Enhanced profile information
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    ssn_hash: str = ""
    
    # Household information
    household_size: int = 1
    num_adults: int = 1
    num_children: int = 0
    num_pets: int = 0
    household_income: Optional[Decimal] = None
    employment_status: str = ""
    marital_status: str = ""
    
    # Profile description and metadata
    profile_description: str = ""
    profile_tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def full_name(self) -> str:
        """Get customer's full name or company name."""
        if self.company_name:
            return self.company_name
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def full_address(self) -> str:
        """Get customer's full address."""
        parts = [self.address, self.city, self.state, self.zip_code]
        return ", ".join(part for part in parts if part)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'customer_id': self.customer_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'company_name': self.company_name,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'created_date': self.created_date.isoformat(),
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'household_size': self.household_size,
            'num_adults': self.num_adults,
            'num_children': self.num_children,
            'num_pets': self.num_pets,
            'household_income': str(self.household_income) if self.household_income else None,
            'employment_status': self.employment_status,
            'marital_status': self.marital_status,
            'profile_description': self.profile_description,
            'profile_tags': self.profile_tags
        }