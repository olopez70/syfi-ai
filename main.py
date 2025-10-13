#!/usr/bin/env python3
"""
SyFi AI - Synthetic Banking Data Library
Main CLI interface and realistic banking data demonstration.

This demonstrates the core SyFi AI capabilities:
1. Natural language parsing for transaction patterns
2. Realistic banking profile generation using ProfileBuilder
3. Banking data generation for complete datasets
4. Sample data queries and exports

Run with: python main.py
"""

import sys
from pathlib import Path
from datetime import date
import json

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from syfi.database import DatabaseManager
from syfi.profile_builder import (
    ProfileBuilder, BankingDataGenerator, create_young_professional_template
)
from syfi.core.parser import ConfigurationParser


def demo_natural_language_parsing():
    """Demonstrate natural language parsing capabilities."""
    print("🏦 SyFi AI - Synthetic Banking Data Library")
    print("=" * 50)
    
    # Example natural language prompts
    prompts = [
        "Generate monthly salary deposits of $3,500 on the 15th",
        "Create weekly grocery spending between $80-120 on weekends", 
        "Simulate quarterly tax payments of 22% of income",
        "Generate random ATM withdrawals of $20-200, 2-5 times per week"
    ]
    
    parser = ConfigurationParser()
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\n{i}. Processing: '{prompt}'")
        print("-" * 40)
        
        try:
            config = parser.parse(prompt)
            print("✅ Parsed successfully!")
            
            # Handle different return types properly
            if isinstance(config, dict):
                print(f"   - Transaction Type: {config.get('transaction_type', 'N/A')}")
                print(f"   - Category: {config.get('category', 'N/A')}")
                print(f"   - Amount Type: {config.get('amount_type', 'N/A')}")
                print(f"   - Amount Value: ${config.get('amount', 0)}")
                print(f"   - Frequency: {config.get('frequency', 'N/A')}")
            else:
                # Handle Configuration object with attribute access
                print(f"   - Configuration type: {type(config).__name__}")
                print(f"   - Transaction Type: {getattr(config, 'transaction_type', 'N/A')}")
                print(f"   - Category: {getattr(config, 'category', 'N/A')}")
                print(f"   - Amount Type: {getattr(config, 'amount_type', 'N/A')}")
                print(f"   - Amount Value: ${getattr(config, 'amount', 0)}")
                print(f"   - Frequency: {getattr(config, 'frequency', 'N/A')}")
            
            # Save example config
            config_file = f"example_config_{i}.json"
            if isinstance(config, dict):
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)
            else:
                # Convert dataclass to dict for JSON serialization
                import dataclasses
                if dataclasses.is_dataclass(config):
                    config_dict = dataclasses.asdict(config)
                    with open(config_file, 'w') as f:
                        json.dump(config_dict, f, indent=2, default=str)
                else:
                    # Fallback: convert object to dict using __dict__
                    config_dict = getattr(config, '__dict__', {})
                    with open(config_file, 'w') as f:
                        json.dump(config_dict, f, indent=2, default=str)
            print(f"   - Saved to: {config_file}")
            
        except Exception as e:
            print(f"❌ Parsing failed: {e}")

def generate_summary_report(results: list, db_path: str) -> None:
    """Generate a summary report of all generated data."""
    
    print("\n" + "="*60)
    print("           SyFi AI BANKING DATA GENERATION SUMMARY")
    print("="*60)
    
    total_customers = sum(len(result["customers"]) for result in results)
    total_accounts = sum(len(result["accounts"]) for result in results)
    total_transactions = sum(len(result["transactions"]) for result in results)
    
    print(f"\n📊 GENERATION STATISTICS:")
    print(f"   Database: {db_path}")
    print(f"   Profiles Generated: {len(results)}")
    print(f"   Total Customers: {total_customers}")
    print(f"   Total Accounts: {total_accounts}")
    print(f"   Total Transactions: {total_transactions}")
    print(f"   Date Range: January 1-31, 2025")
    
    print(f"\n👥 PROFILE BREAKDOWN:")
    for i, result in enumerate(results, 1):
        profile = result["profile"]
        print(f"   Profile {i}: {profile.name}")
        print(f"      Household Income: ${profile.household_income:,}")
        print(f"      Customers: {len(result['customers'])}")
        print(f"      Accounts: {len(result['accounts'])}")
        print(f"      Transactions: {len(result['transactions'])}")
        
        # Calculate total transaction volume
        total_credits = sum(t.amount for t in result["transactions"] if t.amount > 0)
        total_debits = sum(abs(t.amount) for t in result["transactions"] if t.amount < 0)
        print(f"      Transaction Volume: ${total_credits + total_debits:,.2f}")
        print(f"         Credits: ${total_credits:,.2f}")
        print(f"         Debits: ${total_debits:,.2f}")
    
    print("\n✅ Generation Complete! All data successfully created and stored.")


def query_sample_data(db_manager: DatabaseManager):
    """Query and display sample data from the generated database."""
    
    print("\n" + "-"*50)
    print("SAMPLE DATA QUERIES")
    print("-"*50)
    
    # Query customers
    customers = db_manager.get_all_customers()
    print(f"\n👥 GENERATED CUSTOMERS ({len(customers)} total):")
    for customer in customers[:6]:  # Show first 6 customers
        print(f"   {customer['first_name']} {customer['last_name']} - {customer['employment_status']}")
        print(f"      ID: {customer['customer_id']}")
        print(f"      Household Income: ${customer['household_income']:,}")
        print(f"      Household Size: {customer['household_size']}")
    
    if len(customers) > 6:
        print(f"   ... and {len(customers) - 6} more customers")
    
    # Use SQL query for recent transactions
    import sqlite3
    conn = sqlite3.connect(str(db_manager.db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT t.*, a.customer_id, c.first_name, c.last_name
        FROM transactions t
        JOIN accounts a ON t.account_id = a.account_id
        JOIN customers c ON a.customer_id = c.customer_id
        ORDER BY t.transaction_date DESC
        LIMIT 10
    """)
    recent_transactions = cursor.fetchall()
    
    print(f"\n💰 RECENT TRANSACTIONS (showing 10 most recent):")
    for transaction in recent_transactions:
        amount_str = f"${abs(transaction['amount']):,.2f}"
        if transaction['amount'] < 0:
            amount_str = f"-{amount_str}"
        else:
            amount_str = f"+{amount_str}"
        
        customer_name = f"{transaction['first_name']} {transaction['last_name']}"
        print(f"   {transaction['transaction_date'][:10]} | {amount_str:>12} | {customer_name}")
        print(f"      {transaction['description']} ({transaction['category']})")
        if transaction['merchant_name']:
            print(f"      Merchant: {transaction['merchant_name']}")
    
    # Transaction summary by category
    cursor.execute("""
        SELECT category, 
               COUNT(*) as count,
               SUM(ABS(amount)) as total,
               SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as credits,
               SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as debits
        FROM transactions
        GROUP BY category
        ORDER BY total DESC
    """)
    category_results = cursor.fetchall()
    
    print(f"\n📊 TRANSACTION SUMMARY BY CATEGORY:")
    for row in category_results:
        category = row['category']
        count = row['count']
        total = row['total']
        credits = row['credits']
        debits = row['debits']
        print(f"   {category.title():15} | {count:3} txns | ${total:>10,.2f} | Credits: ${credits:>8,.2f} | Debits: ${debits:>8,.2f}")
    
    conn.close()
    
    print(f"\n💡 TIP: Explore more data using:")
    print(f"   - Web Interface: python ../web_browser.py")
    print(f"   - SQLite CLI: sqlite3 ../data/example_complete_demo.db")
    print(f"   - Custom queries with DatabaseManager class")


def main():
    """Main function - demonstrate SyFi AI capabilities."""
    try:
        # Step 1: Natural language parsing demo
        demo_natural_language_parsing()
        
        # Step 2: Realistic banking data generation demo
        realistic_banking_data_demo()
        
        print("\n\n🚀 Next Steps:")
        print("1. Use ProfileBuilder for more complex scenarios")
        print("2. Explore different profile templates") 
        print("3. Export data in different formats")
        print("4. Run web interface: python web_browser.py")
        print("\nFor more information, see README.md and docs/")
        
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

def realistic_banking_data_demo():
    """Run the complete SyFi AI banking data generation workflow."""
    
    print("🚀 SyFi AI Complete Banking Data Generation Example")
    print("="*55)
    print("Using ProfileBuilder and BankingDataGenerator classes")
    
    # Setup database (relative to project root)
    project_root = Path(__file__).parent.parent
    db_path = project_root / "data" / "example_complete_demo.db"
    (project_root / "data").mkdir(exist_ok=True)
    
    # Remove existing database to ensure fresh schema
    if db_path.exists():
        db_path.unlink()
    
    db_manager = DatabaseManager(db_path)
    db_manager.initialize_schema()
    
    print(f"📁 Database initialized: {db_path}")
    
    # Step 1: Create profile template using built-in template
    print(f"\n📝 STEP 1: Creating Profile Template")
    template = create_young_professional_template()
    print(f"✅ Created Profile Template: {template.name}")
    print(f"   ID: {template.template_id}")
    
    # Step 2: Use ProfileBuilder to generate profiles from template  
    print(f"\n👥 STEP 2: Using ProfileBuilder to Generate Profiles")
    profile_names = [
        "The Johnson Family",
        "The Garcia Household", 
        "The Chen Family"
    ]
    
    profiles = []
    for i, name in enumerate(profile_names, 1):
        # Create ProfileBuilder with unique seed for each family
        builder = ProfileBuilder(db_manager, seed=1000 + i)
        
        # Build profile from template
        profile = builder.build_profile(template, name)
        profiles.append(profile)
        
        print(f"✅ Built Profile: {profile.name}")
        print(f"   ID: {profile.profile_id}")
        print(f"   Household Income: ${profile.household_income:,}")
        print(f"   Members: {profile.total_members} total, {profile.banking_members} banking")
    
    # Step 3: Use BankingDataGenerator to create banking data
    print(f"\n🏦 STEP 3: Using BankingDataGenerator for Banking Data (Jan 2025)")
    
    # Create data generator
    data_generator = BankingDataGenerator(db_manager)
    
    # Generate banking data for January 2025
    start_date = date(2025, 1, 1)
    end_date = date(2025, 1, 31)
    
    results = []
    for profile in profiles:
        result = data_generator.generate_banking_data(profile, start_date, end_date)
        results.append(result)
        
        print(f"✅ Generated Banking Data for '{profile.name}':")
        print(f"   Customers: {len(result['customers'])}")
        print(f"   Accounts: {len(result['accounts'])}")
        print(f"   Transactions: {len(result['transactions'])}")
    
    # Step 4: Generate summary report
    generate_summary_report(results, db_path)
    
    # Step 5: Save profiles for reference
    profiles_data = {
        "template": template.to_dict(),
        "profiles": [profile.to_dict() for profile in profiles]
    }
    
    profiles_file = project_root / "data" / "example_profiles.json"
    with open(profiles_file, 'w') as f:
        json.dump(profiles_data, f, indent=2, default=str)
    
    print(f"💾 Profiles saved to: {profiles_file}")
    
    # Step 6: Query and display sample data
    print(f"\n🔍 STEP 6: Sample Data Queries")
    query_sample_data(db_manager)


if __name__ == "__main__":
    main()