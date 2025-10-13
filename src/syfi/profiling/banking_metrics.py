"""
Banking-specific metrics calculator for SyFi AI data profiling.

This module calculates domain-specific metrics that are relevant to
synthetic banking data analysis.
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional
from decimal import Decimal

class BankingMetricsCalculator:
    """
    Calculates banking-domain specific metrics and insights.
    
    Provides analysis specific to banking data including account penetration,
    balance distributions, customer segmentation, and financial patterns.
    """
    
    def __init__(self, conn: sqlite3.Connection):
        """
        Initialize calculator with database connection.
        
        Args:
            conn: SQLite database connection
        """
        self.conn = conn
        self.conn.row_factory = sqlite3.Row
    
    def _column_exists(self, table: str, column: str) -> bool:
        """Check if a column exists in a table."""
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        return column in columns
    
    def calculate_all_metrics(self) -> Dict[str, Any]:
        """
        Calculate comprehensive banking metrics.
        
        Returns:
            Dictionary containing all banking-specific metrics
        """
        metrics = {}
        
        # Account analysis
        metrics['account_metrics'] = self._calculate_account_metrics()
        
        # Transaction analysis
        metrics['transaction_metrics'] = self._analyze_transactions()
        
        # Customer segmentation
        metrics['customer_segments'] = self._analyze_customer_segments()
        
        # Balance analysis
        metrics['balance_analysis'] = self._analyze_balances()
        
        # Product penetration
        metrics['product_penetration'] = self._calculate_product_penetration()
        
        # Profile-based analysis
        metrics['profile_analysis'] = self._analyze_by_profiles()
        
        return metrics
    
    def _calculate_account_metrics(self) -> Dict[str, Any]:
        """Calculate account-related metrics."""
        cursor = self.conn.cursor()
        metrics = {}
        
        # Account type distribution
        cursor.execute("""
            SELECT account_type, COUNT(*) as count, 
                   AVG(balance) as avg_balance,
                   SUM(balance) as total_balance
            FROM accounts 
            GROUP BY account_type
            ORDER BY count DESC
        """)
        
        account_types = {}
        total_accounts = 0
        total_balance = Decimal('0')
        
        for row in cursor.fetchall():
            account_type = row['account_type']
            count = row['count']
            avg_balance = float(row['avg_balance']) if row['avg_balance'] else 0
            type_total_balance = float(row['total_balance']) if row['total_balance'] else 0
            
            account_types[account_type] = {
                'count': count,
                'avg_balance': round(avg_balance, 2),
                'total_balance': round(type_total_balance, 2)
            }
            
            total_accounts += count
            total_balance += Decimal(str(type_total_balance))
        
        # Calculate percentages
        for account_type in account_types:
            account_types[account_type]['percentage'] = round(
                (account_types[account_type]['count'] / total_accounts * 100), 1
            ) if total_accounts > 0 else 0
        
        metrics['account_type_distribution'] = account_types
        metrics['total_accounts'] = total_accounts
        metrics['total_balance_across_all_accounts'] = float(total_balance)
        
        # Active vs inactive accounts
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_accounts,
                SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END) as inactive_accounts
            FROM accounts
        """)
        result = cursor.fetchone()
        metrics['account_status'] = {
            'active': result['active_accounts'] if result['active_accounts'] else 0,
            'inactive': result['inactive_accounts'] if result['inactive_accounts'] else 0
        }
        
        return metrics
    
    def _analyze_transactions(self) -> Dict[str, Any]:
        """Analyze transaction patterns and metrics."""
        cursor = self.conn.cursor()
        transaction_metrics = {}
        
        # Check if transactions table exists
        if not self._table_exists('transactions'):
            return {'message': 'No transactions table found'}
        
        # Get transaction count
        cursor.execute("SELECT COUNT(*) FROM transactions")
        total_transactions = cursor.fetchone()[0]
        
        if total_transactions == 0:
            return {'message': 'No transactions found', 'total_transactions': 0}
        
        transaction_metrics['total_transactions'] = total_transactions
        
        # Transaction type distribution
        cursor.execute("""
            SELECT transaction_type, COUNT(*) as count
            FROM transactions
            GROUP BY transaction_type
            ORDER BY count DESC
        """)
        type_dist = {}
        for row in cursor.fetchall():
            type_dist[row[0]] = row[1]
        transaction_metrics['transaction_type_distribution'] = type_dist
        
        # Transaction volume by amount ranges
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN ABS(amount) < 50 THEN 'Small (<$50)'
                    WHEN ABS(amount) < 200 THEN 'Medium ($50-$200)'
                    WHEN ABS(amount) < 1000 THEN 'Large ($200-$1k)'
                    ELSE 'Very Large ($1k+)'
                END as amount_range,
                COUNT(*) as count,
                AVG(ABS(amount)) as avg_amount
            FROM transactions
            GROUP BY amount_range
            ORDER BY avg_amount
        """)
        amount_ranges = {}
        for row in cursor.fetchall():
            amount_ranges[row[0]] = {
                'count': row[1],
                'avg_amount': round(float(row[2]), 2) if row[2] else 0
            }
        transaction_metrics['amount_distribution'] = amount_ranges
        
        # Monthly transaction patterns
        cursor.execute("""
            SELECT 
                strftime('%Y-%m', transaction_date) as month,
                COUNT(*) as transaction_count,
                SUM(ABS(amount)) as total_volume,
                AVG(ABS(amount)) as avg_amount
            FROM transactions
            GROUP BY strftime('%Y-%m', transaction_date)
            ORDER BY month
        """)
        monthly_patterns = {}
        for row in cursor.fetchall():
            if row[0]:  # Skip null months
                monthly_patterns[row[0]] = {
                    'transaction_count': row[1],
                    'total_volume': round(float(row[2]), 2) if row[2] else 0,
                    'avg_amount': round(float(row[3]), 2) if row[3] else 0
                }
        transaction_metrics['monthly_patterns'] = monthly_patterns
        
        # Account activity analysis
        cursor.execute("""
            SELECT 
                a.account_type,
                COUNT(t.transaction_id) as transaction_count,
                AVG(ABS(t.amount)) as avg_transaction_amount
            FROM accounts a
            LEFT JOIN transactions t ON a.account_id = t.account_id
            GROUP BY a.account_type
            ORDER BY transaction_count DESC
        """)
        account_activity = {}
        for row in cursor.fetchall():
            account_activity[row[0]] = {
                'transaction_count': row[1] if row[1] else 0,
                'avg_transaction_amount': round(float(row[2]), 2) if row[2] else 0
            }
        transaction_metrics['account_activity'] = account_activity
        
        return transaction_metrics
    
    def _table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (table_name,))
        return cursor.fetchone() is not None
    
    def _analyze_customer_segments(self) -> Dict[str, Any]:
        """Analyze customer segmentation patterns."""
        cursor = self.conn.cursor()
        segments = {}
        
        # Age-based segmentation (approximate from birth date)
        has_income = self._column_exists('customers', 'household_income')
        income_col = "AVG(household_income) as avg_income" if has_income else "NULL as avg_income"
        
        # Safe query execution - income_col is predefined constant, not user input
        cursor.execute(f"""
            SELECT 
                CASE 
                    WHEN (julianday('now') - julianday(date_of_birth))/365 < 30 THEN 'Young (18-29)'
                    WHEN (julianday('now') - julianday(date_of_birth))/365 < 50 THEN 'Middle-aged (30-49)'
                    WHEN (julianday('now') - julianday(date_of_birth))/365 < 65 THEN 'Mature (50-64)'
                    ELSE 'Senior (65+)'
                END as age_group,
                COUNT(*) as count,
                {income_col}
            FROM customers 
            WHERE date_of_birth IS NOT NULL
            GROUP BY age_group
            ORDER BY count DESC
        """)  # nosec B608 - income_col is safe constant
        
        age_segments = {}
        for row in cursor.fetchall():
            age_group = row['age_group']
            age_segments[age_group] = {
                'count': row['count'],
                'avg_income': round(float(row['avg_income']), 2) if row['avg_income'] else None
            }
        
        segments['age_distribution'] = age_segments
        
        # Income-based segmentation (only if household_income exists)
        if has_income:
            has_household_size = self._column_exists('customers', 'household_size')
            household_col = "AVG(household_size) as avg_household_size" if has_household_size else "NULL as avg_household_size"
            
            # Safe query execution - household_col is predefined constant
            cursor.execute(f"""
                SELECT 
                    CASE 
                        WHEN household_income < 40000 THEN 'Low Income (<$40k)'
                        WHEN household_income < 80000 THEN 'Middle Income ($40k-$80k)'
                        WHEN household_income < 120000 THEN 'High Income ($80k-$120k)'
                        ELSE 'Very High Income ($120k+)'
                    END as income_bracket,
                    COUNT(*) as count,
                    {household_col}
                FROM customers 
                WHERE household_income IS NOT NULL
                GROUP BY income_bracket
                ORDER BY 
                    CASE 
                        WHEN income_bracket = 'Low Income (<$40k)' THEN 1
                        WHEN income_bracket = 'Middle Income ($40k-$80k)' THEN 2
                        WHEN income_bracket = 'High Income ($80k-$120k)' THEN 3
                        ELSE 4
                    END
            """)  # nosec B608 - household_col is safe constant
            
            income_segments = {}
            for row in cursor.fetchall():
                income_bracket = row['income_bracket']
                income_segments[income_bracket] = {
                    'count': row['count'],
                    'avg_household_size': round(row['avg_household_size'], 1) if row['avg_household_size'] else None
                }
            
            segments['income_distribution'] = income_segments
        else:
            segments['income_distribution'] = {}
        
        # Family composition segments (only if columns exist)
        has_adults = self._column_exists('customers', 'num_adults')
        has_children = self._column_exists('customers', 'num_children')
        
        if has_adults and has_children:
            income_col_family = "AVG(household_income) as avg_income" if has_income else "NULL as avg_income"
            
            # Safe query execution - income_col_family is predefined constant
            cursor.execute(f"""
                SELECT 
                    CASE 
                        WHEN num_children = 0 AND num_adults = 1 THEN 'Single Person'
                        WHEN num_children = 0 AND num_adults = 2 THEN 'Couple (No Children)'
                        WHEN num_children > 0 AND num_adults = 1 THEN 'Single Parent'
                        WHEN num_children > 0 AND num_adults = 2 THEN 'Nuclear Family'
                        WHEN num_adults > 2 THEN 'Extended Family'
                        ELSE 'Other'
                    END as family_type,
                    COUNT(*) as count,
                    {income_col_family}
                FROM customers 
                WHERE num_adults IS NOT NULL AND num_children IS NOT NULL
                GROUP BY family_type
                ORDER BY count DESC
            """)  # nosec B608 - income_col_family is safe constant
            
            family_segments = {}
            for row in cursor.fetchall():
                family_type = row['family_type']
                family_segments[family_type] = {
                    'count': row['count'],
                    'avg_income': round(float(row['avg_income']), 2) if row['avg_income'] else None
                }
            
            segments['family_composition'] = family_segments
        else:
            segments['family_composition'] = {}
        
        return segments
    
    def _analyze_balances(self) -> Dict[str, Any]:
        """Analyze balance distributions and patterns."""
        cursor = self.conn.cursor()
        analysis = {}
        
        # Overall balance statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_accounts,
                AVG(balance) as mean_balance,
                MIN(balance) as min_balance,
                MAX(balance) as max_balance,
                SUM(balance) as total_balance
            FROM accounts 
            WHERE balance IS NOT NULL
        """)
        
        result = cursor.fetchone()
        analysis['overall_statistics'] = {
            'total_accounts': result['total_accounts'],
            'mean_balance': round(float(result['mean_balance']), 2) if result['mean_balance'] else 0,
            'min_balance': round(float(result['min_balance']), 2) if result['min_balance'] else 0,
            'max_balance': round(float(result['max_balance']), 2) if result['max_balance'] else 0,
            'total_balance': round(float(result['total_balance']), 2) if result['total_balance'] else 0
        }
        
        # Balance distribution by ranges
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN balance < 1000 THEN 'Under $1K'
                    WHEN balance < 10000 THEN '$1K - $10K'
                    WHEN balance < 50000 THEN '$10K - $50K'
                    WHEN balance < 100000 THEN '$50K - $100K'
                    ELSE 'Over $100K'
                END as balance_range,
                COUNT(*) as count,
                SUM(balance) as total_in_range
            FROM accounts 
            WHERE balance IS NOT NULL
            GROUP BY balance_range
            ORDER BY 
                CASE 
                    WHEN balance_range = 'Under $1K' THEN 1
                    WHEN balance_range = '$1K - $10K' THEN 2
                    WHEN balance_range = '$10K - $50K' THEN 3
                    WHEN balance_range = '$50K - $100K' THEN 4
                    ELSE 5
                END
        """)
        
        balance_ranges = {}
        total_accounts_with_balance = 0
        
        for row in cursor.fetchall():
            balance_range = row['balance_range']
            count = row['count']
            total_accounts_with_balance += count
            
            balance_ranges[balance_range] = {
                'count': count,
                'total_amount': round(float(row['total_in_range']), 2) if row['total_in_range'] else 0
            }
        
        # Add percentages
        for range_name in balance_ranges:
            balance_ranges[range_name]['percentage'] = round(
                (balance_ranges[range_name]['count'] / total_accounts_with_balance * 100), 1
            ) if total_accounts_with_balance > 0 else 0
        
        analysis['balance_distribution'] = balance_ranges
        
        return analysis
    
    def _calculate_product_penetration(self) -> Dict[str, Any]:
        """Calculate banking product penetration rates."""
        cursor = self.conn.cursor()
        penetration = {}
        
        # Get total customers
        cursor.execute("SELECT COUNT(*) as total_customers FROM customers")
        total_customers = cursor.fetchone()['total_customers']
        
        if total_customers == 0:
            return penetration
        
        # Product penetration by account type
        cursor.execute("""
            SELECT 
                a.account_type,
                COUNT(DISTINCT a.customer_id) as customers_with_product,
                COUNT(a.account_id) as total_accounts_of_type
            FROM accounts a
            GROUP BY a.account_type
        """)
        
        product_penetration = {}
        for row in cursor.fetchall():
            account_type = row['account_type']
            customers_with_product = row['customers_with_product']
            total_accounts = row['total_accounts_of_type']
            
            penetration_rate = round((customers_with_product / total_customers * 100), 1)
            accounts_per_customer = round((total_accounts / customers_with_product), 2) if customers_with_product > 0 else 0
            
            product_penetration[account_type] = {
                'customers_with_product': customers_with_product,
                'penetration_rate_percent': penetration_rate,
                'total_accounts': total_accounts,
                'accounts_per_customer': accounts_per_customer
            }
        
        penetration['by_product_type'] = product_penetration
        
        # Multi-product customers
        cursor.execute("""
            SELECT 
                product_count,
                COUNT(*) as customer_count
            FROM (
                SELECT customer_id, COUNT(DISTINCT account_type) as product_count
                FROM accounts
                GROUP BY customer_id
            ) product_counts
            GROUP BY product_count
            ORDER BY product_count
        """)
        
        multi_product = {}
        for row in cursor.fetchall():
            product_count = row['product_count']
            customer_count = row['customer_count']
            percentage = round((customer_count / total_customers * 100), 1)
            
            multi_product[f"{product_count}_products"] = {
                'customer_count': customer_count,
                'percentage': percentage
            }
        
        penetration['multi_product_analysis'] = multi_product
        
        return penetration
    
    def _analyze_by_profiles(self) -> Dict[str, Any]:
        """Analyze metrics broken down by customer profiles."""
        cursor = self.conn.cursor()
        profile_analysis = {}
        
        # Only analyze profiles if profile_description column exists
        if not self._column_exists('customers', 'profile_description'):
            return {'profile_accounts': {}, 'profile_demographics': {}}
        
        # Profile-based account preferences
        cursor.execute("""
            SELECT 
                c.profile_description,
                a.account_type,
                COUNT(*) as account_count,
                AVG(a.balance) as avg_balance
            FROM customers c
            JOIN accounts a ON c.customer_id = a.customer_id
            WHERE c.profile_description IS NOT NULL
            GROUP BY c.profile_description, a.account_type
            ORDER BY c.profile_description, account_count DESC
        """)
        
        profile_accounts = {}
        for row in cursor.fetchall():
            profile = row['profile_description']
            account_type = row['account_type']
            
            if profile not in profile_accounts:
                profile_accounts[profile] = {}
            
            profile_accounts[profile][account_type] = {
                'count': row['account_count'],
                'avg_balance': round(float(row['avg_balance']), 2) if row['avg_balance'] else 0
            }
        
        profile_analysis['account_preferences_by_profile'] = profile_accounts
        
        # Profile-based demographic analysis
        has_income = self._column_exists('customers', 'household_income')
        has_household_size = self._column_exists('customers', 'household_size')
        has_children = self._column_exists('customers', 'num_children')
        
        income_col = "AVG(household_income) as avg_income" if has_income else "NULL as avg_income"
        household_col = "AVG(household_size) as avg_household_size" if has_household_size else "NULL as avg_household_size"
        children_col = "AVG(num_children) as avg_children" if has_children else "NULL as avg_children"
        
        # Safe query execution - all columns are predefined constants
        cursor.execute(f"""
            SELECT 
                profile_description,
                COUNT(*) as customer_count,
                {income_col},
                {household_col},
                {children_col}
            FROM customers
            WHERE profile_description IS NOT NULL
            GROUP BY profile_description
            ORDER BY customer_count DESC
        """)  # nosec B608 - all column expressions are safe constants
        
        profile_demographics = {}
        for row in cursor.fetchall():
            profile = row['profile_description']
            profile_demographics[profile] = {
                'customer_count': row['customer_count'],
                'avg_income': round(float(row['avg_income']), 2) if row['avg_income'] else None,
                'avg_household_size': round(row['avg_household_size'], 1) if row['avg_household_size'] else None,
                'avg_children': round(row['avg_children'], 1) if row['avg_children'] else None
            }
        
        profile_analysis['demographics_by_profile'] = profile_demographics
        
        return profile_analysis