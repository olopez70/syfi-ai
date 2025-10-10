"""
Shared test configuration and fixtures for SyFi AI test suite.

This file contains pytest fixtures and configuration shared across all test modules.
"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from typing import Generator, Dict, Any
import json

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from decimal import Decimal
from src.syfi.models import Customer, Account, Transaction, AccountType, TransactionType
from src.syfi.database import DatabaseManager
from src.syfi.generators import CustomerGenerator
from src.syfi.core.parser import ConfigurationParser


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Get the test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session") 
def test_db_dir(test_data_dir: Path) -> Path:
    """Get the test database directory."""
    db_dir = test_data_dir / "databases"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    """Create temporary database for isolated testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def database_manager(temp_db: str) -> DatabaseManager:
    """Create DatabaseManager with temporary database."""
    db_manager = DatabaseManager(temp_db)
    db_manager.initialize_schema()
    return db_manager


@pytest.fixture
def sample_customer() -> Customer:
    """Create a sample customer for testing."""
    return Customer(
        customer_id="TEST_001",
        first_name="John",
        last_name="Doe", 
        email="john.doe@test.com",
        phone="555-012-3456",
        date_of_birth="1985-01-15",
        address="123 Test Street",
        city="Test City",
        state="TS",
        zip_code="12345",
        household_size=3,
        num_adults=2,
        num_children=1,
        num_pets=0,
        household_income=75000.0,
        employment_status="employed",
        marital_status="married"
    )


@pytest.fixture
def sample_account(sample_customer: Customer) -> Account:
    """Create a sample account for testing."""
    return Account(
        account_id="ACC_001",
        customer_id=sample_customer.customer_id,
        account_number="1234567890",
        account_type=AccountType.CHECKING,
        balance=Decimal('1474.50'),  # Match the balance_after in sample transaction
        available_balance=Decimal('1474.50'),
        currency="USD",
        is_active=True
    )


@pytest.fixture
def sample_transaction(sample_account: Account) -> Transaction:
    """Create a sample transaction for testing."""
    return Transaction(
        transaction_id="TXN_001",
        account_id=sample_account.account_id,
        transaction_type=TransactionType.DEBIT,
        amount=-25.50,
        currency="USD",
        description="Coffee Shop Purchase",
        category="dining",
        merchant_name="Test Coffee Co",
        merchant_category="restaurants",
        transaction_date="2024-01-15 09:30:00",
        posted_date="2024-01-15 09:30:00",
        reference_number="REF123456",
        balance_after=1474.50
    )


@pytest.fixture
def customer_generator() -> CustomerGenerator:
    """Create CustomerGenerator with fixed seed for testing."""
    return CustomerGenerator(seed=12345)


@pytest.fixture
def configuration_parser() -> ConfigurationParser:
    """Create ConfigurationParser for testing."""
    return ConfigurationParser()


@pytest.fixture
def populated_database(database_manager: DatabaseManager, 
                      sample_customer: Customer,
                      sample_account: Account, 
                      sample_transaction: Transaction) -> DatabaseManager:
    """Create database populated with test data."""
    # Insert test data (methods take lists)
    database_manager.insert_customers([sample_customer])
    database_manager.insert_accounts([sample_account])
    database_manager.insert_transactions([sample_transaction])
    
    return database_manager


@pytest.fixture
def sample_config_json() -> Dict[str, Any]:
    """Sample configuration JSON for testing."""
    return {
        "metadata": {
            "source_text": "Generate monthly salary deposits of $3000",
            "created_at": "2024-01-01T00:00:00Z",
            "version": "1.0"
        },
        "transaction_patterns": [{
            "pattern_id": "salary_001", 
            "name": "Monthly Salary",
            "type": "income",
            "category": "salary",
            "amount": {
                "type": "fixed",
                "value": 3000.0,
                "currency": "USD"
            },
            "schedule": {
                "frequency": "monthly",
                "day_of_month": [15]
            }
        }],
        "generation": {
            "seed": 12345,
            "deterministic": True
        }
    }


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment and cleanup."""
    # Setup
    test_exports_dir = Path("test_exports")
    test_exports_dir.mkdir(exist_ok=True)
    
    yield
    
    # Cleanup
    import shutil
    if test_exports_dir.exists():
        shutil.rmtree(test_exports_dir)


# Test categories for pytest markers
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "web: Web interface tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow-running tests")
    config.addinivalue_line("markers", "banking: Banking domain tests")