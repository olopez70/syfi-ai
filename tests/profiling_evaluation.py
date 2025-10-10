#!/usr/bin/env python3
"""
Test script to evaluate ydata-profiling with SyFi banking data.
"""

import sqlite3
import pandas as pd
from ydata_profiling import ProfileReport
from pathlib import Path

def test_ydata_profiling():
    """Test ydata-profiling with SyFi banking data."""
    
    # Connect to database
    db_path = "../data/profile_test.db"
    if not Path(db_path).exists():
        db_path = "./profile_test.db"  # Fallback
        if not Path(db_path).exists():
            print(f"Database not found in ../data/ or current directory. Please run the CLI to create sample data first.")
            return
    
    conn = sqlite3.connect(db_path)
    
    # Load customers data
    customers_df = pd.read_sql_query("""
        SELECT customer_id, first_name, last_name, email, phone, 
               date_of_birth, address, city, state, zip_code,
               household_size, num_adults, num_children, num_pets,
               household_income, employment_status, marital_status,
               profile_description, created_date
        FROM customers
    """, conn)
    
    # Load accounts data
    accounts_df = pd.read_sql_query("""
        SELECT account_id, customer_id, account_number, account_type,
               balance, available_balance, currency, created_date,
               is_active, interest_rate, credit_limit
        FROM accounts
    """, conn)
    
    # Load transactions if any exist
    transactions_df = pd.read_sql_query("""
        SELECT transaction_id, account_id, transaction_type, amount,
               currency, description, category, merchant_name,
               merchant_category, transaction_date, posted_date,
               reference_number, balance_after
        FROM transactions
        LIMIT 1000
    """, conn)
    
    conn.close()
    
    print("=== YDATA-PROFILING EVALUATION ===")
    print(f"Customers: {len(customers_df)} rows")
    print(f"Accounts: {len(accounts_df)} rows")
    print(f"Transactions: {len(transactions_df)} rows")
    
    # Test with customers data (most comprehensive)
    if not customers_df.empty:
        print("\nGenerating profile report for customers table...")
        
        # Configure profiling (minimal to avoid heavy computation)
        profile = ProfileReport(
            customers_df,
            title="SyFi Banking - Customers Profile",
            minimal=True,  # Faster generation
            explorative=False  # Disable heavy computations
        )
        
        # Generate HTML report
        profile.to_file("./exports/customers_profile_report.html")
        print("✅ Customer profile report saved to: ./exports/customers_profile_report.html")
        
        # Get statistics
        stats = profile.get_description()
        print(f"\nProfile Statistics:")
        print(f"  Variables: {stats.get('n_variables', 'N/A')}")
        print(f"  Observations: {stats.get('n_observations', 'N/A')}")
        print(f"  Missing cells: {stats.get('n_cells_missing', 'N/A')}")
        print(f"  Duplicate rows: {stats.get('n_duplicate_rows', 'N/A')}")
        
        # Sample variable insights
        if hasattr(profile, 'get_variables'):
            variables = profile.get_variables()
            print(f"\nVariable insights available for: {list(variables.keys())[:5]}...")
    
    # Test with accounts data
    if not accounts_df.empty:
        print("\nGenerating profile report for accounts table...")
        accounts_profile = ProfileReport(
            accounts_df,
            title="SyFi Banking - Accounts Profile",
            minimal=True
        )
        accounts_profile.to_file("./exports/accounts_profile_report.html")
        print("✅ Account profile report saved to: ./exports/accounts_profile_report.html")
    
    print("\n=== YDATA-PROFILING CAPABILITIES ===")
    print("✅ Automatic data type detection")
    print("✅ Missing value analysis")
    print("✅ Duplicate detection")
    print("✅ Statistical summaries")
    print("✅ Distribution visualizations")
    print("✅ Correlation analysis")
    print("✅ HTML report generation")
    print("✅ Configurable detail levels")

if __name__ == "__main__":
    test_ydata_profiling()