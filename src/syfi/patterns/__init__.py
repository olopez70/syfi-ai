"""
Gang of Four Design Patterns for SyFi AI

This module implements classic design patterns to improve architecture,
maintainability, and extensibility of the SyFi AI system.
"""

# Factory Method Pattern
from .factories import (
    DataGeneratorFactory,
    FamilyDataGeneratorFactory, 
    BusinessDataGeneratorFactory,
    GeneratorFactoryRegistry
)

# Strategy Pattern  
from .strategies import (
    ProfileBuildingStrategy,
    StandardFamilyStrategy,
    HighIncomeStrategy,
    YoungSingleStrategy,
    ProfileStrategyRegistry
)

# Repository Pattern
from .repositories import (
    CustomerRepository,
    AccountRepository,
    TransactionRepository,
    ProfileRepository,
    UnitOfWork,
    SQLiteUnitOfWork
)

# Builder Pattern
from .builders import (
    ProfileBuilder,
    ConcreteProfileBuilder,
    ProfileDirector
)

# Observer Pattern
from .observers import (
    Observer,
    Subject,
    GenerationEvent,
    GenerationEventData,
    ProgressLogger,
    ProgressBar,
    MetricsCollector,
    DatabaseEventLogger,
    ObservableDataGenerator,
    ObserverFactory
)

# Command Pattern
from .commands import (
    Command,
    ExportCommand,
    ExportCustomersCommand,
    ExportAccountsCommand,
    ExportTransactionsCommand,
    MacroCommand,
    CommandInvoker,
    ExportCommandFactory
)

__all__ = [
    # Factory Method Pattern
    'DataGeneratorFactory',
    'FamilyDataGeneratorFactory',
    'BusinessDataGeneratorFactory', 
    'GeneratorFactoryRegistry',
    
    # Strategy Pattern
    'ProfileBuildingStrategy',
    'StandardFamilyStrategy',
    'HighIncomeStrategy',
    'YoungSingleStrategy',
    'ProfileStrategyRegistry',
    
    # Repository Pattern
    'CustomerRepository',
    'AccountRepository', 
    'TransactionRepository',
    'ProfileRepository',
    'UnitOfWork',
    'SQLiteUnitOfWork',
    
    # Builder Pattern
    'ProfileBuilder',
    'ConcreteProfileBuilder',
    'ProfileDirector',
    
    # Observer Pattern
    'Observer',
    'Subject',
    'GenerationEvent',
    'GenerationEventData',
    'ProgressLogger',
    'ProgressBar',
    'MetricsCollector',
    'DatabaseEventLogger',
    'ObservableDataGenerator',
    'ObserverFactory',
    
    # Command Pattern
    'Command',
    'ExportCommand',
    'ExportCustomersCommand',
    'ExportAccountsCommand',
    'ExportTransactionsCommand',
    'MacroCommand',
    'CommandInvoker',
    'ExportCommandFactory'
]