#!/usr/bin/env python3
"""
SyFi AI - Multi-Entity Banking Data Generation Example

This example demonstrates generating realistic banking data for diverse entity types:
(a) Middle income suburban family
(b) Small local restaurant business  
(c) Local supermarket
(d) Large non-profit organization

Each entity type has unique transaction patterns, account structures, and financial behaviors
that reflect real-world banking scenarios developers would encounter.

Run with: python multi_entity_banking_demo.py
"""

import sys
from pathlib import Path
from datetime import date, datetime
import json
from decimal import Decimal

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from syfi.database import DatabaseManager
from syfi.profile_builder import BankingDataGenerator
from syfi.models import ProfileTemplate, TransactionProfile

# Import our enhanced ProfileBuilder
sys.path.insert(0, str(Path(__file__).parent))
from enhanced_profile_builder import EnhancedProfileBuilder


def create_suburban_family_template():
    """Create profile template for middle income suburban family."""
    
    return ProfileTemplate(
        name="Middle Income Suburban Family",
        description="""
        Middle-class suburban family with two working parents and 2-3 children. 
        Primary earner works in professional services earning $60,000-70,000 annually, 
        secondary earner works part-time or full-time earning $25,000-40,000. 
        They own a suburban home with a mortgage, have regular childcare expenses, 
        shop weekly at grocery stores and big-box retailers, drive two cars requiring 
        regular gas purchases, and maintain a moderate entertainment and dining budget. 
        They use checking/savings accounts and credit cards responsibly for family expenses.
        """,
        category="household",
        complexity_level="medium",
        created_by="Multi-Entity Demo",
        tags=["suburban", "family", "middle-income", "homeowners", "children"]
    )


def create_small_restaurant_template():
    """Create profile template for small local restaurant business."""
    
    return ProfileTemplate(
        name="Small Local Restaurant",
        description="""
        Family-owned casual dining restaurant serving lunch and dinner. 
        Generates $15,000-25,000 monthly revenue through dine-in, takeout, and delivery orders.
        Daily cash deposits and credit card settlements. Weekly payments to food distributors, 
        produce suppliers, and beverage companies. Bi-weekly payroll for 8-12 staff members 
        including servers, cooks, and management. Monthly fixed expenses include commercial rent, 
        utilities, business insurance, and equipment leases. Seasonal variations with higher 
        revenue during holidays and summer months. Uses business checking, savings, and credit accounts.
        """,
        category="business",
        complexity_level="medium",
        created_by="Multi-Entity Demo", 
        tags=["restaurant", "small-business", "food-service", "retail", "hospitality"]
    )


def create_supermarket_template():
    """Create profile template for local supermarket business."""
    
    return ProfileTemplate(
        name="Local Supermarket",
        description="""
        Independent supermarket serving a local community with 15,000-20,000 square feet of retail space.
        Annual revenue of $8-12 million through grocery sales, fresh produce, deli, bakery, and pharmacy services.
        Daily credit card settlements and cash deposits from high-volume transactions. 
        Multiple daily deliveries from food distributors, produce wholesalers, dairy companies, 
        and beverage suppliers. Large weekly inventory purchases from major distributors. 
        Bi-weekly payroll for 35-50 employees including cashiers, stockers, department managers, 
        and administrative staff. Significant monthly expenses for commercial lease, utilities 
        (high electricity for refrigeration), business insurance, and equipment maintenance. 
        Uses multiple business accounts for operations, payroll, and vendor payments.
        """,
        category="business",
        complexity_level="high",
        created_by="Multi-Entity Demo",
        tags=["supermarket", "retail", "grocery", "high-volume", "community-business"]
    )


def create_nonprofit_template():
    """Create profile template for large non-profit organization."""
    
    return ProfileTemplate(
        name="Large Non-Profit Organization", 
        description="""
        Established community-focused non-profit organization with 25+ years of service.
        Annual operating budget of $2-4 million supported by federal/state grants, 
        foundation grants, corporate sponsorships, individual donations, and fundraising events.
        Serves 5,000+ community members annually through education, health, and social programs.
        Staff of 35-50 full-time employees plus part-time and contract workers.
        Monthly payroll, program expenses, administrative costs, and office operations.
        Quarterly grant disbursements and major fundraising events. Maintains separate 
        accounts for restricted funds, general operations, payroll, and reserve funds.
        Strong financial oversight with annual audits and board governance.
        """,
        category="organization",
        complexity_level="high", 
        created_by="Multi-Entity Demo",
        tags=["nonprofit", "community-service", "grants", "donations", "social-impact"]
    )


def generate_entity_banking_data(db_manager, template, entity_name, entity_index=0, profiles_per_template=5):
    """Generate banking data for a specific entity type with multiple profiles."""
    
    print(f"\n🏢 GENERATING DATA FOR: {entity_name} ({profiles_per_template} profiles)")
    print("=" * 60)
    
    # Initialize aggregated results
    all_results = {
        'customers': [],
        'accounts': [],
        'transactions': [],
        'profiles': []
    }
    
    # Generate multiple profiles for this entity type
    for profile_index in range(profiles_per_template):
        print(f"\n   � Creating profile {profile_index + 1}/{profiles_per_template}...")
        
        # Use unique seed for each profile to ensure diverse names and data
        unique_seed = 1000 + (entity_index * 100) + (profile_index * 10) + hash(entity_name) % 100
        builder = EnhancedProfileBuilder(db_manager=db_manager, seed=unique_seed)
        profile = builder.build_profile(template, entity_name)  # Let the builder create unique variations
        
        print(f"      ✅ Profile Created: {profile.name}")
        print(f"         Annual Revenue/Income: ${profile.household_income:,}")
        print(f"         Profile ID: {profile.profile_id}")
        
        # Generate banking data for full quarter (January-March 2025)
        generator = BankingDataGenerator(db_manager)
        profile_results = generator.generate_banking_data(
            profile=profile,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31)  # Full quarter for better business patterns
        )
        
        print(f"      ✅ Generated Banking Data:")
        print(f"         Customers: {len(profile_results['customers'])}")
        print(f"         Accounts: {len(profile_results['accounts'])}")
        print(f"         Transactions: {len(profile_results['transactions'])}")
        
        # Aggregate results
        all_results['customers'].extend(profile_results['customers'])
        all_results['accounts'].extend(profile_results['accounts'])
        all_results['transactions'].extend(profile_results['transactions'])
        all_results['profiles'].append(profile)
    
    # Calculate total transaction volume
    total_volume = sum(abs(txn.amount) for txn in all_results['transactions'])
    print(f"\n✅ SUMMARY FOR {entity_name}:")
    print(f"   Total Profiles: {len(all_results['profiles'])}")
    print(f"   Total Customers: {len(all_results['customers'])}")
    print(f"   Total Accounts: {len(all_results['accounts'])}")
    print(f"   Total Transactions: {len(all_results['transactions'])}")
    print(f"   Total Volume: ${total_volume:,.2f}")
    
    # Get transaction breakdown by category from generated data
    from collections import defaultdict
    category_summary = defaultdict(lambda: {'count': 0, 'total': 0, 'credits': 0, 'debits': 0})
    
    for txn in all_results['transactions']:
        category = txn.category
        category_summary[category]['count'] += 1
        category_summary[category]['total'] += abs(txn.amount)
        if txn.amount > 0:
            category_summary[category]['credits'] += txn.amount
        else:
            category_summary[category]['debits'] += abs(txn.amount)
    
    if category_summary:
        print(f"\n📊 Transaction Categories for {entity_name}:")
        # Sort by transaction count, descending
        sorted_categories = sorted(category_summary.items(), key=lambda x: x[1]['count'], reverse=True)
        for category, stats in sorted_categories[:8]:  # Top 8 categories
            category_name = category.value if hasattr(category, 'value') else str(category)
            print(f"   {category_name.title():<15} | {stats['count']:>3} txns | ${stats['total']:>10,.0f} | Credits: ${stats['credits']:>8,.0f} | Debits: ${stats['debits']:>8,.0f}")
    
    return all_results


def main():
    """Generate banking data for four different entity types."""
    
    print("🏦 SyFi AI - Multi-Entity Banking Data Generation")
    print("=" * 65)
    print("Creating realistic banking datasets for diverse entity types:\n")
    print("(a) Middle income suburban family (5 profiles)")
    print("(b) Small local restaurant business (5 profiles)")  
    print("(c) Local supermarket (5 profiles)")
    print("(d) Large non-profit organization (5 profiles)")
    print("\nEach entity demonstrates unique transaction patterns and financial behaviors.")
    print("Total: 20 profiles across 4 entity templates.")
    
    # Setup database
    db_path = "data/multi_entity_demo.db"
    db_manager = DatabaseManager(db_path)
    db_manager.initialize_schema()
    
    print(f"\n📁 Database initialized: {db_path}")
    
    try:
        # Create profile templates
        templates = [
            (create_suburban_family_template(), "Middle Income Suburban Family"),
            (create_small_restaurant_template(), "Small Local Restaurant"),  
            (create_supermarket_template(), "Local Supermarket"),
            (create_nonprofit_template(), "Large Non-Profit Organization")
        ]
        
        all_results = []
        
        # Generate banking data for each entity type (5 profiles per template)
        profiles_per_template = 5
        for entity_index, (template, entity_name) in enumerate(templates):
            results = generate_entity_banking_data(db_manager, template, entity_name, entity_index, profiles_per_template)
            all_results.append((entity_name, results))
        
        # Generate comprehensive summary
        print(f"\n" + "=" * 80)
        print("                    MULTI-ENTITY BANKING DATA SUMMARY")
        print("=" * 80)
        
        total_customers = sum(len(r[1]['customers']) for r in all_results)
        total_accounts = sum(len(r[1]['accounts']) for r in all_results) 
        total_transactions = sum(len(r[1]['transactions']) for r in all_results)
        total_volume = sum(sum(abs(txn.amount) for txn in r[1]['transactions']) for r in all_results)
        
        total_profiles = sum(len(r[1].get('profiles', [])) for r in all_results)
        
        print(f"\n📊 AGGREGATE STATISTICS:")
        print(f"   Database: {db_path}")
        print(f"   Entity Types: 4 different templates")
        print(f"   Profiles per Template: {profiles_per_template}")
        print(f"   Total Profiles: {total_profiles}")
        print(f"   Total Customers: {total_customers}")
        print(f"   Total Accounts: {total_accounts}")
        print(f"   Total Transactions: {total_transactions}")
        print(f"   Total Transaction Volume: ${total_volume:,.2f}")
        print(f"   Date Range: January 1 - March 31, 2025 (Q1)")
        
        print(f"\n🏢 ENTITY BREAKDOWN:")
        for entity_name, results in all_results:
            entity_volume = sum(abs(txn.amount) for txn in results['transactions'])
            print(f"   {entity_name}:")
            print(f"      Customers: {len(results['customers'])}")
            print(f"      Accounts: {len(results['accounts'])}")
            print(f"      Transactions: {len(results['transactions'])}")
            print(f"      Volume: ${entity_volume:,.2f}")
        
        # Show sample transactions from the last entity generated
        if all_results:
            last_entity_name, last_results = all_results[-1]
            sample_transactions = last_results['transactions'][:10]  # First 10 transactions
            if sample_transactions:
                print(f"\n💰 SAMPLE TRANSACTIONS (from {last_entity_name}):")
                for txn in sample_transactions:
                    amount_str = f"+${txn.amount:.2f}" if txn.amount > 0 else f"-${abs(txn.amount):.2f}"
                    print(f"   {txn.transaction_date} | {amount_str:>12} | {txn.description[:50]}")
        
        print(f"\n✅ Multi-Entity Banking Data Generation Complete!")
        print(f"\n🎯 USE CASES FOR THIS DATA:")
        print(f"   • Test banking applications with diverse customer types")
        print(f"   • Demo financial analytics across different sectors")  
        print(f"   • Validate transaction processing systems")
        print(f"   • Train machine learning models on varied financial patterns")
        print(f"   • Create realistic test environments for fintech applications")
        
        print(f"\n💡 EXPLORE THE DATA:")
        print(f"   • Web Interface: python web_browser.py")
        print(f"   • SQLite CLI: sqlite3 {db_path}")
        print(f"   • Custom queries with DatabaseManager class")
        print(f"   • Export data in various formats for external tools")
        
    except Exception as e:
        print(f"\n❌ Error generating multi-entity banking data: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db_manager.close()
        print(f"\n💾 Database connection closed")


if __name__ == "__main__":
    main()