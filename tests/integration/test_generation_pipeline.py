"""
Integration tests for end-to-end data generation pipeline.

Tests the complete workflow from configuration to data generation.
"""

import pytest
import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path for imports  
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from src.syfi import SyFiGenerator
from src.syfi.core.parser import ConfigurationParser
from src.syfi.database import DatabaseManager
from src.syfi.generators import CustomerGenerator


@pytest.mark.integration
class TestGenerationPipeline:
    """Test complete data generation pipeline."""
    
    def test_natural_language_to_database(self, temp_db):
        """Test full pipeline: NLP → Configuration → Generation → Database."""
        # Step 1: Parse natural language
        parser = ConfigurationParser()
        config = parser.parse("Generate 3 customers with checking accounts")
        
        # Step 2: Create generator and database
        generator = SyFiGenerator()
        generator.config = config
        
        db_manager = DatabaseManager(temp_db)
        db_manager.initialize_schema()
        
        # Step 3: Generate customers (mock implementation for now)
        customer_gen = CustomerGenerator(seed=12345)
        customers, accounts = customer_gen.generate_customers(3, accounts_per_customer=1)
        
        # Step 4: Store in database
        db_manager.insert_customers(customers)
        db_manager.insert_accounts(accounts)
        
        # Step 5: Verify data in database
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM customers")
        customer_count = cursor.fetchone()[0]
        assert customer_count == 3
        
        cursor.execute("SELECT COUNT(*) FROM accounts")
        account_count = cursor.fetchone()[0]
        assert account_count >= 3  # At least one account per customer
        
        conn.close()
    
    def test_configuration_serialization_roundtrip(self, temp_db):
        """Test configuration save and load maintains consistency."""
        parser = ConfigurationParser()
        original_config = parser.parse("Generate monthly salary $3000")
        
        # Save configuration
        config_path = Path(temp_db).parent / "test_config.json"
        original_config.save_to_file(config_path)
        
        # Load configuration
        from src.syfi.core.config import Configuration
        loaded_config = Configuration.load_from_file(config_path)
        
        # Verify consistency
        assert loaded_config.metadata["source_text"] == original_config.metadata["source_text"]
        assert len(loaded_config.transaction_patterns) == len(original_config.transaction_patterns)
        
        # Verify patterns match
        orig_pattern = original_config.transaction_patterns[0]
        loaded_pattern = loaded_config.transaction_patterns[0]
        
        assert orig_pattern.type == loaded_pattern.type
        assert orig_pattern.category == loaded_pattern.category
        assert orig_pattern.amount.value == loaded_pattern.amount.value
        
        # Cleanup
        config_path.unlink()


@pytest.mark.integration 
class TestDatabaseOperations:
    """Test multi-table database operations."""
    
    def test_customer_account_relationship(self, populated_database):
        """Test customer-account relationships in database."""
        db = populated_database
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Test JOIN query
        cursor.execute("""
            SELECT c.customer_id, c.first_name, a.account_number, a.account_type
            FROM customers c 
            JOIN accounts a ON c.customer_id = a.customer_id
        """)
        
        results = cursor.fetchall()
        assert len(results) > 0
        
        # Verify relationship integrity
        customer_id, first_name, account_number, account_type = results[0]
        assert customer_id is not None
        assert first_name is not None
        assert account_number is not None
        assert account_type is not None
    
    def test_transaction_balance_consistency(self, populated_database):
        """Test transaction balance calculations."""
        db = populated_database
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get account balance
        cursor.execute("SELECT balance FROM accounts WHERE account_id = 'ACC_001'")
        account_balance = cursor.fetchone()[0]
        
        # Get last transaction balance
        cursor.execute("""
            SELECT balance_after FROM transactions 
            WHERE account_id = 'ACC_001' 
            ORDER BY transaction_date DESC LIMIT 1
        """)
        last_transaction_balance = cursor.fetchone()[0]
        
        # Balances should match
        assert abs(account_balance - last_transaction_balance) < 0.01
    
    def test_bulk_insertion_performance(self, temp_db):
        """Test bulk data insertion performance."""
        db_manager = DatabaseManager(temp_db)
        db_manager.initialize_schema()
        
        customer_gen = CustomerGenerator(seed=54321)
        
        # Generate larger dataset
        start_time = datetime.now()
        customers, accounts = customer_gen.generate_customers(100, accounts_per_customer=2)
        
        # Bulk insert
        db_manager.insert_customers(customers)
        db_manager.insert_accounts(accounts)
            
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Should complete in reasonable time (adjust threshold as needed)
        assert duration < 30  # 30 seconds for 100 customers + 200 accounts
        
        # Verify all data inserted
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM customers")
        assert cursor.fetchone()[0] == 100
        
        cursor.execute("SELECT COUNT(*) FROM accounts") 
        account_count = cursor.fetchone()[0]
        assert account_count >= 100  # At least one account per customer
        
        conn.close()


@pytest.mark.integration
class TestExportIntegration:
    """Test data export functionality."""
    
    def test_database_to_csv_export(self, populated_database):
        """Test exporting database data to CSV."""
        # This test is placeholder - DataExporter class needs to be implemented
        # For now, just verify the populated_database fixture works
        assert populated_database is not None
        assert hasattr(populated_database, 'db_path')
    
    def test_configuration_to_generation_consistency(self, temp_db):
        """Test that same configuration produces consistent results."""
        parser = ConfigurationParser()
        
        # Parse same input twice
        config1 = parser.parse("Generate 5 customers with savings accounts")
        config2 = parser.parse("Generate 5 customers with savings accounts")
        
        # Should produce same configuration (with same seed)
        assert config1.generation.seed == config2.generation.seed
        
        # Test that generator produces consistent results with same seed
        gen1 = CustomerGenerator(seed=12345)
        gen2 = CustomerGenerator(seed=12345)
        
        customers1, _ = gen1.generate_customers(2)
        customers2, _ = gen2.generate_customers(2)
        
        # Basic consistency checks - at least should generate same number
        assert len(customers1) == len(customers2) == 2