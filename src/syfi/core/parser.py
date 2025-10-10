"""
Natural Language Processing for SyFi AI Configuration Parser.

This module converts natural language descriptions of banking transaction
patterns into structured configuration files.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from .config import (
    Configuration, 
    TransactionPatternConfig, 
    AmountConfig, 
    ScheduleConfig, 
    MerchantConfig,
    AccountConfig,
    GenerationConfig
)

@dataclass
class ParsedEntity:
    """Represents a parsed entity from natural language text."""
    
    entity_type: str  # "amount", "frequency", "category", "time"
    value: Any
    confidence: float = 1.0
    source_text: str = ""

class ConfigurationParser:
    """
    Parses natural language descriptions and converts them to structured configurations.
    
    Example inputs:
    - "Generate monthly salary deposits of $3,500 on the 15th"
    - "Create weekly grocery spending between $80-120 on weekends"
    - "Simulate quarterly tax payments of 22% of income"
    """
    
    def __init__(self):
        """Initialize the parser with pattern matching rules."""
        self._initialize_patterns()
        self._initialize_categories()
    
    def _initialize_patterns(self):
        """Initialize regex patterns for entity extraction."""
        
        # Amount patterns
        self.amount_patterns = [
            r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',  # $1,234.56
            r'(\d+(?:,\d{3})*(?:\.\d{2})?) dollars?',  # 1234 dollars
            r'between \$(\d+(?:,\d{3})*(?:\.\d{2})?) (?:and|-) \$(\d+(?:,\d{3})*(?:\.\d{2})?)',  # between $80-120
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)% of (\w+)',  # 22% of income
        ]
        
        # Frequency patterns  
        self.frequency_patterns = [
            (r'\b(?:every\s+)?daily\b', 'daily'),
            (r'\b(?:every\s+)?weekly?\b', 'weekly'),
            (r'\b(?:every\s+)?monthly?\b', 'monthly'),
            (r'\b(?:every\s+)?quarterly?\b', 'quarterly'),
            (r'\b(?:every\s+)?yearly?\b|annually?', 'yearly'),
            (r'every\s+(\d+)\s+days?', 'daily'),
            (r'every\s+(\d+)\s+weeks?', 'weekly'),
            (r'every\s+(\d+)\s+months?', 'monthly'),
            (r'(\d+)\s+times?\s+(?:per\s+)?(?:week|weekly)', 'weekly'),
            (r'(\d+)\s+times?\s+(?:per\s+)?(?:month|monthly)', 'monthly'),
        ]
        
        # Time/schedule patterns
        self.time_patterns = [
            (r'on the (\d+)(?:st|nd|rd|th)?', 'day_of_month'),
            (r'on (monday|tuesday|wednesday|thursday|friday|saturday|sunday)s?', 'day_of_week'),
            (r'on (weekends?)', 'weekend'),
            (r'on (weekdays?)', 'weekday'),
            (r'during (business hours?)', 'business_hours'),
            (r'at (\d{1,2}):?(\d{2})?\s*(am|pm)?', 'time'),
            (r'between (\d{1,2}):?(\d{2})?\s*(am|pm)? and (\d{1,2}):?(\d{2})?\s*(am|pm)?', 'time_range'),
        ]
        
        # Category patterns
        self.category_patterns = [
            (r'\b(?:salary|paycheck|income|wages?|pay)\b', 'salary'),
            (r'\b(?:grocery|groceries|supermarket|food shopping)\b', 'grocery'),
            (r'\b(?:gas|fuel|gasoline|petrol)\b', 'gas'),
            (r'\b(?:utilities?|electric|electricity|water|internet|phone)\b', 'utilities'),
            (r'\b(?:entertainment|movies?|games?|streaming)\b', 'entertainment'),
            (r'\b(?:healthcare|medical|doctor|hospital|pharmacy)\b', 'healthcare'),
            (r'\b(?:shopping|retail|stores?|mall)\b', 'shopping'),
            (r'\b(?:restaurant|dining|food|eating out)\b', 'restaurant'),
            (r'\b(?:atm|cash|withdrawal)\b', 'atm'),
            (r'\b(?:tax|taxes|irs)\b', 'tax'),
            (r'\b(?:rent|mortgage|housing)\b', 'housing'),
        ]
        
        # Transaction type patterns
        self.transaction_type_patterns = [
            (r'\b(?:deposit|deposits?|income|receive|credit)\b', 'income'),
            (r'\b(?:payment|payments?|spending|expense|debit|withdraw)\b', 'expense'),
            (r'\b(?:transfer|transfers?|move money)\b', 'transfer'),
        ]
    
    def _initialize_categories(self):
        """Initialize category mappings."""
        self.category_mapping = {
            'salary': 'salary',
            'grocery': 'grocery', 
            'gas': 'gas',
            'utilities': 'utilities',
            'entertainment': 'entertainment',
            'healthcare': 'healthcare',
            'shopping': 'shopping',
            'restaurant': 'restaurant',
            'atm': 'atm',
            'tax': 'other',
            'housing': 'other'
        }
    
    def parse(self, text: str) -> Configuration:
        """
        Parse natural language text and return a Configuration object.
        
        Args:
            text: Natural language description of transaction pattern
            
        Returns:
            Configuration object with parsed transaction pattern
        """
        # Clean and normalize text
        text = self._normalize_text(text)
        
        # Extract entities
        entities = self._extract_entities(text)
        
        # Build configuration
        config = self._build_configuration(entities, text)
        
        return config
    
    def _normalize_text(self, text: str) -> str:
        """Normalize input text for better parsing."""
        # Convert to lowercase for pattern matching
        text = text.lower()
        
        # Replace common variations
        replacements = {
            'bi-weekly': 'every 2 weeks',
            'biweekly': 'every 2 weeks', 
            'semi-monthly': 'twice monthly',
            'semi-annually': 'every 6 months',
            'biannually': 'every 6 months',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def _extract_entities(self, text: str) -> List[ParsedEntity]:
        """Extract entities from normalized text."""
        entities = []
        
        # Extract amounts
        entities.extend(self._extract_amounts(text))
        
        # Extract frequency
        entities.extend(self._extract_frequency(text))
        
        # Extract time/schedule info
        entities.extend(self._extract_schedule(text))
        
        # Extract categories
        entities.extend(self._extract_categories(text))
        
        # Extract transaction types
        entities.extend(self._extract_transaction_types(text))
        
        return entities
    
    def _extract_amounts(self, text: str) -> List[ParsedEntity]:
        """Extract amount information from text."""
        entities = []
        
        # Check for range patterns first
        range_match = re.search(r'between \$(\d+(?:,\d{3})*(?:\.\d{2})?) (?:and|-) \$(\d+(?:,\d{3})*(?:\.\d{2})?)', text)
        if range_match:
            min_amount = float(range_match.group(1).replace(',', ''))
            max_amount = float(range_match.group(2).replace(',', ''))
            entities.append(ParsedEntity(
                entity_type="amount_range",
                value={"min": min_amount, "max": max_amount},
                source_text=range_match.group(0)
            ))
            return entities
        
        # Check for percentage patterns
        percent_match = re.search(r'(\d+(?:\.\d+)?)% of (\w+)', text)
        if percent_match:
            percentage = float(percent_match.group(1))
            base = percent_match.group(2)
            entities.append(ParsedEntity(
                entity_type="amount_percentage", 
                value={"percentage": percentage, "base": base},
                source_text=percent_match.group(0)
            ))
            return entities
        
        # Check for fixed amount patterns
        for pattern in self.amount_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                if 'between' not in match.group(0):  # Skip range patterns
                    amount_str = match.group(1).replace(',', '')
                    try:
                        amount = float(amount_str)
                        entities.append(ParsedEntity(
                            entity_type="amount_fixed",
                            value=amount,
                            source_text=match.group(0)
                        ))
                    except ValueError:
                        continue
        
        return entities
    
    def _extract_frequency(self, text: str) -> List[ParsedEntity]:
        """Extract frequency information from text."""
        entities = []
        
        for pattern, freq_type in self.frequency_patterns:
            match = re.search(pattern, text)
            if match:
                interval = 1
                if match.groups() and match.group(1).isdigit():
                    interval = int(match.group(1))
                
                entities.append(ParsedEntity(
                    entity_type="frequency",
                    value={"frequency": freq_type, "interval": interval},
                    source_text=match.group(0)
                ))
                break  # Use first match
        
        return entities
    
    def _extract_schedule(self, text: str) -> List[ParsedEntity]:
        """Extract schedule/timing information from text.""" 
        entities = []
        
        for pattern, schedule_type in self.time_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                if schedule_type == 'day_of_month':
                    day = int(match.group(1))
                    entities.append(ParsedEntity(
                        entity_type="schedule_day_of_month",
                        value=day,
                        source_text=match.group(0)
                    ))
                elif schedule_type == 'day_of_week':
                    day = match.group(1)
                    entities.append(ParsedEntity(
                        entity_type="schedule_day_of_week", 
                        value=day,
                        source_text=match.group(0)
                    ))
                elif schedule_type == 'weekend':
                    entities.append(ParsedEntity(
                        entity_type="schedule_weekend",
                        value=True,
                        source_text=match.group(0)
                    ))
                elif schedule_type == 'weekday':
                    entities.append(ParsedEntity(
                        entity_type="schedule_weekday",
                        value=True,
                        source_text=match.group(0)
                    ))
        
        return entities
    
    def _extract_categories(self, text: str) -> List[ParsedEntity]:
        """Extract category information from text."""
        entities = []
        
        for pattern, category in self.category_patterns:
            if re.search(pattern, text):
                entities.append(ParsedEntity(
                    entity_type="category",
                    value=category,
                    source_text=pattern
                ))
                break  # Use first match
        
        return entities
    
    def _extract_transaction_types(self, text: str) -> List[ParsedEntity]:
        """Extract transaction type information from text."""
        entities = []
        
        for pattern, txn_type in self.transaction_type_patterns:
            if re.search(pattern, text):
                entities.append(ParsedEntity(
                    entity_type="transaction_type",
                    value=txn_type,
                    source_text=pattern
                ))
                break  # Use first match
        
        return entities
    
    def _build_configuration(self, entities: List[ParsedEntity], original_text: str) -> Configuration:
        """Build Configuration object from extracted entities."""
        
        # Create default configuration
        config = Configuration()
        config.metadata = {
            "name": "Parsed Configuration",
            "description": f"Generated from: {original_text}",
            "version": "1.0",
            "source_text": original_text
        }
        
        # Create default account
        default_account = AccountConfig(
            account_id="default_account",
            name="Primary Account",
            type="checking", 
            initial_balance=5000.0
        )
        config.accounts.append(default_account)
        
        # Build transaction pattern from entities
        pattern = self._build_transaction_pattern(entities, original_text)
        config.transaction_patterns.append(pattern)
        
        return config
    
    def _build_transaction_pattern(self, entities: List[ParsedEntity], original_text: str) -> TransactionPatternConfig:
        """Build TransactionPatternConfig from entities."""
        
        # Initialize with defaults
        pattern = TransactionPatternConfig(
            pattern_id="parsed_pattern_1",
            name="Parsed Transaction Pattern",
            type="expense",  # Default to expense
            category="other"
        )
        
        # Process entities
        amount_config = AmountConfig()
        schedule_config = ScheduleConfig()
        merchant_config = None
        
        for entity in entities:
            if entity.entity_type == "amount_fixed":
                amount_config.type = "fixed"
                amount_config.value = entity.value
                
            elif entity.entity_type == "amount_range":
                amount_config.type = "range"
                amount_config.min = entity.value["min"]
                amount_config.max = entity.value["max"]
                
            elif entity.entity_type == "amount_percentage":
                # For percentage, we'll use a fixed amount as placeholder
                # In practice, you'd need more context about the base amount
                amount_config.type = "fixed"
                amount_config.value = 1000.0  # Placeholder
                
            elif entity.entity_type == "frequency":
                schedule_config.frequency = entity.value["frequency"]
                schedule_config.interval = entity.value["interval"]
                
            elif entity.entity_type == "schedule_day_of_month":
                schedule_config.day_of_month = [entity.value]
                
            elif entity.entity_type == "schedule_day_of_week":
                schedule_config.day_of_week = [entity.value]
                
            elif entity.entity_type == "schedule_weekend":
                schedule_config.day_of_week = ["saturday", "sunday"]
                
            elif entity.entity_type == "schedule_weekday":
                schedule_config.day_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday"]
                
            elif entity.entity_type == "category":
                pattern.category = entity.value
                
            elif entity.entity_type == "transaction_type":
                pattern.type = entity.value
        
        # Set configurations
        pattern.amount = amount_config
        pattern.schedule = schedule_config
        
        # Add merchant config if category suggests it
        if pattern.category in ["grocery", "gas", "restaurant", "shopping"]:
            merchant_config = MerchantConfig(
                categories=[pattern.category],
                use_real_data=False
            )
            pattern.merchant = merchant_config
        
        # Generate description template
        pattern.description_template = self._generate_description_template(pattern, original_text)
        
        return pattern
    
    def _generate_description_template(self, pattern: TransactionPatternConfig, original_text: str) -> str:
        """Generate a description template for the transaction pattern."""
        
        category_descriptions = {
            "salary": "Salary deposit - {merchant_name}",
            "grocery": "Grocery purchase - {merchant_name}", 
            "gas": "Gas station - {merchant_name}",
            "utilities": "Utility payment - {merchant_name}",
            "entertainment": "Entertainment - {merchant_name}",
            "restaurant": "Restaurant - {merchant_name}",
            "shopping": "Purchase - {merchant_name}",
            "atm": "ATM withdrawal",
            "other": f"Transaction - {original_text[:30]}..."
        }
        
        return category_descriptions.get(pattern.category, category_descriptions["other"])

# Export the parser class
__all__ = ['ConfigurationParser', 'ParsedEntity']