"""
SyFi AI - Synthetic Banking Data Library

A Python library for generating realistic synthetic banking transaction data
from natural language descriptions.
"""

__version__ = "0.1.0"
__author__ = "SyFi AI Team"
__description__ = "Synthetic Banking Data Generation Library"

# Import statements will be added after creating the modules
# from .core.parser import ConfigurationParser
# from .database import DatabaseManager
from .generators import CustomerGenerator, TransactionEngine
from .profile_builder import ProfileBuilder, BankingDataGenerator, create_young_professional_template  
# from .core.config import Configuration
# from .core.validator import ValidationEngine
# from .models.account import Account
# from .models.transaction import Transaction
# from .models.customer import Customer

class SyFiGenerator:
    """Main interface for the SyFi AI library."""
    
    def __init__(self, config=None):
        self.config = config
        self.generator = None
        # Will be implemented after creating TransactionGenerator
        # if config:
        #     self.generator = TransactionGenerator(config)
    
    def from_natural_language(self, prompt: str):
        """Create generator from natural language description."""
        # Import here to avoid circular imports during initialization
        from .core.parser import ConfigurationParser
        
        print(f"Processing natural language prompt: {prompt}")
        parser = ConfigurationParser()
        self.config = parser.parse(prompt)
        # self.generator = TransactionGenerator(self.config)  # Will implement later
        return self
    
    def generate_period(self, start_date: str, end_date: str):
        """Generate transactions for specified time period."""
        print(f"Generating transactions from {start_date} to {end_date}")
        return []

__all__ = [
    "SyFiGenerator"
]