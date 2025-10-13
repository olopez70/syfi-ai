"""
Database Schema Management for SyFi AI.

Provides schema versioning, validation, and migration capabilities
to prevent schema-code misalignment issues.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

class SchemaVersion(Enum):
    """Supported database schema versions."""
    V1_0_BASIC = "1.0.0"      # Basic customers, accounts tables
    V1_1_EXTENDED = "1.1.0"   # Added transactions, profiles
    V1_2_ENHANCED = "1.2.0"   # Added status, date columns
    CURRENT = V1_2_ENHANCED

@dataclass
class TableSchema:
    """Definition of a table schema."""
    name: str
    columns: Dict[str, str]  # column_name -> data_type
    required_columns: Set[str]
    optional_columns: Set[str]
    
@dataclass 
class DatabaseSchema:
    """Complete database schema definition."""
    version: SchemaVersion
    tables: Dict[str, TableSchema]
    relationships: Dict[str, List[str]]  # foreign_key -> referenced_tables

class SchemaManager:
    """Manages database schema validation and migrations."""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(__name__)
        
    def get_current_schema_version(self) -> Optional[SchemaVersion]:
        """Get the current schema version from database metadata."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if schema_info table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='schema_info'
            """)
            
            if cursor.fetchone():
                cursor.execute("SELECT version FROM schema_info ORDER BY created_at DESC LIMIT 1")
                result = cursor.fetchone()
                if result:
                    return SchemaVersion(result[0])
            
            # Fallback: detect version by analyzing existing tables
            return self._detect_schema_version(conn)
            
        except Exception as e:
            self.logger.warning(f"Could not determine schema version: {e}")
            return None
        finally:
            conn.close()
    
    def _detect_schema_version(self, conn: sqlite3.Connection) -> SchemaVersion:
        """Detect schema version by analyzing existing table structure."""
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        
        # Version detection logic
        if 'transactions' in tables and 'profile_description' in self._get_table_columns(conn, 'customers'):
            return SchemaVersion.V1_2_ENHANCED
        elif 'transactions' in tables:
            return SchemaVersion.V1_1_EXTENDED
        elif 'customers' in tables and 'accounts' in tables:
            return SchemaVersion.V1_0_BASIC
        else:
            return SchemaVersion.V1_0_BASIC  # Default/minimal
    
    def _get_table_columns(self, conn: sqlite3.Connection, table_name: str) -> Set[str]:
        """Get column names for a table."""
        cursor = conn.cursor()
        try:
            cursor.execute(f"PRAGMA table_info({table_name})")
            return {row[1] for row in cursor.fetchall()}  # row[1] is column name
        except sqlite3.OperationalError:
            return set()
    
    def validate_schema_compatibility(self, required_schema: DatabaseSchema) -> Dict[str, List[str]]:
        """Validate current database against required schema."""
        issues = {"missing_tables": [], "missing_columns": [], "incompatible_types": []}
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            for table_name, table_schema in required_schema.tables.items():
                if not self._table_exists(conn, table_name):
                    issues["missing_tables"].append(table_name)
                    continue
                
                current_columns = self._get_table_columns(conn, table_name)
                
                # Check required columns
                for required_col in table_schema.required_columns:
                    if required_col not in current_columns:
                        issues["missing_columns"].append(f"{table_name}.{required_col}")
                        
        except Exception as e:
            self.logger.error(f"Schema validation error: {e}")
            
        finally:
            conn.close()
            
        return issues
    
    def _table_exists(self, conn: sqlite3.Connection, table_name: str) -> bool:
        """Check if table exists in database."""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (table_name,))
        return cursor.fetchone() is not None

# Schema Definitions
SCHEMA_DEFINITIONS = {
    SchemaVersion.V1_2_ENHANCED: DatabaseSchema(
        version=SchemaVersion.V1_2_ENHANCED,
        tables={
            "customers": TableSchema(
                name="customers",
                columns={
                    "customer_id": "TEXT PRIMARY KEY",
                    "first_name": "TEXT NOT NULL", 
                    "last_name": "TEXT NOT NULL",
                    "email": "TEXT UNIQUE",
                    "phone": "TEXT",
                    "date_of_birth": "DATE",
                    "created_date": "DATE DEFAULT CURRENT_DATE",
                    "income": "DECIMAL(12,2)",
                    "credit_score": "INTEGER",
                    "profile_description": "TEXT"
                },
                required_columns={"customer_id", "first_name", "last_name"},
                optional_columns={"email", "phone", "date_of_birth", "income", "credit_score", "profile_description"}
            ),
            "accounts": TableSchema(
                name="accounts", 
                columns={
                    "account_id": "TEXT PRIMARY KEY",
                    "customer_id": "TEXT NOT NULL",
                    "account_type": "TEXT CHECK(account_type IN ('checking', 'savings', 'credit'))",
                    "balance": "DECIMAL(12,2) DEFAULT 0.00",
                    "opened_date": "DATE DEFAULT CURRENT_DATE",
                    "status": "TEXT DEFAULT 'active'",
                    "is_active": "INTEGER DEFAULT 1"
                },
                required_columns={"account_id", "customer_id", "account_type"},
                optional_columns={"balance", "opened_date", "status", "is_active"}
            ),
            "transactions": TableSchema(
                name="transactions",
                columns={
                    "transaction_id": "TEXT PRIMARY KEY",
                    "account_id": "TEXT NOT NULL",
                    "transaction_type": "TEXT CHECK(transaction_type IN ('debit', 'credit'))",
                    "amount": "DECIMAL(10,2) NOT NULL",
                    "transaction_date": "DATE DEFAULT CURRENT_DATE",
                    "description": "TEXT",
                    "category": "TEXT"
                },
                required_columns={"transaction_id", "account_id", "transaction_type", "amount"},
                optional_columns={"transaction_date", "description", "category"}
            )
        },
        relationships={
            "accounts.customer_id": ["customers.customer_id"],
            "transactions.account_id": ["accounts.account_id"]
        }
    )
}

def get_schema_manager(db_path: str) -> SchemaManager:
    """Factory function to create schema manager."""
    return SchemaManager(db_path)