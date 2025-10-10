"""
Banking domain validation tests.

Tests business rules and financial data consistency requirements.
"""

import pytest
import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from src.syfi.models import Customer, Account, Transaction, AccountType, TransactionType


@pytest.mark.banking
class TestAccountValidation:
    """Test banking account business rules."""
    
    def test_checking_account_rules(self, sample_customer):
        """Test checking account validation rules."""
        checking_account = Account(
            account_id="CHK_001",
            customer_id=sample_customer.customer_id,
            account_number="1234567890",
            account_type=AccountType.CHECKING,
            balance=Decimal('1000.00'),
            available_balance=Decimal('1000.00'),
            currency="USD",
            is_active=True
        )
        
        # Checking account should be active
        assert checking_account.is_active
        
        # Account type should be CHECKING
        assert checking_account.account_type == AccountType.CHECKING
        
        # Available balance should not exceed actual balance
        assert checking_account.available_balance <= checking_account.balance
    
    def test_credit_account_rules(self, sample_customer):
        """Test credit account validation rules."""
        credit_account = Account(
            account_id="CC_001",
            customer_id=sample_customer.customer_id,
            account_number="4567890123",
            account_type=AccountType.CREDIT,
            balance=Decimal('-500.00'),  # Negative balance indicates debt
            available_balance=Decimal('1500.00'),  # Available credit
            currency="USD",
            is_active=True
        )
        
        # Credit account should be active
        assert credit_account.is_active
        
        # Account type should be CREDIT
        assert credit_account.account_type == AccountType.CREDIT
        
        # Credit accounts can have negative balances (debt)
        assert credit_account.balance < 0
    
    def test_savings_account_rules(self, sample_customer):
        """Test savings account validation rules."""
        savings_account = Account(
            account_id="SAV_001",
            customer_id=sample_customer.customer_id,
            account_number="7890123456",
            account_type=AccountType.SAVINGS,
            balance=Decimal('5000.00'),
            available_balance=Decimal('5000.00'),
            currency="USD",
            is_active=True
        )
        
        # Savings account should be active
        assert savings_account.is_active
        
        # Account type should be SAVINGS
        assert savings_account.account_type == AccountType.SAVINGS
        
        # Balance should be non-negative
        assert savings_account.balance >= 0


@pytest.mark.banking
class TestTransactionValidation:
    """Test transaction business rules."""
    
    def test_debit_transaction_rules(self, sample_account):
        """Test debit transaction validation."""
        debit_transaction = Transaction(
            transaction_id="TXN_DEBIT_001",
            account_id=sample_account.account_id,
            transaction_type=TransactionType.DEBIT,
            amount=Decimal('-50.00'),  # Negative for debit
            currency="USD",
            description="ATM Withdrawal",
            category="cash",
            merchant_name="Bank ATM",
            merchant_category="banking",
            transaction_date=datetime.now().isoformat(),
            posted_date=datetime.now().isoformat(),
            reference_number="ATM123456",
            balance_after=Decimal('1424.50')  # Original balance 1474.50 - 50
        )
        
        # Debit amounts should be negative
        assert debit_transaction.amount < 0
        
        # Balance after should be less than original balance for debits
        original_balance = sample_account.balance
        expected_balance = original_balance + debit_transaction.amount
        assert abs(debit_transaction.balance_after - expected_balance) < Decimal('0.01')
    
    def test_credit_transaction_rules(self, sample_account):
        """Test credit transaction validation."""
        credit_transaction = Transaction(
            transaction_id="TXN_CREDIT_001", 
            account_id=sample_account.account_id,
            transaction_type=TransactionType.CREDIT,
            amount=Decimal('1000.00'),  # Positive for credit
            currency="USD",
            description="Salary Deposit",
            category="income",
            merchant_name="Employer Corp",
            merchant_category="payroll",
            transaction_date=datetime.now().isoformat(),
            posted_date=datetime.now().isoformat(),
            reference_number="PAY123456",
            balance_after=Decimal('2474.50')  # Original balance 1474.50 + 1000
        )
        
        # Credit amounts should be positive
        assert credit_transaction.amount > 0
        
        # Balance after should be more than original balance for credits
        original_balance = sample_account.balance
        expected_balance = original_balance + credit_transaction.amount
        assert abs(credit_transaction.balance_after - expected_balance) < Decimal('0.01')
    
    def test_transaction_date_validation(self, sample_account):
        """Test transaction date business rules."""
        now = datetime.now()
        
        # Transaction date should not be in the future
        future_transaction = Transaction(
            transaction_id="TXN_FUTURE_001",
            account_id=sample_account.account_id,
            transaction_type=TransactionType.DEBIT,
            amount=-10.00,
            currency="USD", 
            description="Future Transaction",
            category="test",
            transaction_date=(now - timedelta(days=1)).isoformat(),
            posted_date=now.isoformat(),
            reference_number="FUT123456",
            balance_after=1490.00
        )
        
        # Validate that transaction date is not in future
        transaction_date = datetime.fromisoformat(future_transaction.transaction_date.replace('Z', '+00:00'))
        assert transaction_date <= now + timedelta(minutes=5)  # Allow small clock skew
        
        # Posted date should be same or after transaction date
        posted_date = datetime.fromisoformat(future_transaction.posted_date.replace('Z', '+00:00'))
        assert posted_date >= transaction_date


@pytest.mark.banking
class TestCustomerValidation:
    """Test customer data business rules."""
    
    def test_customer_age_validation(self):
        """Test customer age requirements."""
        from datetime import date
        
        # Adult customer (18+)
        adult_customer = Customer(
            customer_id="ADULT_001",
            first_name="John",
            last_name="Adult",
            email="john.adult@test.com",
            phone="555-0123",
            date_of_birth="1990-01-01",  # 34 years old
            household_income=50000.0,
            employment_status="employed"
        )
        
        # Calculate age
        birth_date = date.fromisoformat(adult_customer.date_of_birth)
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        
        # Customer should be adult (18+) for most banking products
        assert age >= 18, f"Customer age {age} is below minimum banking age"
        
        # Senior customers (65+) may have different product eligibility
        is_senior = age >= 65
        print(f"Customer age: {age}, Senior: {is_senior}")
    
    def test_income_validation(self, sample_customer):
        """Test customer income validation rules."""
        # Income should be non-negative
        assert sample_customer.household_income >= 0
        
        # Income should be reasonable (not excessive)
        assert sample_customer.household_income <= 10_000_000  # $10M max
        
        # Income should align with employment status
        if sample_customer.employment_status == "unemployed":
            # Unemployed customers may still have investment income, benefits, etc.
            assert sample_customer.household_income <= 100_000  # Reasonable for non-employment income
    
    def test_contact_information_validation(self, sample_customer):
        """Test customer contact information rules.""" 
        # Email should contain @ symbol
        assert "@" in sample_customer.email
        
        # Phone should be reasonable length
        # Remove non-digits for validation
        digits_only = ''.join(filter(str.isdigit, sample_customer.phone))
        assert 10 <= len(digits_only) <= 15  # US phones typically 10 digits


@pytest.mark.banking
class TestBalanceConsistency:
    """Test balance consistency across accounts and transactions."""
    
    def test_account_balance_consistency(self, populated_database):
        """Test that account balances match transaction history."""
        db = populated_database
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get account with transactions
        cursor.execute("""
            SELECT account_id, balance FROM accounts 
            WHERE account_id IN (SELECT DISTINCT account_id FROM transactions)
            LIMIT 1
        """)
        account_result = cursor.fetchone()
        
        if account_result:
            account_id, current_balance = account_result
            
            # Calculate balance from transaction history
            cursor.execute("""
                SELECT SUM(amount) as total_amount 
                FROM transactions 
                WHERE account_id = ?
                ORDER BY transaction_date
            """, (account_id,))
            
            transaction_total = cursor.fetchone()[0] or 0
            
            # Get initial balance (would need to be tracked separately in real system)
            # For testing, assume current balance represents the correct state
            
            # Verify the last transaction's balance_after matches account balance
            cursor.execute("""
                SELECT balance_after FROM transactions 
                WHERE account_id = ? 
                ORDER BY transaction_date DESC 
                LIMIT 1
            """, (account_id,))
            
            last_transaction_balance = cursor.fetchone()
            if last_transaction_balance:
                assert abs(current_balance - last_transaction_balance[0]) < 0.01
    
    def test_currency_consistency(self, populated_database):
        """Test currency consistency across related records."""
        db = populated_database
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check that account and transaction currencies match
        cursor.execute("""
            SELECT a.currency as account_currency, t.currency as transaction_currency
            FROM accounts a
            JOIN transactions t ON a.account_id = t.account_id
        """)
        
        results = cursor.fetchall()
        for account_currency, transaction_currency in results:
            assert account_currency == transaction_currency, \
                f"Currency mismatch: Account {account_currency} vs Transaction {transaction_currency}"