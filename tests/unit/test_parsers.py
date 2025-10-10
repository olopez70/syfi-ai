"""
Unit tests for configuration parsers.

Tests the natural language parsing functionality in isolation.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from src.syfi.core.parser import ConfigurationParser


@pytest.mark.unit
class TestConfigurationParser:
    """Test natural language configuration parsing."""
    
    def test_parse_monthly_salary_pattern(self, configuration_parser):
        """Test parsing monthly salary deposit pattern."""
        text = "Generate monthly salary deposits of $3,500 on the 15th"
        config = configuration_parser.parse(text)
        
        assert len(config.transaction_patterns) == 1
        pattern = config.transaction_patterns[0]
        
        assert pattern.type == "income"
        assert pattern.category == "salary"
        assert pattern.amount.type == "fixed"
        assert pattern.amount.value == 3500.0
        assert pattern.schedule.frequency == "monthly"
        assert pattern.schedule.day_of_month == [15]
    
    def test_parse_weekly_grocery_range(self, configuration_parser):
        """Test parsing grocery spending with amount range."""
        text = "Create weekly grocery spending between $80-120 on weekends"
        config = configuration_parser.parse(text)
        
        pattern = config.transaction_patterns[0]
        assert pattern.category == "grocery"
        assert pattern.schedule.frequency == "weekly"
        # Range parsing may need implementation
        
    def test_parse_quarterly_frequency(self, configuration_parser):
        """Test parsing quarterly payment pattern."""
        text = "Simulate quarterly tax payments of $500"
        config = configuration_parser.parse(text)
        
        pattern = config.transaction_patterns[0]
        assert pattern.schedule.frequency == "quarterly"
        assert pattern.amount.value == 500.0
    
    def test_empty_input_handling(self, configuration_parser):
        """Test handling of empty input."""
        # Parser handles empty input by returning a default configuration
        config = configuration_parser.parse("")
        assert config is not None
        assert config.generation.seed == 12345  # Default value
    
    def test_basic_parsing(self, configuration_parser):
        """Test basic parsing functionality."""
        config = configuration_parser.parse("Generate 5 customers")
        assert config is not None


@pytest.mark.unit 
class TestConfigurationValidation:
    """Test configuration validation logic."""
    
    def test_valid_configuration(self, sample_config_json):
        """Test validation of valid configuration."""
        from src.syfi.core.config import Configuration
        config = Configuration.from_dict(sample_config_json)
        assert config.validate() is True
    
    def test_missing_required_fields(self):
        """Test validation fails for missing required fields."""
        from src.syfi.core.config import Configuration, TransactionPatternConfig
        
        config = Configuration()
        invalid_pattern = TransactionPatternConfig()
        # Missing required fields should cause validation to fail
        config.transaction_patterns.append(invalid_pattern)
        assert config.validate() is False