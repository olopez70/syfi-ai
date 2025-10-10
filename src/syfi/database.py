"""
Database management for SyFi AI.

This module handles SQLite database operations including schema creation,
data insertion, and querying for the synthetic banking data system.
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
from dataclasses import asdict

from .models import Customer, Account, Transaction


# Configure SQLite adapters and converters for Python 3.12 compatibility
def adapt_datetime_iso(val):
    """Adapt datetime to ISO format string."""
    return val.isoformat()

def adapt_date_iso(val):
    """Adapt date to ISO format string."""
    return val.isoformat()

def convert_datetime(val):
    """Convert ISO format string back to datetime."""
    return datetime.fromisoformat(val.decode())

def convert_date(val):
    """Convert ISO format string back to date."""
    return date.fromisoformat(val.decode())

# Register adapters and converters
sqlite3.register_adapter(datetime, adapt_datetime_iso)
sqlite3.register_adapter(date, adapt_date_iso)
sqlite3.register_converter("datetime", convert_datetime)
sqlite3.register_converter("date", convert_date)

class DatabaseManager:
    """
    Manages SQLite database operations for SyFi AI banking data.
    
    Handles schema creation, data insertion, and querying for customers,
    accounts, and transactions.
    """
    
    def __init__(self, db_path: str):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.connection = None
    
    def get_connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self.connection is None:
            self.connection = sqlite3.connect(
                self.db_path, 
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            self.connection.row_factory = sqlite3.Row
        return self.connection
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def initialize_schema(self):
        """
        Create database schema for SyFi AI banking data.
        
        Creates tables for customers, accounts, transactions, and metadata.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Customers table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            company_name TEXT,  -- For business entities
            email TEXT,
            phone TEXT,
            date_of_birth DATE,
            address TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            ssn_hash TEXT,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            -- Household information
            household_size INTEGER DEFAULT 1,
            num_adults INTEGER DEFAULT 1,
            num_children INTEGER DEFAULT 0,
            num_pets INTEGER DEFAULT 0,
            household_income DECIMAL(15,2),
            employment_status TEXT,
            marital_status TEXT,
            
            -- Profile information
            profile_description TEXT,
            profile_tags TEXT,  -- JSON array of tags
            
            metadata TEXT  -- JSON for additional fields
        )
        """)
        
        # Accounts table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            account_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            account_number TEXT UNIQUE NOT NULL,
            account_type TEXT NOT NULL,
            balance DECIMAL(15,2) DEFAULT 0.00,
            available_balance DECIMAL(15,2) DEFAULT 0.00,
            currency TEXT DEFAULT 'USD',
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            closed_date DATE,
            is_active BOOLEAN DEFAULT 1,
            interest_rate DECIMAL(5,4),
            credit_limit DECIMAL(15,2),
            metadata TEXT,  -- JSON for additional fields
            FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
        )
        """)
        
        # Transactions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL,
            transaction_type TEXT NOT NULL,
            amount DECIMAL(15,2) NOT NULL,
            currency TEXT DEFAULT 'USD',
            description TEXT,
            category TEXT,
            merchant_name TEXT,
            merchant_category TEXT,
            transaction_date DATETIME NOT NULL,
            posted_date DATETIME,
            reference_number TEXT,
            balance_after DECIMAL(15,2),
            related_account_id TEXT,
            related_transaction_id TEXT,
            location TEXT,
            metadata TEXT,  -- JSON for additional fields
            FOREIGN KEY (account_id) REFERENCES accounts (account_id)
        )
        """)
        
        # Metadata table for generation tracking
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS generation_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            generation_type TEXT NOT NULL,  -- 'customers', 'accounts', 'transactions'
            generation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            parameters TEXT,  -- JSON with generation parameters
            record_count INTEGER,
            seed INTEGER,
            notes TEXT
        )
        """)
        
        # Profile templates table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS profile_templates (
            template_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            entity_type TEXT NOT NULL,  -- 'personal', 'business', 'non-profit'
            category TEXT NOT NULL,     -- 'Personal', 'Business', 'Non-profit'
            complexity_level TEXT NOT NULL,  -- 'Low', 'Medium', 'High'
            icon TEXT,
            color TEXT,
            typical_income_range TEXT,
            typical_accounts TEXT,      -- JSON array of account types
            typical_transactions TEXT,  -- JSON array of transaction patterns
            tags TEXT,                  -- JSON array of tags
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT               -- JSON for additional fields
        )
        """)
        
        # Profiles table (instances of templates used for customers)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            profile_id TEXT PRIMARY KEY,
            template_id TEXT NOT NULL,
            customer_id TEXT,          -- NULL until assigned to customer
            name TEXT NOT NULL,
            description TEXT,
            parameters TEXT,           -- JSON with generation parameters
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            used_date DATETIME,        -- When profile was used for generation
            metadata TEXT,             -- JSON for additional fields
            FOREIGN KEY (template_id) REFERENCES profile_templates (template_id),
            FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
        )
        """)

        # Create indexes for better query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_accounts_customer ON accounts (customer_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions (account_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions (transaction_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions (transaction_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_profiles_template ON profiles (template_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_profiles_customer ON profiles (customer_id)")
        
        conn.commit()
    
    def insert_customers(self, customers: List[Customer]) -> List[str]:
        """
        Insert customers into database.
        
        Args:
            customers: List of Customer objects to insert
            
        Returns:
            List of inserted customer IDs
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        customer_ids = []
        
        for customer in customers:
            customer_data = asdict(customer)
            
            # Convert metadata to JSON if present
            metadata = customer_data.pop('metadata', {})
            
            # Convert profile_tags to JSON if present
            profile_tags = customer_data.pop('profile_tags', [])
            
            cursor.execute("""
            INSERT OR REPLACE INTO customers (
                customer_id, first_name, last_name, company_name, email, phone, 
                date_of_birth, address, city, state, zip_code, ssn_hash, 
                created_date, household_size, num_adults, num_children, 
                num_pets, household_income, employment_status, marital_status,
                profile_description, profile_tags, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                customer_data['customer_id'],
                customer_data['first_name'], 
                customer_data['last_name'],
                customer_data.get('company_name', ''),
                customer_data['email'],
                customer_data['phone'],
                customer_data['date_of_birth'],
                customer_data.get('address', ''),
                customer_data.get('city', ''),
                customer_data.get('state', ''),
                customer_data.get('zip_code', ''),
                customer_data.get('ssn_hash', ''),
                customer_data['created_date'],
                customer_data.get('household_size', 1),
                customer_data.get('num_adults', 1),
                customer_data.get('num_children', 0),
                customer_data.get('num_pets', 0),
                str(customer_data.get('household_income')) if customer_data.get('household_income') else None,
                customer_data.get('employment_status', ''),
                customer_data.get('marital_status', ''),
                customer_data.get('profile_description', ''),
                json.dumps(profile_tags) if profile_tags else None,
                json.dumps(metadata) if metadata else None
            ))
            
            customer_ids.append(customer_data['customer_id'])
        
        conn.commit()
        return customer_ids
    
    def insert_accounts(self, accounts: List[Account]) -> List[str]:
        """
        Insert accounts into database.
        
        Args:
            accounts: List of Account objects to insert
            
        Returns:
            List of inserted account IDs
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        account_ids = []
        
        for account in accounts:
            account_data = asdict(account)
            
            # Convert enums to strings
            account_type = account_data['account_type']
            if hasattr(account_type, 'value'):
                account_type = account_type.value
            
            # Convert metadata to JSON if present
            metadata = account_data.pop('metadata', {})
            
            cursor.execute("""
            INSERT OR REPLACE INTO accounts (
                account_id, customer_id, account_number, account_type,
                balance, available_balance, currency, created_date, 
                is_active, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                account_data['account_id'],
                account_data['customer_id'],
                account_data['account_number'],
                account_type,
                float(account_data['balance']),
                float(account_data['available_balance']),
                account_data['currency'],
                account_data['created_date'],
                account_data['is_active'],
                json.dumps(metadata) if metadata else None
            ))
            
            account_ids.append(account_data['account_id'])
        
        conn.commit()
        return account_ids
    
    def insert_transactions(self, transactions: List[Transaction]) -> List[str]:
        """
        Insert transactions into database.
        
        Args:
            transactions: List of Transaction objects to insert
            
        Returns:
            List of inserted transaction IDs
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        transaction_ids = []
        
        for transaction in transactions:
            tx_data = asdict(transaction)
            
            # Convert enums to strings
            tx_type = tx_data['transaction_type']
            if hasattr(tx_type, 'value'):
                tx_type = tx_type.value
            
            category = tx_data['category']
            if hasattr(category, 'value'):
                category = category.value
            
            # Convert metadata to JSON if present
            metadata = tx_data.pop('metadata', {})
            
            cursor.execute("""
            INSERT OR REPLACE INTO transactions (
                transaction_id, account_id, transaction_type, amount,
                currency, description, category, merchant_name,
                merchant_category, transaction_date, posted_date,
                reference_number, balance_after, related_account_id,
                related_transaction_id, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tx_data['transaction_id'],
                tx_data['account_id'],
                tx_type,
                float(tx_data['amount']),
                tx_data['currency'],
                tx_data['description'],
                category,
                tx_data['merchant_name'],
                tx_data['merchant_category'],
                tx_data['transaction_date'],
                tx_data['posted_date'],
                tx_data['reference_number'],
                float(tx_data['balance_after']) if tx_data['balance_after'] else None,
                tx_data['related_account_id'],
                tx_data['related_transaction_id'],
                json.dumps(metadata) if metadata else None
            ))
            
            transaction_ids.append(tx_data['transaction_id'])
        
        conn.commit()
        return transaction_ids
    
    def get_all_customers(self) -> List[Dict[str, Any]]:
        """Get all customers from database."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM customers ORDER BY created_date")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_all_accounts(self) -> List[Dict[str, Any]]:
        """Get all accounts from database."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM accounts WHERE is_active = 1 ORDER BY created_date")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_accounts_for_customer(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get all accounts for a specific customer."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT * FROM accounts 
        WHERE customer_id = ? AND is_active = 1 
        ORDER BY created_date
        """, (customer_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_transactions_for_period(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Get transactions for a specific date range."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT * FROM transactions 
        WHERE DATE(transaction_date) BETWEEN ? AND ?
        ORDER BY transaction_date
        """, (start_date, end_date))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def count_customers(self) -> int:
        """Get total number of customers."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM customers")
        return cursor.fetchone()[0]
    
    def count_accounts(self) -> int:
        """Get total number of active accounts."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM accounts WHERE is_active = 1")
        return cursor.fetchone()[0]
    
    def count_transactions(self) -> int:
        """Get total number of transactions."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM transactions")
        return cursor.fetchone()[0]
    
    def get_transaction_date_range(self) -> Optional[Tuple[str, str]]:
        """Get the date range of transactions in the database."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT 
            MIN(DATE(transaction_date)) as min_date,
            MAX(DATE(transaction_date)) as max_date
        FROM transactions
        """)
        
        result = cursor.fetchone()
        if result and result[0]:
            return (result[0], result[1])
        return None
    
    def log_generation_metadata(self, generation_type: str, parameters: Dict[str, Any], 
                               record_count: int, seed: Optional[int] = None):
        """Log metadata about data generation."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO generation_metadata (
            generation_type, parameters, record_count, seed
        ) VALUES (?, ?, ?, ?)
        """, (
            generation_type,
            json.dumps(parameters),
            record_count,
            seed
        ))
        
        conn.commit()
    
    def insert_profile_template(self, template_id: str, name: str, description: str, 
                               entity_type: str, category: str, complexity_level: str,
                               icon: str = "", color: str = "", typical_income_range: str = "",
                               typical_accounts: List[str] = None, typical_transactions: List[str] = None,
                               tags: List[str] = None, metadata: Dict[str, Any] = None) -> str:
        """
        Insert profile template into database.
        
        Args:
            template_id: Unique identifier for template
            name: Template name
            description: Template description
            entity_type: Type of entity (personal, business, non-profit)
            category: Display category
            complexity_level: Complexity level (Low, Medium, High)
            icon: Display icon
            color: Display color
            typical_income_range: Income range description
            typical_accounts: List of typical account types
            typical_transactions: List of typical transaction patterns
            tags: List of tags
            metadata: Additional metadata
            
        Returns:
            The inserted template ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT OR REPLACE INTO profile_templates (
            template_id, name, description, entity_type, category, complexity_level,
            icon, color, typical_income_range, typical_accounts, typical_transactions,
            tags, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            template_id, name, description, entity_type, category, complexity_level,
            icon, color, typical_income_range,
            json.dumps(typical_accounts) if typical_accounts else None,
            json.dumps(typical_transactions) if typical_transactions else None,
            json.dumps(tags) if tags else None,
            json.dumps(metadata) if metadata else None
        ))
        
        conn.commit()
        return template_id
    
    def insert_profile(self, profile_id: str, template_id: str, name: str, 
                      description: str = "", customer_id: str = None,
                      parameters: Dict[str, Any] = None, metadata: Dict[str, Any] = None) -> str:
        """
        Insert profile instance into database.
        
        Args:
            profile_id: Unique identifier for profile
            template_id: ID of template this profile is based on
            name: Profile name
            description: Profile description
            customer_id: Customer this profile is assigned to (optional)
            parameters: Generation parameters used
            metadata: Additional metadata
            
        Returns:
            The inserted profile ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        used_date = datetime.now() if customer_id else None
        
        cursor.execute("""
        INSERT OR REPLACE INTO profiles (
            profile_id, template_id, customer_id, name, description,
            parameters, used_date, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            profile_id, template_id, customer_id, name, description,
            json.dumps(parameters) if parameters else None,
            used_date,
            json.dumps(metadata) if metadata else None
        ))
        
        conn.commit()
        return profile_id
    
    def get_profile_templates(self) -> List[Dict[str, Any]]:
        """Get all profile templates."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT 
            template_id, name, description, entity_type, category, complexity_level,
            icon, color, typical_income_range, typical_accounts, typical_transactions,
            tags, created_date, metadata
        FROM profile_templates
        ORDER BY category, name
        """)
        
        templates = []
        for row in cursor.fetchall():
            template = dict(row)
            # Parse JSON fields
            if template['typical_accounts']:
                template['typical_accounts'] = json.loads(template['typical_accounts'])
            if template['typical_transactions']:
                template['typical_transactions'] = json.loads(template['typical_transactions'])
            if template['tags']:
                template['tags'] = json.loads(template['tags'])
            if template['metadata']:
                template['metadata'] = json.loads(template['metadata'])
            templates.append(template)
        
        return templates
    
    def get_profiles_by_template(self, template_id: str) -> List[Dict[str, Any]]:
        """Get all profile instances for a specific template."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT 
            p.profile_id, p.template_id, p.customer_id, p.name, p.description,
            p.parameters, p.created_date, p.used_date, p.metadata,
            c.first_name, c.last_name
        FROM profiles p
        LEFT JOIN customers c ON p.customer_id = c.customer_id
        WHERE p.template_id = ?
        ORDER BY p.created_date DESC
        """, (template_id,))
        
        profiles = []
        for row in cursor.fetchall():
            profile = dict(row)
            # Parse JSON fields
            if profile['parameters']:
                profile['parameters'] = json.loads(profile['parameters'])
            if profile['metadata']:
                profile['metadata'] = json.loads(profile['metadata'])
            profiles.append(profile)
        
        return profiles
    
    def link_profile_to_customer(self, profile_id: str, customer_id: str):
        """Link a profile to a customer."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        UPDATE profiles 
        SET customer_id = ?, used_date = ?
        WHERE profile_id = ?
        """, (customer_id, datetime.now(), profile_id))
        
        conn.commit()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

# Export the DatabaseManager class
__all__ = ['DatabaseManager']