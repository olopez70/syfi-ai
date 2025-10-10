"""
Configuration management for SyFi AI.

This module handles configuration parsing, validation, and management
for the synthetic banking data generation system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, date
import json
import yaml
from pathlib import Path

@dataclass 
class AmountConfig:
    """Configuration for transaction amounts."""
    
    type: str = "fixed"  # "fixed", "range", "normal", "uniform"
    value: Optional[float] = None
    min: Optional[float] = None 
    max: Optional[float] = None
    mean: Optional[float] = None
    std: Optional[float] = None
    currency: str = "USD"
    
    def validate(self) -> bool:
        """Validate the amount configuration."""
        if self.type == "fixed" and self.value is None:
            return False
        if self.type == "range" and (self.min is None or self.max is None):
            return False
        if self.type in ["normal"] and (self.mean is None or self.std is None):
            return False
        return True

@dataclass
class ScheduleConfig:
    """Configuration for transaction scheduling."""
    
    frequency: str = "monthly"  # "daily", "weekly", "monthly", "quarterly", "yearly"
    interval: int = 1  # Every N periods
    day_of_week: Optional[List[str]] = None  # ["monday", "tuesday", ...]
    day_of_month: Optional[List[int]] = None  # [1, 15, -1] (-1 = last day)
    time_range: Optional[List[str]] = None  # ["09:00", "17:00"]
    exclude_weekends: bool = False
    exclude_holidays: bool = False
    
    def validate(self) -> bool:
        """Validate the schedule configuration."""
        valid_frequencies = ["daily", "weekly", "monthly", "quarterly", "yearly"]
        if self.frequency not in valid_frequencies:
            return False
        return True

@dataclass
class MerchantConfig:
    """Configuration for merchant information."""
    
    categories: Optional[List[str]] = None
    names: Optional[List[str]] = None
    use_real_data: bool = False
    location_bias: Optional[str] = None  # "local", "national", "international"

@dataclass 
class TransactionPatternConfig:
    """Configuration for a transaction pattern."""
    
    pattern_id: str = ""
    name: str = ""
    type: str = "expense"  # "income", "expense", "transfer"
    category: str = "other"
    amount: AmountConfig = field(default_factory=AmountConfig)
    schedule: ScheduleConfig = field(default_factory=ScheduleConfig) 
    merchant: Optional[MerchantConfig] = None
    description_template: str = ""
    enabled: bool = True
    
    def validate(self) -> bool:
        """Validate the transaction pattern configuration."""
        if not self.pattern_id or not self.name:
            return False
        if not self.amount.validate():
            return False
        if not self.schedule.validate():
            return False
        return True

@dataclass
class AccountConfig:
    """Configuration for account setup."""
    
    account_id: str = ""
    name: str = ""
    type: str = "checking"  # "checking", "savings", "credit"
    initial_balance: float = 0.0
    currency: str = "USD"
    overdraft_limit: Optional[float] = None
    
    def validate(self) -> bool:
        """Validate the account configuration."""
        if not self.account_id or not self.name:
            return False
        valid_types = ["checking", "savings", "credit", "investment", "loan"]
        if self.type not in valid_types:
            return False
        return True

@dataclass
class GenerationConfig:
    """Configuration for data generation parameters."""
    
    seed: int = 12345
    deterministic: bool = True
    output_format: str = "json"  # "json", "csv", "parquet"
    include_metadata: bool = True
    validate_consistency: bool = True

@dataclass
class Configuration:
    """Main configuration class for SyFi AI."""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    accounts: List[AccountConfig] = field(default_factory=list)
    transaction_patterns: List[TransactionPatternConfig] = field(default_factory=list)
    
    def __post_init__(self):
        """Post-initialization processing."""
        if not self.metadata:
            self.metadata = {
                "name": "SyFi Configuration",
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "description": "Generated configuration for synthetic banking data"
            }
    
    def validate(self) -> bool:
        """Validate the entire configuration."""
        # Validate accounts
        for account in self.accounts:
            if not account.validate():
                return False
        
        # Validate transaction patterns
        for pattern in self.transaction_patterns:
            if not pattern.validate():
                return False
        
        # Check for unique account IDs
        account_ids = [acc.account_id for acc in self.accounts]
        if len(account_ids) != len(set(account_ids)):
            return False
            
        # Check for unique pattern IDs
        pattern_ids = [pat.pattern_id for pat in self.transaction_patterns]
        if len(pattern_ids) != len(set(pattern_ids)):
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'metadata': self.metadata,
            'generation': {
                'seed': self.generation.seed,
                'deterministic': self.generation.deterministic,
                'output_format': self.generation.output_format,
                'include_metadata': self.generation.include_metadata,
                'validate_consistency': self.generation.validate_consistency
            },
            'accounts': [
                {
                    'account_id': acc.account_id,
                    'name': acc.name,
                    'type': acc.type,
                    'initial_balance': acc.initial_balance,
                    'currency': acc.currency,
                    'overdraft_limit': acc.overdraft_limit
                } for acc in self.accounts
            ],
            'transaction_patterns': [
                {
                    'pattern_id': pat.pattern_id,
                    'name': pat.name,
                    'type': pat.type,
                    'category': pat.category,
                    'amount': {
                        'type': pat.amount.type,
                        'value': pat.amount.value,
                        'min': pat.amount.min,
                        'max': pat.amount.max,
                        'mean': pat.amount.mean,
                        'std': pat.amount.std,
                        'currency': pat.amount.currency
                    },
                    'schedule': {
                        'frequency': pat.schedule.frequency,
                        'interval': pat.schedule.interval,
                        'day_of_week': pat.schedule.day_of_week,
                        'day_of_month': pat.schedule.day_of_month,
                        'time_range': pat.schedule.time_range,
                        'exclude_weekends': pat.schedule.exclude_weekends,
                        'exclude_holidays': pat.schedule.exclude_holidays
                    },
                    'merchant': {
                        'categories': pat.merchant.categories if pat.merchant else None,
                        'names': pat.merchant.names if pat.merchant else None,
                        'use_real_data': pat.merchant.use_real_data if pat.merchant else False,
                        'location_bias': pat.merchant.location_bias if pat.merchant else None
                    } if pat.merchant else None,
                    'description_template': pat.description_template,
                    'enabled': pat.enabled
                } for pat in self.transaction_patterns
            ]
        }
    
    def save_to_file(self, filepath: Union[str, Path]) -> None:
        """Save configuration to file (JSON or YAML based on extension)."""
        filepath = Path(filepath)
        data = self.to_dict()
        
        if filepath.suffix.lower() == '.yaml' or filepath.suffix.lower() == '.yml':
            with open(filepath, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, indent=2)
        else:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
    
    @classmethod
    def load_from_file(cls, filepath: Union[str, Path]) -> 'Configuration':
        """Load configuration from file."""
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Configuration file not found: {filepath}")
        
        with open(filepath, 'r') as f:
            if filepath.suffix.lower() in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Configuration':
        """Create configuration from dictionary."""
        # This is a simplified version - in practice you'd want more robust parsing
        config = cls()
        config.metadata = data.get('metadata', {})
        
        gen_data = data.get('generation', {})
        config.generation = GenerationConfig(
            seed=gen_data.get('seed', 12345),
            deterministic=gen_data.get('deterministic', True),
            output_format=gen_data.get('output_format', 'json'),
            include_metadata=gen_data.get('include_metadata', True),
            validate_consistency=gen_data.get('validate_consistency', True)
        )
        
        # Parse accounts
        for acc_data in data.get('accounts', []):
            account = AccountConfig(
                account_id=acc_data.get('account_id', ''),
                name=acc_data.get('name', ''),
                type=acc_data.get('type', 'checking'),
                initial_balance=acc_data.get('initial_balance', 0.0),
                currency=acc_data.get('currency', 'USD'),
                overdraft_limit=acc_data.get('overdraft_limit')
            )
            config.accounts.append(account)
        
        # Parse transaction patterns
        for pat_data in data.get('transaction_patterns', []):
            amount_data = pat_data.get('amount', {})
            amount_config = AmountConfig(
                type=amount_data.get('type', 'fixed'),
                value=amount_data.get('value'),
                min=amount_data.get('min'),
                max=amount_data.get('max'),
                mean=amount_data.get('mean'),
                std=amount_data.get('std'),
                currency=amount_data.get('currency', 'USD')
            )
            
            schedule_data = pat_data.get('schedule', {})
            schedule_config = ScheduleConfig(
                frequency=schedule_data.get('frequency', 'monthly'),
                interval=schedule_data.get('interval', 1),
                day_of_week=schedule_data.get('day_of_week'),
                day_of_month=schedule_data.get('day_of_month'),
                time_range=schedule_data.get('time_range'),
                exclude_weekends=schedule_data.get('exclude_weekends', False),
                exclude_holidays=schedule_data.get('exclude_holidays', False)
            )
            
            merchant_data = pat_data.get('merchant')
            merchant_config = None
            if merchant_data:
                merchant_config = MerchantConfig(
                    categories=merchant_data.get('categories'),
                    names=merchant_data.get('names'),
                    use_real_data=merchant_data.get('use_real_data', False),
                    location_bias=merchant_data.get('location_bias')
                )
            
            pattern = TransactionPatternConfig(
                pattern_id=pat_data.get('pattern_id', ''),
                name=pat_data.get('name', ''),
                type=pat_data.get('type', 'expense'),
                category=pat_data.get('category', 'other'),
                amount=amount_config,
                schedule=schedule_config,
                merchant=merchant_config,
                description_template=pat_data.get('description_template', ''),
                enabled=pat_data.get('enabled', True)
            )
            config.transaction_patterns.append(pattern)
        
        return config

# Export configuration classes
__all__ = [
    'Configuration',
    'GenerationConfig',
    'AccountConfig', 
    'TransactionPatternConfig',
    'AmountConfig',
    'ScheduleConfig',
    'MerchantConfig'
]