"""
Tests for Strategy Pattern Implementation.

This module tests the profile building strategies that implement the Gang of Four
Strategy pattern for different profile building approaches.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch
from typing import Dict, Any

from src.syfi.patterns.strategies import (
    ProfileBuildingStrategy,
    StandardFamilyStrategy,
    SinglePersonStrategy, 
    StudentStrategy,
    RetirementStrategy,
    BusinessStrategy,
    ProfileBuildingContext,
    StrategyFactory
)
from src.syfi.models import Profile, ProfileTemplate


@pytest.mark.unit
class TestProfileBuildingStrategy:
    """Test abstract ProfileBuildingStrategy interface."""
    
    def test_strategy_cannot_be_instantiated(self):
        """Test that abstract ProfileBuildingStrategy cannot be directly instantiated."""
        with pytest.raises(TypeError):
            ProfileBuildingStrategy()


@pytest.mark.unit
class TestStandardFamilyStrategy:
    """Test StandardFamilyStrategy implementation."""
    
    @pytest.fixture
    def strategy(self):
        """Create a StandardFamilyStrategy instance."""
        return StandardFamilyStrategy()
    
    @pytest.fixture
    def sample_template(self):
        """Create a sample ProfileTemplate for testing."""
        return ProfileTemplate(
            template_id="family_template_001",
            name="Standard Family Template",
            description="Template for standard family profiles",
            household_type="family"
        )
    
    def test_strategy_initialization(self, strategy):
        """Test strategy initialization."""
        assert isinstance(strategy, ProfileBuildingStrategy)
        assert strategy is not None
    
    def test_get_strategy_name(self, strategy):
        """Test getting strategy name."""
        name = strategy.get_strategy_name()
        assert isinstance(name, str)
        assert "family" in name.lower()
    
    @patch('src.syfi.patterns.strategies.random')
    def test_build_profile_basic(self, mock_random, strategy, sample_template):
        """Test basic profile building."""
        # Setup random mocks
        mock_random.seed.return_value = None
        mock_random.choice.return_value = 4
        mock_random.randint.return_value = 100000
        
        profile = strategy.build_profile(sample_template, "Test Family", seed=12345)
        
        assert isinstance(profile, Profile)
        assert profile.name == "Test Family"
        assert profile.template_id == "family_template_001"
        assert profile.household_type == "family"
        assert profile.generation_seed == 12345
        mock_random.seed.assert_called_once_with(12345)
    
    @patch('src.syfi.patterns.strategies.random')
    def test_build_profile_with_custom_params(self, mock_random, strategy, sample_template):
        """Test profile building with custom parameters."""
        mock_random.seed.return_value = None
        mock_random.choice.return_value = 3
        mock_random.randint.return_value = 85000
        
        profile = strategy.build_profile(
            sample_template, 
            "Custom Family",
            seed=54321,
            description="Custom description",
            household_type="extended_family",
            total_members=5,
            banking_members=3,
            household_income=Decimal('120000')
        )
        
        assert profile.name == "Custom Family"
        assert profile.description == "Custom description"
        assert profile.household_type == "extended_family"
        assert profile.total_members == 5
        assert profile.banking_members == 3
        assert profile.household_income == Decimal('120000')
        assert profile.generation_seed == 54321
    
    @patch('src.syfi.patterns.strategies.random')
    def test_build_profile_default_description(self, mock_random, strategy, sample_template):
        """Test profile building with default description."""
        mock_random.seed.return_value = None
        mock_random.choice.return_value = 4
        mock_random.randint.return_value = 100000
        
        profile = strategy.build_profile(sample_template, "Test Family", seed=12345)
        
        assert "Standard Family Template" in profile.description
    
    @patch('src.syfi.patterns.strategies.random')
    def test_family_specific_data_added(self, mock_random, strategy, sample_template):
        """Test that family-specific data is added to profile."""
        mock_random.seed.return_value = None
        mock_random.choice.return_value = 4
        mock_random.randint.return_value = 100000
        
        # Mock the _add_family_data method to verify it's called
        with patch.object(strategy, '_add_family_data') as mock_add_data:
            profile = strategy.build_profile(sample_template, "Test Family", seed=12345)
            
            mock_add_data.assert_called_once_with(profile, sample_template, 12345)


@pytest.mark.unit
class TestSinglePersonStrategy:
    """Test SinglePersonStrategy implementation."""
    
    def test_single_person_strategy_exists(self):
        """Test that SinglePersonStrategy can be imported."""
        try:
            from src.syfi.patterns.strategies import SinglePersonStrategy
            strategy = SinglePersonStrategy()
            assert isinstance(strategy, ProfileBuildingStrategy)
        except ImportError:
            pytest.skip("SinglePersonStrategy not implemented yet")
    
    def test_single_person_strategy_name(self):
        """Test single person strategy name."""
        try:
            from src.syfi.patterns.strategies import SinglePersonStrategy
            strategy = SinglePersonStrategy()
            name = strategy.get_strategy_name()
            assert "single" in name.lower() or "person" in name.lower()
        except ImportError:
            pytest.skip("SinglePersonStrategy not implemented yet")


@pytest.mark.unit
class TestStudentStrategy:
    """Test StudentStrategy implementation."""
    
    def test_student_strategy_exists(self):
        """Test that StudentStrategy can be imported."""
        try:
            from src.syfi.patterns.strategies import StudentStrategy
            strategy = StudentStrategy()
            assert isinstance(strategy, ProfileBuildingStrategy)
        except ImportError:
            pytest.skip("StudentStrategy not implemented yet")


@pytest.mark.unit
class TestRetirementStrategy:
    """Test RetirementStrategy implementation."""
    
    def test_retirement_strategy_exists(self):
        """Test that RetirementStrategy can be imported."""
        try:
            from src.syfi.patterns.strategies import RetirementStrategy
            strategy = RetirementStrategy()
            assert isinstance(strategy, ProfileBuildingStrategy)
        except ImportError:
            pytest.skip("RetirementStrategy not implemented yet")


@pytest.mark.unit
class TestBusinessStrategy:
    """Test BusinessStrategy implementation."""
    
    def test_business_strategy_exists(self):
        """Test that BusinessStrategy can be imported."""
        try:
            from src.syfi.patterns.strategies import BusinessStrategy
            strategy = BusinessStrategy()
            assert isinstance(strategy, ProfileBuildingStrategy)
        except ImportError:
            pytest.skip("BusinessStrategy not implemented yet")


@pytest.mark.unit
class TestProfileBuildingContext:
    """Test ProfileBuildingContext class."""
    
    @pytest.fixture
    def mock_strategy(self):
        """Create a mock strategy."""
        strategy = Mock(spec=ProfileBuildingStrategy)
        strategy.get_strategy_name.return_value = "Mock Strategy"
        strategy.build_profile.return_value = Mock(spec=Profile)
        return strategy
    
    @pytest.fixture
    def context(self, mock_strategy):
        """Create a ProfileBuildingContext with mock strategy."""
        return ProfileBuildingContext(mock_strategy)
    
    def test_context_initialization(self, context, mock_strategy):
        """Test context initialization."""
        assert context.strategy is mock_strategy
    
    def test_set_strategy(self, context):
        """Test setting a new strategy."""
        new_strategy = Mock(spec=ProfileBuildingStrategy)
        
        context.set_strategy(new_strategy)
        
        assert context.strategy is new_strategy
    
    def test_build_profile_delegates_to_strategy(self, context, mock_strategy):
        """Test that build_profile delegates to the strategy."""
        mock_template = Mock(spec=ProfileTemplate)
        
        result = context.build_profile(mock_template, "Test Profile", seed=12345)
        
        mock_strategy.build_profile.assert_called_once_with(
            mock_template, "Test Profile", 12345
        )
        assert result is mock_strategy.build_profile.return_value
    
    def test_build_profile_with_kwargs(self, context, mock_strategy):
        """Test build_profile with additional kwargs."""
        mock_template = Mock(spec=ProfileTemplate)
        
        context.build_profile(
            mock_template, 
            "Test Profile", 
            seed=12345,
            custom_param="value",
            another_param=42
        )
        
        mock_strategy.build_profile.assert_called_once_with(
            mock_template, "Test Profile", 12345, custom_param="value", another_param=42
        )
    
    def test_get_current_strategy_name(self, context, mock_strategy):
        """Test getting current strategy name."""
        name = context.get_current_strategy_name()
        
        assert name == "Mock Strategy"
        mock_strategy.get_strategy_name.assert_called_once()


@pytest.mark.unit
class TestStrategyFactory:
    """Test StrategyFactory for creating appropriate strategies."""
    
    def test_factory_exists(self):
        """Test that StrategyFactory can be imported."""
        try:
            from src.syfi.patterns.strategies import StrategyFactory
            factory = StrategyFactory()
            assert factory is not None
        except ImportError:
            pytest.skip("StrategyFactory not implemented yet")
    
    def test_create_strategy_by_type(self):
        """Test creating strategy by type."""
        try:
            from src.syfi.patterns.strategies import StrategyFactory
            
            factory = StrategyFactory()
            
            # Test family strategy creation
            family_strategy = factory.create_strategy("family")
            assert isinstance(family_strategy, ProfileBuildingStrategy)
            
            # Test single person strategy creation  
            single_strategy = factory.create_strategy("single")
            assert isinstance(single_strategy, ProfileBuildingStrategy)
            
        except ImportError:
            pytest.skip("StrategyFactory not fully implemented yet")
    
    def test_create_strategy_invalid_type(self):
        """Test creating strategy with invalid type."""
        try:
            from src.syfi.patterns.strategies import StrategyFactory
            
            factory = StrategyFactory()
            
            with pytest.raises(ValueError, match="Unknown strategy type"):
                factory.create_strategy("nonexistent")
                
        except ImportError:
            pytest.skip("StrategyFactory not fully implemented yet")
    
    def test_get_available_strategies(self):
        """Test getting list of available strategies."""
        try:
            from src.syfi.patterns.strategies import StrategyFactory
            
            factory = StrategyFactory()
            strategies = factory.get_available_strategies()
            
            assert isinstance(strategies, list)
            assert len(strategies) > 0
            assert "family" in strategies
            
        except ImportError:
            pytest.skip("StrategyFactory not fully implemented yet")


@pytest.mark.unit
class TestStrategyComparison:
    """Test comparing different strategies."""
    
    @pytest.fixture
    def sample_template(self):
        """Create a sample template for testing."""
        return ProfileTemplate(
            template_id="test_template",
            name="Test Template",
            description="Template for testing",
            household_type="family"
        )
    
    def test_different_strategies_produce_different_profiles(self, sample_template):
        """Test that different strategies produce different profile characteristics."""
        try:
            family_strategy = StandardFamilyStrategy()
            
            # Would compare with other strategies when implemented
            family_profile = family_strategy.build_profile(sample_template, "Test", seed=12345)
            
            assert family_profile.household_type == "family"
            # More specific comparisons would be added when other strategies exist
            
        except ImportError:
            pytest.skip("Multiple strategies not available for comparison")


@pytest.mark.integration
class TestStrategyIntegration:
    """Integration tests for strategy pattern."""
    
    def test_strategy_context_switching(self):
        """Test switching strategies in context."""
        try:
            from src.syfi.patterns.strategies import (
                ProfileBuildingContext, 
                StandardFamilyStrategy,
                SinglePersonStrategy
            )
            
            # Create context with family strategy
            context = ProfileBuildingContext(StandardFamilyStrategy())
            
            # Switch to single person strategy
            context.set_strategy(SinglePersonStrategy())
            
            # Verify strategy changed
            assert "single" in context.get_current_strategy_name().lower()
            
        except ImportError:
            pytest.skip("Multiple strategies not available for integration test")
    
    def test_strategy_with_real_profile_template(self):
        """Test strategy with real ProfileTemplate."""
        template = ProfileTemplate(
            template_id="integration_test",
            name="Integration Test Template", 
            description="Template for integration testing",
            household_type="family"
        )
        
        strategy = StandardFamilyStrategy()
        profile = strategy.build_profile(template, "Integration Test Profile", seed=99999)
        
        # Verify profile was created correctly
        assert profile.name == "Integration Test Profile"
        assert profile.template_id == "integration_test"
        assert profile.generation_seed == 99999
        assert isinstance(profile.household_income, Decimal)
        assert profile.total_members > 0
        assert profile.banking_members > 0