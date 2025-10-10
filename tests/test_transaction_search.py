#!/usr/bin/env python3
"""
Test script for transaction-based customer search functionality
"""

import sqlite3
from pathlib import Path
import pytest

def test_transaction_search():
    """Test the transaction search functionality."""
    
    # Test database connection
    db_path = Path("data/syfi_bank3.db")
    if not db_path.exists():
        db_path = Path("syfi_bank3.db")  # Fallback
        if not db_path.exists():
            pytest.skip("Database syfi_bank3.db not found - this test requires pre-existing data")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check transaction data
    print("🔍 Checking transaction data...")
    cursor.execute("SELECT COUNT(*) FROM transactions")
    tx_count = cursor.fetchone()[0]
    print(f"   Total transactions: {tx_count}")
    
    if tx_count == 0:
        print("❌ No transactions found in database")
        conn.close()
        assert False, "No transactions found in database"
    
    # Test basic aggregate query
    print("\n📊 Testing transaction aggregates...")
    query = """
        SELECT 
            c.customer_id,
            c.first_name,
            c.last_name,
            COUNT(t.transaction_id) as tx_count,
            COALESCE(SUM(t.amount), 0) as tx_net_amount
        FROM customers c
        JOIN accounts a ON c.customer_id = a.customer_id
        LEFT JOIN transactions t ON a.account_id = t.account_id
        GROUP BY c.customer_id
        HAVING COUNT(t.transaction_id) > 0
        ORDER BY tx_count DESC
        LIMIT 5
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    print("   Top 5 customers by transaction count:")
    for row in results:
        customer_id, first_name, last_name, tx_count, net_amount = row
        print(f"   • {customer_id}: {first_name} {last_name} - {tx_count} transactions, ${net_amount:.2f} net")
    
    # Test date range filtering
    print("\n📅 Testing date range filtering...")
    cursor.execute("""
        SELECT MIN(DATE(transaction_date)), MAX(DATE(transaction_date))
        FROM transactions
    """)
    date_range = cursor.fetchone()
    print(f"   Transaction date range: {date_range[0]} to {date_range[1]}")
    
    # Test transaction types
    print("\n💳 Testing transaction types...")
    cursor.execute("SELECT DISTINCT transaction_type FROM transactions")
    tx_types = [row[0] for row in cursor.fetchall()]
    print(f"   Available transaction types: {', '.join(tx_types)}")
    
    # Test high-value customers
    print("\n💰 Testing high-value customer search...")
    cursor.execute("""
        SELECT 
            c.customer_id,
            c.first_name,
            c.last_name,
            COUNT(t.transaction_id) as tx_count,
            ABS(SUM(t.amount)) as total_volume
        FROM customers c
        JOIN accounts a ON c.customer_id = a.customer_id
        LEFT JOIN transactions t ON a.account_id = t.account_id
        GROUP BY c.customer_id
        HAVING ABS(SUM(t.amount)) > 1000
        ORDER BY total_volume DESC
        LIMIT 3
    """)
    
    high_value = cursor.fetchall()
    print("   Customers with >$1000 total volume:")
    for row in high_value:
        customer_id, first_name, last_name, tx_count, total_volume = row
        print(f"   • {customer_id}: {first_name} {last_name} - ${total_volume:.2f} total volume")
    
    conn.close()
    print("\n✅ Transaction search functionality test completed!")
    # Test functions should return None for pytest

if __name__ == "__main__":
    test_transaction_search()