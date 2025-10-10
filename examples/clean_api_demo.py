#!/usr/bin/env python3
"""
Simple API Demo - Clean ProfileBuilder Usage

This shows the ideal clean API for using SyFi AI:
"""

import sys
from pathlib import Path
from datetime import date

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from syfi.database import DatabaseManager
from syfi.profile_builder import (
    ProfileBuilder, BankingDataGenerator, create_young_professional_template
)


def main():
    """Demonstrate the clean ProfileBuilder API."""
    
    print("🎯 SyFi AI Clean API Demonstration")
    print("="*40)
    
    # Setup database
    project_root = Path(__file__).parent.parent
    db_path = project_root / "data" / "clean_api_demo.db"
    (project_root / "data").mkdir(exist_ok=True)
    
    db_manager = DatabaseManager(db_path)
    db_manager.initialize_schema()
    
    # 1. Create a profile template
    template = create_young_professional_template()
    print(f"✅ Template: {template.name}")
    
    # 2. Use ProfileBuilder to create profiles
    builder = ProfileBuilder(seed=2025)
    profile = builder.build_profile(template, "The Smith Family")
    print(f"✅ Profile: {profile.name} - ${profile.household_income:,} income")
    
    # 3. Generate banking data
    data_generator = BankingDataGenerator(db_manager)
    result = data_generator.generate_banking_data(
        profile, 
        start_date=date(2025, 1, 1), 
        end_date=date(2025, 1, 31)
    )
    
    print(f"✅ Banking Data Generated:")
    print(f"   👥 {len(result['customers'])} customers")
    print(f"   💳 {len(result['accounts'])} accounts") 
    print(f"   💰 {len(result['transactions'])} transactions")
    
    # 4. Show sample customer
    customer = result['customers'][0]
    print(f"\n👤 Sample Customer:")
    print(f"   Name: {customer.first_name} {customer.last_name}")
    print(f"   Job: {customer.employment_status}")
    print(f"   Household: ${customer.household_income:,}, {customer.household_size} members")
    
    print(f"\n💾 Data saved to: {db_path}")
    print("🎉 Clean API demo complete!")


if __name__ == "__main__":
    main()