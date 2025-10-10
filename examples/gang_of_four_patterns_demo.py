#!/usr/bin/env python3
"""
Enhanced Architecture Example using Gang of Four Design Patterns
===============================================================

This example demonstrates the improved SyFi AI architecture utilizing
classic design patterns for maintainable and extensible code.

Patterns Demonstrated:
- Factory Method: Extensible data generator creation
- Strategy: Interchangeable profile building algorithms  
- Repository: Clean data access layer abstraction
- Builder: Complex profile construction
- Observer: Progress monitoring and event handling
- Command: Encapsulated operations with undo capability

Run this example to see professional architecture in action!
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from syfi.database import DatabaseManager

# Import patterns individually to avoid potential circular imports
try:
    from syfi.patterns.factories import FamilyDataGeneratorFactory, BusinessDataGeneratorFactory, GeneratorFactoryRegistry
    from syfi.patterns.strategies import StandardFamilyStrategy, HighIncomeStrategy, YoungSingleStrategy, ProfileStrategyRegistry
    from syfi.patterns.repositories import SQLiteUnitOfWork
    print("✅ Basic patterns imported successfully")
except ImportError as e:
    print(f"❌ Error importing basic patterns: {e}")
    sys.exit(1)

# Import remaining patterns
try:
    from syfi.patterns.builders import ConcreteProfileBuilder, ProfileDirector
    from syfi.patterns.observers import (
        ProgressLogger, ProgressBar, MetricsCollector, DatabaseEventLogger,
        ObservableDataGenerator, ObserverFactory
    )
    from syfi.patterns.commands import (
        ExportCustomersCommand, ExportAccountsCommand, ExportTransactionsCommand,
        MacroCommand, CommandInvoker, ExportCommandFactory
    )
    print("✅ All patterns imported successfully")
except ImportError as e:
    print(f"❌ Error importing advanced patterns: {e}")
    print("Continuing with basic patterns only...")
    # Set dummy variables to avoid name errors
    ConcreteProfileBuilder = None
    ProfileDirector = None
    ProgressLogger = None
    ProgressBar = None
    MetricsCollector = None
    DatabaseEventLogger = None
    ObservableDataGenerator = None
    ObserverFactory = None
    ExportCustomersCommand = None
    ExportAccountsCommand = None
    ExportTransactionsCommand = None
    MacroCommand = None
    CommandInvoker = None
    ExportCommandFactory = None

# Old import block removed


def demonstrate_factory_pattern():
    """Demonstrate Factory Method pattern for extensible generation."""
    print("\n🏭 FACTORY METHOD PATTERN DEMO")
    print("=" * 50)
    
    # Register different factory types
    registry = GeneratorFactoryRegistry()
    registry.register_factory("family", FamilyDataGeneratorFactory())
    registry.register_factory("business", BusinessDataGeneratorFactory())
    
    # Create generators using factory
    family_factory = registry.create_factory("family")
    business_factory = registry.create_factory("business")
    
    print(f"✅ Family Factory: {type(family_factory).__name__}")
    print(f"✅ Business Factory: {type(business_factory).__name__}")
    print("💡 Easy to add new generator types without modifying existing code!")


def demonstrate_strategy_pattern():
    """Demonstrate Strategy pattern for interchangeable algorithms."""
    print("\n🎯 STRATEGY PATTERN DEMO")  
    print("=" * 50)
    
    # Register different building strategies
    registry = ProfileStrategyRegistry()
    registry.register("standard", StandardFamilyStrategy())
    registry.register("high_income", HighIncomeStrategy()) 
    registry.register("young_single", YoungSingleStrategy())
    
    # Show different strategies available
    strategies = registry.list_strategies()
    for name, strategy in strategies.items():
        print(f"✅ {name}: {type(strategy).__name__}")
    
    print("💡 Algorithms can be swapped at runtime for different behaviors!")


def demonstrate_repository_pattern(db_manager):
    """Demonstrate Repository pattern for clean data access."""
    print("\n📚 REPOSITORY PATTERN DEMO")
    print("=" * 50)
    
    # Use Unit of Work for transaction management
    with SQLiteUnitOfWork(db_manager) as uow:
        customer_repo = uow.customers
        account_repo = uow.accounts
        transaction_repo = uow.transactions
        
        print(f"✅ Customer Repository: {type(customer_repo).__name__}")
        print(f"✅ Account Repository: {type(account_repo).__name__}")  
        print(f"✅ Transaction Repository: {type(transaction_repo).__name__}")
        print("💡 Database operations abstracted behind clean interfaces!")
        
        # Example: Count entities
        customer_count = customer_repo.count()
        account_count = account_repo.count()
        transaction_count = transaction_repo.count()
        
        print(f"📊 Current data: {customer_count} customers, {account_count} accounts, {transaction_count} transactions")


def demonstrate_builder_pattern(db_manager):
    """Demonstrate Builder pattern for complex profile construction."""
    print("\n🔨 BUILDER PATTERN DEMO")
    print("=" * 50)
    
    # Use director to build different profile types
    builder = ConcreteProfileBuilder(db_manager)
    director = ProfileDirector(builder)
    
    print("Building different profile types:")
    
    # Build family profile
    family_profile = director.build_family_profile()
    print(f"👨‍👩‍👧‍👦 Family Profile: {family_profile.profile_name}")
    print(f"   💰 Income Range: ${family_profile.income_range['min']:,} - ${family_profile.income_range['max']:,}")
    print(f"   🏠 Address: {family_profile.address_pattern}")
    
    # Build high income profile  
    high_income_profile = director.build_high_income_profile()
    print(f"💎 High Income Profile: {high_income_profile.profile_name}")
    print(f"   💰 Income Range: ${high_income_profile.income_range['min']:,} - ${high_income_profile.income_range['max']:,}")
    
    print("💡 Complex construction logic encapsulated in reusable builders!")


def demonstrate_observer_pattern(db_manager):
    """Demonstrate Observer pattern for progress monitoring."""
    print("\n👀 OBSERVER PATTERN DEMO")
    print("=" * 50)
    
    # Create observable data generator
    generator = ObservableDataGenerator(db_manager)
    
    # Create and attach different observers
    progress_logger = ObserverFactory.create_observer("progress_logger", {"log_level": "INFO"})
    progress_bar = ObserverFactory.create_observer("progress_bar", {"width": 30})
    metrics_collector = ObserverFactory.create_observer("metrics", {})
    db_event_logger = ObserverFactory.create_observer("database_events", {"db_manager": db_manager})
    
    generator.attach_observer(progress_logger)
    generator.attach_observer(progress_bar)
    generator.attach_observer(metrics_collector)
    generator.attach_observer(db_event_logger)
    
    print("🔗 Observers attached:")
    print(f"   📝 {type(progress_logger).__name__}")
    print(f"   📊 {type(progress_bar).__name__}")
    print(f"   📈 {type(metrics_collector).__name__}")  
    print(f"   🗃️ {type(db_event_logger).__name__}")
    
    # Generate some data to trigger observer notifications
    print("\n🚀 Generating sample data (observers will be notified)...")
    generator.generate_customers(2, profile_id=1)
    
    print("💡 Multiple observers can monitor the same operations independently!")


def demonstrate_command_pattern(db_manager):
    """Demonstrate Command pattern for encapsulated operations."""
    print("\n⚡ COMMAND PATTERN DEMO")
    print("=" * 50)
    
    # Create command invoker
    invoker = CommandInvoker()
    
    # Create export commands
    export_customers = ExportCommandFactory.create_export_command(
        "customers", db_manager, "demo_customers.txt"
    )
    export_accounts = ExportCommandFactory.create_export_command(
        "accounts", db_manager, "demo_accounts.txt"
    )
    export_transactions = ExportCommandFactory.create_export_command(
        "transactions", db_manager, "demo_transactions.txt"
    )
    
    # Create macro command for bulk operations
    bulk_export = MacroCommand("Bulk Export", [
        export_customers,
        export_accounts, 
        export_transactions
    ])
    
    print("📋 Commands created:")
    print(f"   💾 {export_customers.description}")
    print(f"   💾 {export_accounts.description}")
    print(f"   💾 {export_transactions.description}")
    print(f"   📦 {bulk_export.description} (macro)")
    
    # Execute commands
    print("\n🎬 Executing bulk export command...")
    result = invoker.execute_command(bulk_export)
    
    if result.success:
        print("✅ Bulk export completed successfully!")
        print(f"📁 Files created in exports/ directory")
        
        # Show command history
        history = invoker.get_command_history()
        print(f"\n📜 Command history: {len(history)} commands executed")
        
        # Demonstrate undo capability
        print("🔄 Demonstrating undo capability...")
        undo_result = invoker.undo_last_command()
        if undo_result.success:
            print("✅ Last command undone successfully!")
    
    print("💡 Operations encapsulated as objects with undo capability!")


def main():
    """Run comprehensive Gang of Four patterns demonstration."""
    print("🎨 SYFI AI - GANG OF FOUR PATTERNS DEMONSTRATION")
    print("=" * 60)
    print("Showcasing professional architecture using classic design patterns")
    
    # Setup database
    db_path = "data/gof_patterns_demo.db"
    db_manager = DatabaseManager(db_path)
    db_manager.initialize_schema()
    
    try:
        # Demonstrate each pattern
        demonstrate_factory_pattern()
        demonstrate_strategy_pattern()
        demonstrate_repository_pattern(db_manager)
        demonstrate_builder_pattern(db_manager)
        demonstrate_observer_pattern(db_manager)
        demonstrate_command_pattern(db_manager)
        
        print("\n🎉 DEMONSTRATION COMPLETE!")
        print("=" * 60)
        print("✨ Architecture Benefits Achieved:")
        print("   🏭 Factory Method: Extensible object creation")
        print("   🎯 Strategy: Interchangeable algorithms") 
        print("   📚 Repository: Clean data access abstraction")
        print("   🔨 Builder: Complex object construction")
        print("   👀 Observer: Decoupled event handling")
        print("   ⚡ Command: Encapsulated operations with undo")
        print("\n💡 Your codebase now follows professional design patterns!")
        print("🚀 Easy to extend, maintain, and test!")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db_manager.close()


if __name__ == "__main__":
    main()