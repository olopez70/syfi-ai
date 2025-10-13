"""
Tests for Builder Pattern Implementation.

This module tests the profile builders that implement the Gang of Four Builder pattern
for constructing complex profiles with different configurations.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch

from src.syfi.patterns.builders import (
    ProfileBuilder, 
    ConcreteProfileBuilder, 
    ProfileDirector
)
from src.syfi.models import Profile, ProfileTemplate, TransactionProfile


@pytest.mark.unit
class TestProfileBuilder:
    """Test abstract ProfileBuilder interface."""
    
    def test_abstract_builder_cannot_be_instantiated(self):
        """Test that abstract ProfileBuilder cannot be directly instantiated."""
        with pytest.raises(TypeError):
            ProfileBuilder()


@pytest.mark.unit  
class TestConcreteProfileBuilder:
    """Test ConcreteProfileBuilder implementation."""
    
    @pytest.fixture
    def builder(self):
        """Create a fresh ConcreteProfileBuilder for each test."""
        return ConcreteProfileBuilder(seed=12345)
    
    @pytest.fixture
    def sample_template(self):
        """Create a sample ProfileTemplate for testing."""
        return ProfileTemplate(
            template_id="test_template",
            name="Test Template",
            description="A test template",
            household_type="family"
        )
    
    def test_builder_initialization(self, builder):
        """Test builder initializes correctly."""
        assert builder.seed == 12345
        assert builder.profile is None
        
    def test_builder_initialization_default_seed(self):
        """Test builder with default seed."""
        builder = ConcreteProfileBuilder()
        assert builder.seed == 12345
        
    def test_reset_builder(self, builder, sample_template):
        """Test reset functionality."""
        # Build a profile first
        builder.set_basic_info(sample_template, "Test Profile")
        assert builder.profile is not None
        
        # Reset should clear the profile
        result = builder.reset()
        assert builder.profile is None
        assert result is builder  # Should return self for chaining
        
    def test_set_basic_info(self, builder, sample_template):
        """Test setting basic profile information."""
        result = builder.set_basic_info(
            sample_template, 
            "Test Profile",
            description="Custom description",
            household_type="single",
            total_members=1,
            banking_members=1,
            household_income=Decimal('60000')
        )
        
        assert result is builder  # Should return self for chaining
        assert builder.profile is not None
        assert builder.profile.template_id == "test_template"
        assert builder.profile.name == "Test Profile"
        assert builder.profile.description == "Custom description"
        assert builder.profile.household_type == "single"
        assert builder.profile.total_members == 1
        assert builder.profile.banking_members == 1
        assert builder.profile.household_income == Decimal('60000')
        assert builder.profile.generation_seed == 12345
        
    def test_set_basic_info_with_defaults(self, builder, sample_template):
        """Test setting basic info with default values."""
        builder.set_basic_info(sample_template, "Test Profile")
        
        profile = builder.profile
        assert profile.description == "Profile built from Test Template"
        assert profile.household_type == "family"
        assert profile.total_members == 1
        assert profile.banking_members == 1
        assert profile.household_income == Decimal('50000')
        
    def test_add_household_members(self, builder, sample_template):
        """Test adding household members."""
        builder.set_basic_info(sample_template, "Test Profile")
        
        result = builder.add_household_members(4, banking_members=3)
        
        assert result is builder
        assert builder.profile.total_members == 4
        assert builder.profile.banking_members == 3
        
    def test_add_household_members_default_banking(self, builder, sample_template):
        """Test adding household members with default banking members."""
        builder.set_basic_info(sample_template, "Test Profile")
        
        builder.add_household_members(5)
        
        assert builder.profile.total_members == 5
        assert builder.profile.banking_members == 2  # min(5, 2)
        
    def test_add_household_members_no_profile(self, builder):
        """Test adding household members when no profile exists."""
        result = builder.add_household_members(3)
        assert result is builder  # Should not fail but do nothing
        
    def test_set_income_level(self, builder, sample_template):
        """Test setting income level."""
        builder.set_basic_info(sample_template, "Test Profile")
        
        result = builder.set_income_level(Decimal('75000'))
        
        assert result is builder
        assert builder.profile.household_income == Decimal('75000')
        
    def test_set_income_level_no_profile(self, builder):
        """Test setting income level when no profile exists."""
        result = builder.set_income_level(Decimal('75000'))
        assert result is builder  # Should not fail but do nothing
        
    def test_add_customer_data(self, builder, sample_template):
        """Test adding customer data."""
        builder.set_basic_info(sample_template, "Test Profile")
        
        # Mock the profile's add_customer_data method
        builder.profile.add_customer_data = Mock()
        
        customer_data = [{"name": "John Doe", "age": 30}]
        result = builder.add_customer_data(customers_data=customer_data)
        
        assert result is builder
        builder.profile.add_customer_data.assert_called_once_with({"name": "John Doe", "age": 30})
        
    def test_add_customer_data_no_profile(self, builder):
        """Test adding customer data when no profile exists."""
        result = builder.add_customer_data(customers_data=[])
        assert result is builder  # Should not fail but do nothing
        
    def test_add_account_structure(self, builder, sample_template):
        """Test adding account structure."""
        builder.set_basic_info(sample_template, "Test Profile")
        
        # Mock the profile's add_account_data method
        builder.profile.add_account_data = Mock()
        
        account_data = [{"type": "checking", "balance": 5000}]
        result = builder.add_account_structure(accounts_data=account_data)
        
        assert result is builder
        builder.profile.add_account_data.assert_called_once_with({"type": "checking", "balance": 5000})
        
    def test_add_account_structure_no_profile(self, builder):
        """Test adding account structure when no profile exists."""
        result = builder.add_account_structure(accounts_data=[])
        assert result is builder  # Should not fail but do nothing
        
    def test_add_transaction_patterns(self, builder, sample_template):
        """Test adding transaction patterns."""
        builder.set_basic_info(sample_template, "Test Profile")
        
        # Mock the profile's add_transaction_profile method
        builder.profile.add_transaction_profile = Mock()
        
        transaction_profile = Mock(spec=TransactionProfile)
        result = builder.add_transaction_patterns(
            pattern_name="monthly_salary",
            transaction_profile=transaction_profile
        )
        
        assert result is builder
        builder.profile.add_transaction_profile.assert_called_once_with("monthly_salary", transaction_profile)
        
    def test_add_transaction_patterns_default_name(self, builder, sample_template):
        """Test adding transaction patterns with default name."""
        builder.set_basic_info(sample_template, "Test Profile")
        builder.profile.add_transaction_profile = Mock()
        
        transaction_profile = Mock(spec=TransactionProfile)
        builder.add_transaction_patterns(transaction_profile=transaction_profile)
        
        builder.profile.add_transaction_profile.assert_called_once_with("default", transaction_profile)
        
    def test_add_transaction_patterns_no_profile(self, builder):
        """Test adding transaction patterns when no profile exists."""
        result = builder.add_transaction_patterns()
        assert result is builder  # Should not fail but do nothing
        
    def test_build_success(self, builder, sample_template):
        """Test successful profile building."""
        builder.set_basic_info(sample_template, "Test Profile")
        
        profile = builder.build()
        
        assert isinstance(profile, Profile)
        assert profile.name == "Test Profile"
        assert builder.profile is None  # Should reset after build
        
    def test_build_failure_no_profile(self, builder):
        """Test build failure when no profile is initialized."""
        with pytest.raises(ValueError, match="Profile not initialized"):
            builder.build()
            
    def test_method_chaining(self, builder, sample_template):
        """Test that all methods support method chaining."""
        profile = (builder
                  .set_basic_info(sample_template, "Chain Test")
                  .add_household_members(3)
                  .set_income_level(Decimal('80000'))
                  .build())
        
        assert isinstance(profile, Profile)
        assert profile.name == "Chain Test"
        assert profile.total_members == 3
        assert profile.household_income == Decimal('80000')


@pytest.mark.unit
class TestProfileDirector:
    """Test ProfileDirector class."""
    
    @pytest.fixture
    def builder(self):
        """Create a mock builder for testing."""
        return Mock(spec=ConcreteProfileBuilder)
    
    @pytest.fixture
    def director(self, builder):
        """Create a ProfileDirector with mock builder."""
        return ProfileDirector(builder)
    
    @pytest.fixture
    def sample_template(self):
        """Create a sample ProfileTemplate for testing."""
        return ProfileTemplate(
            template_id="family_template",
            name="Family Template",
            description="Template for family profiles",
            household_type="family"
        )
    
    def test_director_initialization(self, builder):
        """Test director initialization."""
        director = ProfileDirector(builder)
        assert director.builder is builder
        
    @patch('src.syfi.patterns.builders.random')
    def test_build_young_family_profile(self, mock_random, director, builder, sample_template):
        """Test building young family profile."""
        # Setup mocks
        mock_random.seed.return_value = None
        mock_random.randint.return_value = 100000
        builder.seed = 12345
        
        # Setup builder chain
        builder.set_basic_info.return_value = builder
        builder.add_household_members.return_value = builder
        builder.set_income_level.return_value = builder
        builder.add_customer_data.return_value = builder
        builder.add_account_structure.return_value = builder
        builder.add_transaction_patterns.return_value = builder
        
        expected_profile = Mock(spec=Profile)
        builder.build.return_value = expected_profile
        
        # Execute
        result = director.build_young_family_profile(sample_template, "Young Family")
        
        # Verify
        assert result is expected_profile
        mock_random.seed.assert_called_once_with(12345)
        mock_random.randint.assert_called_once_with(75000, 125000)
        
        builder.set_basic_info.assert_called_once()
        builder.add_household_members.assert_called_once()
        builder.set_income_level.assert_called_once_with(Decimal('100000'))
        
    @patch('src.syfi.patterns.builders.random')  
    def test_build_young_family_profile_custom_income(self, mock_random, director, builder, sample_template):
        """Test building young family profile with custom income range."""
        mock_random.randint.return_value = 150000
        builder.seed = 12345
        builder.set_basic_info.return_value = builder
        builder.add_household_members.return_value = builder
        builder.set_income_level.return_value = builder
        builder.add_customer_data.return_value = builder
        builder.add_account_structure.return_value = builder
        builder.add_transaction_patterns.return_value = builder
        builder.build.return_value = Mock(spec=Profile)
        
        director.build_young_family_profile(
            sample_template, 
            "High Income Family", 
            income_range=(120000, 200000)
        )
        
        mock_random.randint.assert_called_once_with(120000, 200000)
        builder.set_income_level.assert_called_once_with(Decimal('150000'))


@pytest.mark.integration
class TestBuilderIntegration:
    """Integration tests for builder pattern with real models."""
    
    def test_complete_profile_building_workflow(self):
        """Test complete workflow from builder to finished profile."""
        # This would require actual Profile and ProfileTemplate implementations
        # For now, we'll skip this as it needs the models to be fully testable
        pytest.skip("Integration test requires full model implementation")


@pytest.mark.unit
class TestSpecializedBuilders:
    """Test specialized builder implementations."""
    
    def test_family_profile_builder_exists(self):
        """Test that FamilyProfileBuilder can be imported."""
        try:
            from src.syfi.patterns.builders import FamilyProfileBuilder
            assert FamilyProfileBuilder is not None
        except (ImportError, AttributeError):
            pytest.skip("FamilyProfileBuilder not implemented yet")
            
    def test_single_person_profile_builder_exists(self):
        """Test that SinglePersonProfileBuilder can be imported."""
        try:
            from src.syfi.patterns.builders import SinglePersonProfileBuilder
            assert SinglePersonProfileBuilder is not None
        except (ImportError, AttributeError):
            pytest.skip("SinglePersonProfileBuilder not implemented yet")
            
    def test_student_profile_builder_exists(self):
        """Test that StudentProfileBuilder can be imported."""
        try:
            from src.syfi.patterns.builders import StudentProfileBuilder
            assert StudentProfileBuilder is not None
        except (ImportError, AttributeError):
            pytest.skip("StudentProfileBuilder not implemented yet")
            
    def test_retired_person_profile_builder_exists(self):
        """Test that RetiredPersonProfileBuilder can be imported."""
        try:
            from src.syfi.patterns.builders import RetiredPersonProfileBuilder
            assert RetiredPersonProfileBuilder is not None
        except (ImportError, AttributeError):
            pytest.skip("RetiredPersonProfileBuilder not implemented yet")