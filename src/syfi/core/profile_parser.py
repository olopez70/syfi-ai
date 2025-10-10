"""
Customer profile parser for SyFi AI.

This module provides profile parsing functionality to interpret natural language
descriptions and convert them into structured customer profile data.
"""

import re
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class ProfileInfo:
    """Structured customer profile information."""
    household_size_range: Tuple[int, int] = (1, 1)
    num_adults_range: Tuple[int, int] = (1, 1)
    num_children_range: Tuple[int, int] = (0, 0)
    num_pets_range: Tuple[int, int] = (0, 0)
    income_range: Tuple[Optional[Decimal], Optional[Decimal]] = (None, None)
    employment_statuses: List[str] = None
    marital_statuses: List[str] = None
    has_mortgage: bool = False
    has_car_loan: bool = False
    has_credit_cards: bool = False
    car_loan_range: Tuple[int, int] = (0, 0)
    credit_card_range: Tuple[int, int] = (0, 0)
    external_accounts: List[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.employment_statuses is None:
            self.employment_statuses = []
        if self.marital_statuses is None:
            self.marital_statuses = []
        if self.external_accounts is None:
            self.external_accounts = []
        if self.tags is None:
            self.tags = []

class CustomerProfileParser:
    """
    Parses natural language customer profile descriptions into structured data.
    """
    
    def __init__(self):
        """Initialize the profile parser with patterns."""
        self.patterns = {
            'household_size': [
                r'(\d+)-(\d+)\s+(?:people|persons|individuals)',
                r'household(?:s)?\s+of\s+(\d+)-(\d+)',
                r'families?\s+of\s+(\d+)-(\d+)',
            ],
            'adults': [
                r'(\d+)-(\d+)\s+adults?',
                r'(\d+)\s+adults?',
            ],
            'children': [
                r'(\d+)-(\d+)\s+children',
                r'(\d+)\s+child(?:ren)?',
            ],
            'pets': [
                r'(\d+)-(\d+)\s+pets?',
                r'(\d+)\s+pets?',
            ],
            'income': [
                r'income(?:s)?\s+(?:of\s+)?(?:between\s+)?\$?(\d+(?:,\d+)*(?:k|K)?)\s*(?:-|to)\s*\$?(\d+(?:,\d+)*(?:k|K)?)',
                r'earning\s+\$?(\d+(?:,\d+)*(?:k|K)?)\s*(?:-|to)\s*\$?(\d+(?:,\d+)*(?:k|K)?)',
                r'(?:dual|two)\s+income',
                r'single\s+income',
            ],
            'employment': [
                r'(?:dual|two)\s+income',
                r'single\s+income', 
                r'unemployed',
                r'retired',
                r'self[-\s]?employed',
                r'full[-\s]?time',
                r'part[-\s]?time',
            ],
            'marital': [
                r'married',
                r'single',
                r'divorced',
                r'widowed',
            ],
            'mortgage': [
                r'mortgage(?:s)?',
                r'home\s+loan(?:s)?',
                r'house\s+payment(?:s)?',
            ],
            'car_loans': [
                r'(\d+)-(\d+)\s+car\s+loan(?:s)?',
                r'(\d+)\s+car\s+loan(?:s)?',
                r'auto\s+loan(?:s)?',
                r'vehicle\s+loan(?:s)?',
            ],
            'credit_cards': [
                r'(\d+)-(\d+)\s+credit\s+card(?:s)?',
                r'(\d+)\s+credit\s+card(?:s)?',
            ],
            'external_bank': [
                r'external\s+bank',
                r'other\s+bank(?:s)?',
                r'different\s+bank',
                r'held\s+(?:at\s+)?(?:an?\s+)?external\s+bank',
            ],
        }
    
    def parse_profile(self, description: str) -> ProfileInfo:
        """
        Parse a natural language profile description.
        
        Args:
            description: Natural language description of customer profile
            
        Returns:
            ProfileInfo object with structured data
        """
        description = description.lower().strip()
        profile = ProfileInfo()
        
        # Parse household composition
        profile.num_adults_range = self._extract_range(description, 'adults')
        profile.num_children_range = self._extract_range(description, 'children')
        profile.num_pets_range = self._extract_range(description, 'pets')
        
        # Calculate total household size
        min_household = profile.num_adults_range[0] + profile.num_children_range[0]
        max_household = profile.num_adults_range[1] + profile.num_children_range[1]
        profile.household_size_range = (min_household, max_household)
        
        # Parse income information
        profile.income_range = self._extract_income_range(description)
        
        # Parse employment status
        profile.employment_statuses = self._extract_employment_status(description)
        
        # Parse marital status
        profile.marital_statuses = self._extract_marital_status(description)
        
        # Parse financial products
        profile.has_mortgage = self._has_pattern(description, 'mortgage')
        profile.has_car_loan = self._has_pattern(description, 'car_loans')
        profile.has_credit_cards = self._has_pattern(description, 'credit_cards')
        
        # Parse specific counts
        profile.car_loan_range = self._extract_range(description, 'car_loans')
        profile.credit_card_range = self._extract_range(description, 'credit_cards')
        
        # Parse external banking
        if self._has_pattern(description, 'external_bank'):
            profile.external_accounts = ['mortgage', 'car_loan', 'credit_card']
        
        # Generate tags
        profile.tags = self._generate_tags(description, profile)
        
        return profile
    
    def _extract_range(self, text: str, pattern_key: str) -> Tuple[int, int]:
        """Extract numeric range from text for a given pattern."""
        patterns = self.patterns.get(pattern_key, [])
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    # Range format (e.g., "1-4 children")
                    try:
                        min_val = int(groups[0])
                        max_val = int(groups[1])
                        return (min_val, max_val)
                    except (ValueError, IndexError):
                        continue
                elif len(groups) == 1:
                    # Single value format (e.g., "2 adults")
                    try:
                        val = int(groups[0])
                        return (val, val)
                    except ValueError:
                        continue
        
        # Default ranges based on pattern key
        defaults = {
            'adults': (1, 1),
            'children': (0, 0),
            'pets': (0, 0),
            'car_loans': (0, 0),
            'credit_cards': (0, 0),
        }
        return defaults.get(pattern_key, (0, 0))
    
    def _extract_income_range(self, text: str) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        """Extract income range from text."""
        income_patterns = self.patterns['income']
        
        for pattern in income_patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    try:
                        min_income = self._parse_income_value(groups[0])
                        max_income = self._parse_income_value(groups[1])
                        return (min_income, max_income)
                    except (ValueError, TypeError):
                        continue
        
        # Default income ranges based on keywords
        if 'dual income' in text or 'two income' in text:
            return (Decimal('60000'), Decimal('150000'))  # Typical dual income range
        elif 'single income' in text:
            return (Decimal('30000'), Decimal('80000'))   # Typical single income range
        
        return (None, None)
    
    def _parse_income_value(self, value_str: str) -> Decimal:
        """Parse income value string (handles k/K suffix)."""
        value_str = value_str.replace(',', '').strip()
        
        if value_str.lower().endswith('k'):
            base_value = Decimal(value_str[:-1])
            return base_value * 1000
        else:
            return Decimal(value_str)
    
    def _extract_employment_status(self, text: str) -> List[str]:
        """Extract employment status indicators."""
        statuses = []
        
        if 'dual income' in text or 'two income' in text:
            statuses.append('dual_income')
        elif 'single income' in text:
            statuses.append('single_income')
        
        if 'full-time' in text or 'full time' in text:
            statuses.append('full_time')
        if 'part-time' in text or 'part time' in text:
            statuses.append('part_time')
        if 'self-employed' in text or 'self employed' in text:
            statuses.append('self_employed')
        if 'retired' in text:
            statuses.append('retired')
        if 'unemployed' in text:
            statuses.append('unemployed')
        
        return statuses or ['employed']  # Default to employed
    
    def _extract_marital_status(self, text: str) -> List[str]:
        """Extract marital status indicators."""
        statuses = []
        
        if 'married' in text:
            statuses.append('married')
        if 'single' in text:
            statuses.append('single')
        if 'divorced' in text:
            statuses.append('divorced')
        if 'widowed' in text:
            statuses.append('widowed')
        
        # Infer from household composition
        if not statuses:
            # If multiple adults mentioned, likely married
            if 'adults' in text and ('2 adults' in text or 'two adults' in text):
                statuses.append('married')
            else:
                statuses.append('single')
        
        return statuses
    
    def _has_pattern(self, text: str, pattern_key: str) -> bool:
        """Check if text contains any of the patterns for a given key."""
        patterns = self.patterns.get(pattern_key, [])
        
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    def _generate_tags(self, description: str, profile: ProfileInfo) -> List[str]:
        """Generate tags based on the parsed profile."""
        tags = []
        
        # Household composition tags
        if profile.num_children_range[1] > 0:
            tags.append('family_with_children')
        if profile.num_pets_range[1] > 0:
            tags.append('pet_owners')
        if profile.num_adults_range[1] > 1:
            tags.append('multi_adult_household')
        
        # Income tags
        if 'dual income' in description or 'two income' in description:
            tags.append('dual_income')
        if 'single income' in description:
            tags.append('single_income')
        
        # Financial product tags
        if profile.has_mortgage:
            tags.append('homeowners')
        if profile.has_car_loan:
            tags.append('auto_borrowers')
        if profile.has_credit_cards:
            tags.append('credit_card_users')
        
        # External banking tags
        if profile.external_accounts:
            tags.append('multi_bank_relationships')
        
        return tags

# Export the parser class
__all__ = ['CustomerProfileParser', 'ProfileInfo']