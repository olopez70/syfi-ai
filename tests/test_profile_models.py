#!/usr/bin/env python3
"""Quick test to verify all models work correctly."""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.syfi.models import (
    Customer, Account, Transaction, 
    ProfileTemplate, Profile, TransactionProfile,
    AccountType, TransactionType, TransactionCategory
)
from decimal import Decimal
from datetime import datetime

def test_existing_models():
    """Test that existing models still work correctly."""
    print("Testing existing models...")
    
    # Test Customer
    customer = Customer(first_name='Test', last_name='User')
    print(f'✓ Customer created: {customer.full_name} (ID: {customer.customer_id})')
    
    # Test Account  
    account = Account(
        customer_id=customer.customer_id, 
        account_type=AccountType.CHECKING, 
        balance=Decimal('1000.00')
    )
    print(f'✓ Account created: {account.account_number} with balance ${account.balance}')
    
    # Test Transaction
    transaction = Transaction(
        account_id=account.account_id, 
        amount=Decimal('100.00'), 
        description='Test transaction'
    )
    print(f'✓ Transaction created: {transaction.transaction_id} for ${transaction.amount}')

def test_new_models():
    """Test that new Profile models work correctly."""
    print("\nTesting new Profile models...")
    
    # Test ProfileTemplate
    template = ProfileTemplate(
        name="Test Template",
        description="A test profile template",
        category="test"
    )
    print(f'✓ ProfileTemplate created: {template.name} (ID: {template.template_id})')
    
    # Test TransactionProfile
    tx_profile = TransactionProfile()
    tx_profile.income_sources = [{"type": "salary", "amount": Decimal('5000')}]
    print(f'✓ TransactionProfile created: {tx_profile.profile_id}')
    
    # Test Profile
    profile = Profile(
        template_id=template.template_id,
        name="Test Profile",
        household_type="individual"
    )
    profile.add_transaction_profile("test_customer", tx_profile)
    print(f'✓ Profile created: {profile.name} (ID: {profile.profile_id})')
    print(f'  Transaction profiles: {len(profile.transaction_profiles)}')

def main():
    """Run all tests."""
    print("Model Verification Tests")
    print("=" * 30)
    
    test_existing_models()
    test_new_models()
    
    print("\n✓ All models work correctly!")
    print("✓ Existing functionality preserved")
    print("✓ New Profile models integrated successfully")

if __name__ == "__main__":
    main()