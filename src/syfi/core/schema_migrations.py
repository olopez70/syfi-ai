"""
Database schema migration utilities for bulk generation tracking
"""
import sqlite3
import uuid
from datetime import datetime
from typing import Optional

class SchemaManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    def execute_migration(self, migration_sql: str, description: str) -> bool:
        """Execute a schema migration with error handling"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Execute the migration
            cursor.executescript(migration_sql)
            conn.commit()
            
            print(f"Migration completed: {description}")
            return True
            
        except sqlite3.Error as e:
            print(f"Migration failed: {description}")
            print(f"Error: {e}")
            return False
        finally:
            if conn:
                conn.close()
                
    def add_bulk_generation_tracking(self) -> bool:
        """Add bulk generation tracking to the database"""
        migration_sql = """
        -- Create bulk_generations table to track all bulk generation operations
        CREATE TABLE IF NOT EXISTS bulk_generations (
            bulk_id TEXT PRIMARY KEY,
            label TEXT,
            operation_type TEXT NOT NULL,  -- 'customers', 'accounts', 'transactions', 'mixed'
            profile_description TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT DEFAULT 'system',
            total_customers_created INTEGER DEFAULT 0,
            total_accounts_created INTEGER DEFAULT 0,
            total_transactions_created INTEGER DEFAULT 0,
            status TEXT DEFAULT 'completed',  -- 'running', 'completed', 'failed'
            metadata TEXT  -- JSON for additional information
        );
        
        -- Add bulk_generation_id and bulk_generation_label columns to customers table
        ALTER TABLE customers ADD COLUMN bulk_generation_id TEXT;
        ALTER TABLE customers ADD COLUMN bulk_generation_label TEXT;
        
        -- Add bulk_generation_id and bulk_generation_label columns to accounts table  
        ALTER TABLE accounts ADD COLUMN bulk_generation_id TEXT;
        ALTER TABLE accounts ADD COLUMN bulk_generation_label TEXT;
        
        -- Add bulk_generation_id and bulk_generation_label columns to transactions table
        ALTER TABLE transactions ADD COLUMN bulk_generation_id TEXT;
        ALTER TABLE transactions ADD COLUMN bulk_generation_label TEXT;
        
        -- Create indexes for efficient searching
        CREATE INDEX IF NOT EXISTS idx_customers_bulk_id ON customers (bulk_generation_id);
        CREATE INDEX IF NOT EXISTS idx_accounts_bulk_id ON accounts (bulk_generation_id);
        CREATE INDEX IF NOT EXISTS idx_transactions_bulk_id ON transactions (bulk_generation_id);
        
        CREATE INDEX IF NOT EXISTS idx_customers_bulk_label ON customers (bulk_generation_label);
        CREATE INDEX IF NOT EXISTS idx_accounts_bulk_label ON accounts (bulk_generation_label);
        CREATE INDEX IF NOT EXISTS idx_transactions_bulk_label ON transactions (bulk_generation_label);
        """
        
        return self.execute_migration(migration_sql, "Adding bulk generation tracking")
    
    def check_bulk_generation_support(self) -> bool:
        """Check if the database supports bulk generation tracking"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if bulk_generations table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='bulk_generations'
            """)
            
            return cursor.fetchone() is not None
            
        except sqlite3.Error:
            return False
        finally:
            if conn:
                conn.close()
    
    def ensure_bulk_generation_support(self) -> bool:
        """Ensure the database supports bulk generation tracking, adding if needed"""
        if self.check_bulk_generation_support():
            print("Bulk generation tracking already supported")
            return True
        
        print("Adding bulk generation tracking support...")
        return self.add_bulk_generation_tracking()


class BulkGenerationTracker:
    """Utility class to manage bulk generation operations"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    def create_bulk_generation(self, operation_type: str, profile_description: str = None, 
                             label: str = None) -> str:
        """Create a new bulk generation record and return the bulk ID"""
        bulk_id = f"BULK_{uuid.uuid4().hex[:8].upper()}"
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO bulk_generations 
                (bulk_id, label, operation_type, profile_description, status)
                VALUES (?, ?, ?, ?, 'running')
            """, (bulk_id, label, operation_type, profile_description))
            
            conn.commit()
            return bulk_id
            
        except sqlite3.Error as e:
            print(f"Failed to create bulk generation: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def update_bulk_generation_stats(self, bulk_id: str, customers: int = 0, 
                                   accounts: int = 0, transactions: int = 0, 
                                   status: str = 'completed'):
        """Update the statistics for a bulk generation"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE bulk_generations 
                SET total_customers_created = ?, 
                    total_accounts_created = ?, 
                    total_transactions_created = ?,
                    status = ?
                WHERE bulk_id = ?
            """, (customers, accounts, transactions, status, bulk_id))
            
            conn.commit()
            
        except sqlite3.Error as e:
            print(f"Failed to update bulk generation stats: {e}")
        finally:
            if conn:
                conn.close()
    
    def get_bulk_generations(self, limit: int = 50) -> list:
        """Get list of bulk generations with their statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT bulk_id, label, operation_type, profile_description, 
                       created_date, total_customers_created, total_accounts_created,
                       total_transactions_created, status
                FROM bulk_generations 
                ORDER BY created_date DESC 
                LIMIT ?
            """, (limit,))
            
            columns = ['bulk_id', 'label', 'operation_type', 'profile_description',
                      'created_date', 'total_customers_created', 'total_accounts_created', 
                      'total_transactions_created', 'status']
            
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            print(f"Failed to get bulk generations: {e}")
            return []
        finally:
            if conn:
                conn.close()