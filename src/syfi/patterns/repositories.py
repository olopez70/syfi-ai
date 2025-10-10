"""
Repository Pattern Implementation for Data Access

Provides abstraction layer over data persistence with different implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from datetime import date

from ..models import Customer, Account, Transaction, Profile, ProfileTemplate


class CustomerRepository(ABC):
    """Abstract repository for customer data access."""
    
    @abstractmethod
    def save(self, customer: Customer) -> str:
        """Save a customer and return the ID."""
        pass
    
    @abstractmethod
    def save_batch(self, customers: List[Customer]) -> List[str]:
        """Save multiple customers."""
        pass
    
    @abstractmethod
    def find_by_id(self, customer_id: str) -> Optional[Customer]:
        """Find customer by ID."""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Customer]:
        """Find all customers."""
        pass
    
    @abstractmethod
    def find_by_income_range(self, min_income: float, max_income: float) -> List[Customer]:
        """Find customers by income range."""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Count total customers."""
        pass


class AccountRepository(ABC):
    """Abstract repository for account data access."""
    
    @abstractmethod
    def save(self, account: Account) -> str:
        """Save an account and return the ID."""
        pass
    
    @abstractmethod
    def save_batch(self, accounts: List[Account]) -> List[str]:
        """Save multiple accounts."""
        pass
    
    @abstractmethod
    def find_by_id(self, account_id: str) -> Optional[Account]:
        """Find account by ID."""
        pass
    
    @abstractmethod
    def find_by_customer_id(self, customer_id: str) -> List[Account]:
        """Find accounts for a customer."""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Account]:
        """Find all accounts."""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Count total accounts."""
        pass


class TransactionRepository(ABC):
    """Abstract repository for transaction data access."""
    
    @abstractmethod
    def save(self, transaction: Transaction) -> str:
        """Save a transaction and return the ID."""
        pass
    
    @abstractmethod
    def save_batch(self, transactions: List[Transaction]) -> List[str]:
        """Save multiple transactions."""
        pass
    
    @abstractmethod
    def find_by_id(self, transaction_id: str) -> Optional[Transaction]:
        """Find transaction by ID."""
        pass
    
    @abstractmethod
    def find_by_account_id(self, account_id: str) -> List[Transaction]:
        """Find transactions for an account."""
        pass
    
    @abstractmethod
    def find_by_date_range(self, start_date: date, end_date: date) -> List[Transaction]:
        """Find transactions in date range."""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Transaction]:
        """Find all transactions."""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Count total transactions."""
        pass


class ProfileRepository(ABC):
    """Abstract repository for profile data access."""
    
    @abstractmethod
    def save_template(self, template: ProfileTemplate) -> str:
        """Save a profile template."""
        pass
    
    @abstractmethod
    def save_profile(self, profile: Profile) -> str:
        """Save a profile."""
        pass
    
    @abstractmethod
    def find_template_by_id(self, template_id: str) -> Optional[ProfileTemplate]:
        """Find template by ID."""
        pass
    
    @abstractmethod
    def find_profile_by_id(self, profile_id: str) -> Optional[Profile]:
        """Find profile by ID."""
        pass
    
    @abstractmethod
    def list_templates(self) -> List[ProfileTemplate]:
        """List all templates."""
        pass
    
    @abstractmethod
    def list_profiles(self) -> List[Profile]:
        """List all profiles."""
        pass


class UnitOfWork(ABC):
    """Abstract unit of work for managing transactions across repositories."""
    
    @abstractmethod
    def __enter__(self):
        pass
    
    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    @abstractmethod
    def commit(self):
        """Commit all changes."""
        pass
    
    @abstractmethod
    def rollback(self):
        """Rollback all changes."""
        pass
    
    @property
    @abstractmethod
    def customers(self) -> CustomerRepository:
        """Get customer repository."""
        pass
    
    @property
    @abstractmethod
    def accounts(self) -> AccountRepository:
        """Get account repository."""
        pass
    
    @property
    @abstractmethod
    def transactions(self) -> TransactionRepository:
        """Get transaction repository."""
        pass
    
    @property
    @abstractmethod
    def profiles(self) -> ProfileRepository:
        """Get profile repository."""
        pass


# SQLite Implementation

class SQLiteCustomerRepository(CustomerRepository):
    """SQLite implementation of customer repository."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def save(self, customer: Customer) -> str:
        return self.save_batch([customer])[0]
    
    def save_batch(self, customers: List[Customer]) -> List[str]:
        return self.db_manager.insert_customers(customers)
    
    def find_by_id(self, customer_id: str) -> Optional[Customer]:
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_customer(row)
        return None
    
    def find_all(self) -> List[Customer]:
        customers_data = self.db_manager.get_all_customers()
        return [self._dict_to_customer(data) for data in customers_data]
    
    def find_by_income_range(self, min_income: float, max_income: float) -> List[Customer]:
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM customers WHERE household_income BETWEEN ? AND ?", 
            (min_income, max_income)
        )
        rows = cursor.fetchall()
        
        return [self._row_to_customer(row) for row in rows]
    
    def count(self) -> int:
        return self.db_manager.count_customers()
    
    def _row_to_customer(self, row) -> Customer:
        """Convert database row to Customer object."""
        from decimal import Decimal
        
        return Customer(
            customer_id=row['customer_id'],
            first_name=row['first_name'],
            last_name=row['last_name'],
            email=row['email'],
            phone=row['phone'],
            household_income=Decimal(str(row['household_income'])) if row['household_income'] else None,
            household_size=row['household_size'] or 1,
            employment_status=row['employment_status']
        )
    
    def _dict_to_customer(self, data: Dict[str, Any]) -> Customer:
        """Convert dictionary to Customer object."""
        from decimal import Decimal
        
        return Customer(
            customer_id=data['customer_id'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            household_income=Decimal(str(data['household_income'])) if data.get('household_income') else None,
            household_size=data.get('household_size', 1),
            employment_status=data.get('employment_status', '')
        )


class SQLiteAccountRepository(AccountRepository):
    """SQLite implementation of account repository."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def save(self, account: Account) -> str:
        return self.save_batch([account])[0]
    
    def save_batch(self, accounts: List[Account]) -> List[str]:
        return self.db_manager.insert_accounts(accounts)
    
    def find_by_id(self, account_id: str) -> Optional[Account]:
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM accounts WHERE account_id = ?", (account_id,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_account(row)
        return None
    
    def find_by_customer_id(self, customer_id: str) -> List[Account]:
        accounts_data = self.db_manager.get_accounts_for_customer(customer_id)
        return [self._dict_to_account(data) for data in accounts_data]
    
    def find_all(self) -> List[Account]:
        accounts_data = self.db_manager.get_all_accounts()
        return [self._dict_to_account(data) for data in accounts_data]
    
    def count(self) -> int:
        return self.db_manager.count_accounts()
    
    def _row_to_account(self, row) -> Account:
        """Convert database row to Account object."""
        from decimal import Decimal
        from ..models import AccountType
        
        return Account(
            account_id=row['account_id'],
            customer_id=row['customer_id'],
            account_type=AccountType(row['account_type']),
            balance=Decimal(str(row['balance'])),
            available_balance=Decimal(str(row['available_balance']))
        )
    
    def _dict_to_account(self, data: Dict[str, Any]) -> Account:
        """Convert dictionary to Account object."""
        from decimal import Decimal
        from ..models import AccountType
        
        return Account(
            account_id=data['account_id'],
            customer_id=data['customer_id'],
            account_type=AccountType(data['account_type']),
            balance=Decimal(str(data['balance'])),
            available_balance=Decimal(str(data['available_balance']))
        )


class SQLiteTransactionRepository(TransactionRepository):
    """SQLite implementation of transaction repository."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def save(self, transaction: Transaction) -> str:
        return self.save_batch([transaction])[0]
    
    def save_batch(self, transactions: List[Transaction]) -> List[str]:
        return self.db_manager.insert_transactions(transactions)
    
    def find_by_id(self, transaction_id: str) -> Optional[Transaction]:
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM transactions WHERE transaction_id = ?", (transaction_id,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_transaction(row)
        return None
    
    def find_by_account_id(self, account_id: str) -> List[Transaction]:
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM transactions WHERE account_id = ? ORDER BY transaction_date", 
                      (account_id,))
        rows = cursor.fetchall()
        
        return [self._row_to_transaction(row) for row in rows]
    
    def find_by_date_range(self, start_date: date, end_date: date) -> List[Transaction]:
        transactions_data = self.db_manager.get_transactions_for_period(start_date, end_date)
        return [self._dict_to_transaction(data) for data in transactions_data]
    
    def find_all(self) -> List[Transaction]:
        transactions_data = self.db_manager.get_all_transactions()
        return [self._dict_to_transaction(data) for data in transactions_data]
    
    def count(self) -> int:
        return self.db_manager.count_transactions()
    
    def _row_to_transaction(self, row) -> Transaction:
        """Convert database row to Transaction object."""
        from decimal import Decimal
        from datetime import datetime
        from ..models import TransactionType, TransactionCategory
        
        return Transaction(
            transaction_id=row['transaction_id'],
            account_id=row['account_id'],
            transaction_type=TransactionType(row['transaction_type']),
            amount=Decimal(str(row['amount'])),
            description=row['description'],
            category=TransactionCategory(row['category']),
            transaction_date=datetime.fromisoformat(row['transaction_date']) if isinstance(row['transaction_date'], str) else row['transaction_date'],
            merchant_name=row['merchant_name'],
            balance_after=Decimal(str(row['balance_after'])) if row['balance_after'] else None
        )
    
    def _dict_to_transaction(self, data: Dict[str, Any]) -> Transaction:
        """Convert dictionary to Transaction object."""
        from decimal import Decimal
        from datetime import datetime
        from ..models import TransactionType, TransactionCategory
        
        return Transaction(
            transaction_id=data['transaction_id'],
            account_id=data['account_id'],
            transaction_type=TransactionType(data['transaction_type']),
            amount=Decimal(str(data['amount'])),
            description=data['description'],
            category=TransactionCategory(data['category']),
            transaction_date=datetime.fromisoformat(data['transaction_date']) if isinstance(data['transaction_date'], str) else data['transaction_date'],
            merchant_name=data.get('merchant_name'),
            balance_after=Decimal(str(data['balance_after'])) if data.get('balance_after') else None
        )


class SQLiteProfileRepository(ProfileRepository):
    """SQLite implementation of profile repository."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        # Initialize profile tables if needed
        self._init_profile_tables()
    
    def _init_profile_tables(self):
        """Initialize profile-related tables."""
        # This would create profile and template tables
        # Implementation would go here
        pass
    
    def save_template(self, template: ProfileTemplate) -> str:
        # Implementation would save to profile_templates table
        return template.template_id
    
    def save_profile(self, profile: Profile) -> str:
        # Implementation would save to profiles table
        return profile.profile_id
    
    def find_template_by_id(self, template_id: str) -> Optional[ProfileTemplate]:
        # Implementation would query profile_templates table
        return None
    
    def find_profile_by_id(self, profile_id: str) -> Optional[Profile]:
        # Implementation would query profiles table
        return None
    
    def list_templates(self) -> List[ProfileTemplate]:
        # Implementation would query all templates
        return []
    
    def list_profiles(self) -> List[Profile]:
        # Implementation would query all profiles
        return []


class SQLiteUnitOfWork(UnitOfWork):
    """SQLite implementation of unit of work."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self._customers = SQLiteCustomerRepository(db_manager)
        self._accounts = SQLiteAccountRepository(db_manager)
        self._transactions = SQLiteTransactionRepository(db_manager)
        self._profiles = SQLiteProfileRepository(db_manager)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
    
    def commit(self):
        """Commit transaction."""
        conn = self.db_manager.get_connection()
        conn.commit()
    
    def rollback(self):
        """Rollback transaction."""
        conn = self.db_manager.get_connection()
        conn.rollback()
    
    @property
    def customers(self) -> CustomerRepository:
        return self._customers
    
    @property
    def accounts(self) -> AccountRepository:
        return self._accounts
    
    @property
    def transactions(self) -> TransactionRepository:
        return self._transactions
    
    @property
    def profiles(self) -> ProfileRepository:
        return self._profiles