"""
Tests for Repository Pattern Implementation.

This module tests the repository pattern that provides an abstraction layer 
over data persistence with different implementations.
"""

import pytest
from unittest.mock import Mock, patch
from typing import List, Optional
from decimal import Decimal
from datetime import date

from src.syfi.patterns.repositories import (
    CustomerRepository,
    AccountRepository, 
    TransactionRepository,
    ProfileRepository,
    DatabaseCustomerRepository,
    DatabaseAccountRepository,
    DatabaseTransactionRepository,
    InMemoryCustomerRepository,
    InMemoryAccountRepository,
    CacheableCustomerRepository,
    RepositoryFactory
)
from src.syfi.models import Customer, Account, Transaction, Profile, ProfileTemplate
from src.syfi.models import AccountType, TransactionType


@pytest.mark.unit
class TestAbstractRepositories:
    """Test abstract repository interfaces."""
    
    def test_customer_repository_abstract(self):
        """Test that CustomerRepository cannot be instantiated."""
        with pytest.raises(TypeError):
            CustomerRepository()
    
    def test_account_repository_abstract(self):
        """Test that AccountRepository cannot be instantiated."""
        with pytest.raises(TypeError):
            AccountRepository()
    
    def test_transaction_repository_abstract(self):
        """Test that TransactionRepository cannot be instantiated."""
        with pytest.raises(TypeError):
            TransactionRepository()
    
    def test_profile_repository_abstract(self):
        """Test that ProfileRepository cannot be instantiated."""
        with pytest.raises(TypeError):
            ProfileRepository()


@pytest.mark.unit
class TestInMemoryCustomerRepository:
    """Test InMemoryCustomerRepository implementation."""
    
    @pytest.fixture
    def repository(self):
        """Create a fresh InMemoryCustomerRepository."""
        return InMemoryCustomerRepository()
    
    @pytest.fixture
    def sample_customer(self):
        """Create a sample customer for testing."""
        return Customer(
            customer_id="test_123",
            first_name="John",
            last_name="Doe",
            age=30,
            income=Decimal('50000'),
            email="john.doe@example.com"
        )
    
    def test_repository_initialization(self, repository):
        """Test repository initialization."""
        assert len(repository._customers) == 0
        assert repository._next_id == 1
    
    def test_save_customer(self, repository, sample_customer):
        """Test saving a customer."""
        customer_id = repository.save(sample_customer)
        
        assert customer_id is not None
        assert len(repository._customers) == 1
        assert customer_id in repository._customers
    
    def test_save_customer_generates_id_if_none(self, repository):
        """Test that save generates ID if customer has none."""
        customer = Customer(
            first_name="Jane",
            last_name="Smith", 
            age=25,
            income=Decimal('40000')
        )
        customer.customer_id = None
        
        customer_id = repository.save(customer)
        
        assert customer_id is not None
        assert customer.customer_id == customer_id
    
    def test_save_batch(self, repository):
        """Test saving multiple customers."""
        customers = [
            Customer(first_name="John", last_name="Doe", age=30, income=Decimal('50000')),
            Customer(first_name="Jane", last_name="Smith", age=25, income=Decimal('40000'))
        ]
        
        customer_ids = repository.save_batch(customers)
        
        assert len(customer_ids) == 2
        assert len(repository._customers) == 2
        for customer_id in customer_ids:
            assert customer_id in repository._customers
    
    def test_find_by_id(self, repository, sample_customer):
        """Test finding customer by ID."""
        customer_id = repository.save(sample_customer)
        
        found_customer = repository.find_by_id(customer_id)
        
        assert found_customer is not None
        assert found_customer.customer_id == customer_id
        assert found_customer.first_name == "John"
    
    def test_find_by_id_not_found(self, repository):
        """Test finding non-existent customer."""
        found_customer = repository.find_by_id("nonexistent")
        
        assert found_customer is None
    
    def test_find_all(self, repository):
        """Test finding all customers."""
        customers = [
            Customer(first_name="John", last_name="Doe", age=30, income=Decimal('50000')),
            Customer(first_name="Jane", last_name="Smith", age=25, income=Decimal('40000'))
        ]
        
        repository.save_batch(customers)
        
        all_customers = repository.find_all()
        
        assert len(all_customers) == 2
    
    def test_find_by_income_range(self, repository):
        """Test finding customers by income range."""
        customers = [
            Customer(first_name="Low", last_name="Income", age=30, income=Decimal('30000')),
            Customer(first_name="Mid", last_name="Income", age=35, income=Decimal('50000')),
            Customer(first_name="High", last_name="Income", age=40, income=Decimal('80000'))
        ]
        
        repository.save_batch(customers)
        
        mid_income_customers = repository.find_by_income_range(40000, 70000)
        
        assert len(mid_income_customers) == 1
        assert mid_income_customers[0].first_name == "Mid"
    
    def test_count(self, repository):
        """Test counting customers."""
        assert repository.count() == 0
        
        customers = [
            Customer(first_name="John", last_name="Doe", age=30, income=Decimal('50000')),
            Customer(first_name="Jane", last_name="Smith", age=25, income=Decimal('40000'))
        ]
        
        repository.save_batch(customers)
        
        assert repository.count() == 2


@pytest.mark.unit
class TestDatabaseCustomerRepository:
    """Test DatabaseCustomerRepository implementation."""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock database manager."""
        return Mock()
    
    @pytest.fixture
    def repository(self, mock_db_manager):
        """Create a DatabaseCustomerRepository with mock db."""
        return DatabaseCustomerRepository(mock_db_manager)
    
    @pytest.fixture
    def sample_customer(self):
        """Create a sample customer for testing."""
        return Customer(
            first_name="John",
            last_name="Doe", 
            age=30,
            income=Decimal('50000')
        )
    
    def test_repository_initialization(self, repository, mock_db_manager):
        """Test repository initialization."""
        assert repository.db_manager is mock_db_manager
    
    def test_save_customer(self, repository, mock_db_manager, sample_customer):
        """Test saving customer to database."""
        mock_db_manager.insert_customer.return_value = "db_generated_id"
        
        customer_id = repository.save(sample_customer)
        
        assert customer_id == "db_generated_id"
        mock_db_manager.insert_customer.assert_called_once_with(sample_customer)
    
    def test_save_batch(self, repository, mock_db_manager):
        """Test batch saving customers."""
        customers = [Mock(spec=Customer), Mock(spec=Customer)]
        mock_db_manager.insert_customers_batch.return_value = ["id1", "id2"]
        
        customer_ids = repository.save_batch(customers)
        
        assert customer_ids == ["id1", "id2"]
        mock_db_manager.insert_customers_batch.assert_called_once_with(customers)
    
    def test_find_by_id(self, repository, mock_db_manager):
        """Test finding customer by ID from database."""
        mock_customer = Mock(spec=Customer)
        mock_db_manager.get_customer_by_id.return_value = mock_customer
        
        result = repository.find_by_id("test_id")
        
        assert result is mock_customer
        mock_db_manager.get_customer_by_id.assert_called_once_with("test_id")
    
    def test_find_all(self, repository, mock_db_manager):
        """Test finding all customers from database."""
        mock_customers = [Mock(spec=Customer), Mock(spec=Customer)]
        mock_db_manager.get_all_customers.return_value = mock_customers
        
        result = repository.find_all()
        
        assert result is mock_customers
        mock_db_manager.get_all_customers.assert_called_once()
    
    def test_find_by_income_range(self, repository, mock_db_manager):
        """Test finding customers by income range."""
        mock_customers = [Mock(spec=Customer)]
        mock_db_manager.get_customers_by_income_range.return_value = mock_customers
        
        result = repository.find_by_income_range(40000, 60000)
        
        assert result is mock_customers
        mock_db_manager.get_customers_by_income_range.assert_called_once_with(40000, 60000)


@pytest.mark.unit
class TestCacheableCustomerRepository:
    """Test CacheableCustomerRepository decorator implementation."""
    
    @pytest.fixture
    def base_repository(self):
        """Create a mock base repository."""
        return Mock(spec=CustomerRepository)
    
    @pytest.fixture
    def repository(self, base_repository):
        """Create a CacheableCustomerRepository."""
        return CacheableCustomerRepository(base_repository)
    
    def test_cacheable_repository_initialization(self, repository, base_repository):
        """Test cacheable repository initialization."""
        assert repository.base_repository is base_repository
        assert len(repository._cache) == 0
    
    def test_find_by_id_caches_result(self, repository, base_repository):
        """Test that find_by_id caches the result."""
        mock_customer = Mock(spec=Customer)
        mock_customer.customer_id = "test_id"
        base_repository.find_by_id.return_value = mock_customer
        
        # First call should hit the base repository
        result1 = repository.find_by_id("test_id")
        assert result1 is mock_customer
        base_repository.find_by_id.assert_called_once_with("test_id")
        
        # Second call should use cache
        base_repository.reset_mock()
        result2 = repository.find_by_id("test_id")
        assert result2 is mock_customer
        base_repository.find_by_id.assert_not_called()  # Should not hit base repo
    
    def test_save_invalidates_cache(self, repository, base_repository):
        """Test that save invalidates cache."""
        # Set up cache
        mock_customer = Mock(spec=Customer)
        mock_customer.customer_id = "test_id"
        repository._cache["test_id"] = mock_customer
        
        # Save should invalidate cache
        new_customer = Mock(spec=Customer)
        base_repository.save.return_value = "new_id"
        
        repository.save(new_customer)
        
        # Cache should be cleared
        assert len(repository._cache) == 0
        base_repository.save.assert_called_once_with(new_customer)


@pytest.mark.unit
class TestInMemoryAccountRepository:
    """Test InMemoryAccountRepository implementation."""
    
    def test_account_repository_exists(self):
        """Test that InMemoryAccountRepository can be imported."""
        try:
            from src.syfi.patterns.repositories import InMemoryAccountRepository
            repo = InMemoryAccountRepository()
            assert repo is not None
        except ImportError:
            pytest.skip("InMemoryAccountRepository not implemented yet")


@pytest.mark.unit
class TestRepositoryFactory:
    """Test RepositoryFactory for creating appropriate repositories."""
    
    def test_factory_exists(self):
        """Test that RepositoryFactory can be imported."""
        try:
            from src.syfi.patterns.repositories import RepositoryFactory
            factory = RepositoryFactory()
            assert factory is not None
        except ImportError:
            pytest.skip("RepositoryFactory not implemented yet")
    
    def test_create_customer_repository(self):
        """Test creating customer repository through factory."""
        try:
            from src.syfi.patterns.repositories import RepositoryFactory
            
            factory = RepositoryFactory()
            
            # Test creating in-memory repository
            memory_repo = factory.create_customer_repository("memory")
            assert isinstance(memory_repo, CustomerRepository)
            
            # Test creating database repository
            db_repo = factory.create_customer_repository("database", db_manager=Mock())
            assert isinstance(db_repo, CustomerRepository)
            
        except ImportError:
            pytest.skip("RepositoryFactory not fully implemented yet")


@pytest.mark.integration
class TestRepositoryIntegration:
    """Integration tests for repository pattern."""
    
    def test_repository_consistency(self):
        """Test that different repository implementations behave consistently."""
        # Test that InMemory and Database repositories have same interface
        pytest.skip("Integration test requires full implementation")
    
    def test_repository_with_real_data(self):
        """Test repositories with real Customer objects."""
        repo = InMemoryCustomerRepository()
        
        # Create real customer
        customer = Customer(
            first_name="Integration",
            last_name="Test",
            age=25,
            income=Decimal('45000'),
            email="integration@test.com"
        )
        
        # Test full workflow
        customer_id = repo.save(customer)
        assert customer_id is not None
        
        found_customer = repo.find_by_id(customer_id)
        assert found_customer.first_name == "Integration"
        assert found_customer.income == Decimal('45000')
        
        all_customers = repo.find_all()
        assert len(all_customers) == 1
        
        income_filtered = repo.find_by_income_range(40000, 50000)
        assert len(income_filtered) == 1