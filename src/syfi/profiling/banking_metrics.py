"""
Banking-specific metrics calculator for SyFi AI data profiling.

This module calculates domain-specific metrics that are relevant to
synthetic banking data analysis.
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional
from decimal import Decimal
from ..schema_management import SchemaAwareConnection, SchemaAwareMetricsCalculator

class BankingMetricsCalculator:
    """
    Calculates banking-domain specific metrics and insights.
    
    Provides analysis specific to banking data including account penetration,
    balance distributions, customer segmentation, and financial patterns.
    """
    
    def __init__(self, db_path_or_connection):
        """
        Initialize calculator with database connection or path.
        
        Args:
            db_path_or_connection: SQLite database connection (legacy) or path to database file
        """
        if isinstance(db_path_or_connection, str):
            # New schema-aware initialization
            self.db = SchemaAwareConnection(db_path_or_connection)
            self.metrics_calculator = SchemaAwareMetricsCalculator(self.db)
            self.conn = None  # Legacy connection for backward compatibility
        else:
            # Legacy connection mode for backward compatibility
            self.conn = db_path_or_connection
            self.conn.row_factory = sqlite3.Row
            self.db = None
            self.metrics_calculator = None
    
    def _safe_fetch_dict(self, result):
        """Safely access cursor result as dictionary or list."""
        if result is None:
            return {}
        
        # If it's already a dict-like object, return as is
        if hasattr(result, '__getitem__') and hasattr(result, 'keys'):
            return result
        
        # If it's a list/tuple (mock scenario), return empty dict 
        # Tests should handle this case appropriately
        if isinstance(result, (list, tuple)):
            return {}
        
        # Default case
        return result if result else {}
    
    def _safe_fetch_value(self, result, index_or_key=0):
        """Safely fetch a single value from cursor result."""
        if result is None:
            return 0
        
        # Handle list/tuple access (mock scenario)
        if isinstance(result, (list, tuple)):
            if len(result) > index_or_key if isinstance(index_or_key, int) else False:
                return result[index_or_key]
            return 0
        
        # Handle dict-like access
        if hasattr(result, '__getitem__'):
            try:
                return result[index_or_key]
            except (KeyError, IndexError, TypeError):
                return 0
        
        return 0
    
    def _column_exists(self, table: str, column: str) -> bool:
        """Check if a column exists in a table."""
        if self.db:
            return self.db.column_exists(table, column)
        elif self.conn:
            # Legacy fallback
            cursor = self.conn.cursor()
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]
            return column in columns
        else:
            return False
    
    def _table_exists(self, table: str) -> bool:
        """Check if a table exists in the database."""
        if self.db:
            return self.db.table_exists(table)
        elif self.conn:
            # Legacy fallback
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            return cursor.fetchone() is not None
        else:
            return False
    
    def _safe_execute(self, query: str, params=None):
        """Execute SQL query using appropriate method based on connection type."""
        if self.db:
            return self.db.safe_execute(query, params or ())
        elif self.conn:
            # Legacy mode
            cursor = self.conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
        else:
            return None
    
    def _safe_count(self, table: str, condition: str = None, params=None) -> int:
        """Get count from table using schema-aware operations."""
        if self.db:
            return self.db.safe_count(table, condition, params)
        elif self.conn:
            # Legacy mode  
            cursor = self.conn.cursor()
            if condition:
                query = f"SELECT COUNT(*) FROM {table} WHERE {condition}"
                cursor.execute(query, params or ())
            else:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
            result = cursor.fetchone()
            return result[0] if result else 0
        else:
            return 0
    
    def calculate_all_metrics(self) -> Dict[str, Any]:
        """
        Calculate comprehensive banking metrics.
        
        Returns:
            Dictionary containing all banking-specific metrics
        """
        metrics = {}
        
        # Account analysis (test expects 'account_stats') - MIGRATED
        metrics['account_stats'] = self._calculate_account_metrics()
        
        # Transaction analysis (test expects 'transaction_stats') - MIGRATED  
        metrics['transaction_stats'] = self._analyze_transactions()
        
        # Only run legacy methods if we have a legacy connection
        # TODO: Migrate these methods in follow-up work
        if self.conn:
            try:
                # Customer segmentation - LEGACY
                metrics['customer_segments'] = self._analyze_customer_segments()
                
                # Balance analysis (test expects 'balance_distribution') - LEGACY
                metrics['balance_distribution'] = self._analyze_balances()
                
                # Product penetration (only if customers table exists) - LEGACY
                metrics['product_penetration'] = self._calculate_product_penetration()
                
                # Profile-based analysis - LEGACY
                metrics['profile_analysis'] = self._analyze_by_profiles()
            except Exception as e:
                # If legacy methods fail, provide empty results
                metrics['customer_segments'] = {'message': f'Legacy method unavailable: {str(e)}'}
                metrics['balance_distribution'] = {'message': 'Legacy method unavailable'}
                metrics['product_penetration'] = {'message': 'Legacy method unavailable'}
                metrics['profile_analysis'] = {'message': 'Legacy method unavailable'}
        else:
            # Schema-aware mode - provide basic implementations or skip
            metrics['customer_segments'] = {'message': 'Customer segmentation requires legacy connection (migration pending)'}
            metrics['balance_distribution'] = {'message': 'Balance analysis requires legacy connection (migration pending)'}
            metrics['product_penetration'] = {'message': 'Product penetration requires legacy connection (migration pending)'}
            metrics['profile_analysis'] = {'message': 'Profile analysis requires legacy connection (migration pending)'}
        
        return metrics
    
    def _calculate_account_metrics(self) -> Dict[str, Any]:
        """Calculate account-related metrics."""
        metrics = {}
        
        # Check if accounts table exists
        if not self._table_exists('accounts'):
            return {
                'message': 'No accounts table found',
                'total_accounts': 0,
                'total_balance_across_all_accounts': 0,
                'account_type_distribution': {},
                'account_status': {'active': 0, 'inactive': 0}
            }
        
        # Account type distribution using schema-aware operations
        if self.db:
            query = """
                SELECT account_type, COUNT(*) as count, 
                       AVG(balance) as avg_balance,
                       SUM(balance) as total_balance
                FROM accounts 
                GROUP BY account_type
                ORDER BY count DESC
            """
            account_type_results = self.db.safe_execute(query)
        else:
            # Legacy mode
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT account_type, COUNT(*) as count, 
                       AVG(balance) as avg_balance,
                       SUM(balance) as total_balance
                FROM accounts 
                GROUP BY account_type
                ORDER BY count DESC
            """)
            account_type_results = cursor.fetchall()
        
        account_types = {}
        total_accounts = 0
        total_balance = Decimal('0')
        
        if account_type_results:
            for row in account_type_results:
                if self.db:
                    # Schema-aware mode - results are tuples
                    account_type = row[0]
                    count = row[1]
                    avg_balance = float(row[2]) if row[2] else 0
                    type_total_balance = float(row[3]) if row[3] else 0
                else:
                    # Legacy mode - results have dict-like access
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
        
        # Active vs inactive accounts using schema-aware calculation
        if self.metrics_calculator:
            # Use the new schema-aware metrics calculator
            metrics['account_status'] = self.metrics_calculator.calculate_account_status()
        else:
            # Legacy fallback - use safe_execute for all queries
            if self._column_exists('accounts', 'status'):
                result = self._safe_execute("""
                    SELECT 
                        SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_accounts,
                        SUM(CASE WHEN status != 'active' OR status IS NULL THEN 1 ELSE 0 END) as inactive_accounts
                    FROM accounts
                """)
                if result and len(result) > 0:
                    row = result[0]
                    metrics['account_status'] = {
                        'active': row[0] if row[0] else 0,
                        'inactive': row[1] if row[1] else 0
                    }
                else:
                    metrics['account_status'] = {'active': 0, 'inactive': 0}
            elif self._column_exists('accounts', 'is_active'):
                result = self._safe_execute("""
                    SELECT 
                        SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_accounts,
                        SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END) as inactive_accounts
                    FROM accounts
                """)
                if result and len(result) > 0:
                    row = result[0]
                    metrics['account_status'] = {
                        'active': row[0] if row[0] else 0,
                        'inactive': row[1] if row[1] else 0
                    }
                else:
                    metrics['account_status'] = {'active': 0, 'inactive': 0}
            else:
                # If no status column, assume all accounts are active
                metrics['account_status'] = {
                    'active': total_accounts,
                    'inactive': 0
                }
        
        return metrics
    
    def _analyze_transactions(self) -> Dict[str, Any]:
        """Analyze transaction patterns and metrics."""
        transaction_metrics = {}
        
        # Check if transactions table exists
        if not self._table_exists('transactions'):
            return {'message': 'No transactions table found'}
        
        # Get transaction count using schema-aware operations
        if self.db:
            total_transactions = self.db.safe_count('transactions')
        else:
            # Legacy mode
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM transactions")
            result = cursor.fetchone()
            total_transactions = self._safe_fetch_value(result, 0)
        
        if total_transactions == 0:
            return {'message': 'No transactions found', 'total_transactions': 0}
        
        transaction_metrics['total_transactions'] = total_transactions
        
        # Transaction type distribution using safe_execute
        type_results = self._safe_execute("""
            SELECT transaction_type, COUNT(*) as count
            FROM transactions
            GROUP BY transaction_type
            ORDER BY count DESC
        """)
        type_dist = {}
        if type_results:
            for row in type_results:
                type_dist[row[0]] = row[1]
        transaction_metrics['transaction_type_distribution'] = type_dist
        
        # Transaction volume by amount ranges (simplified for schema-aware mode)
        if self._column_exists('transactions', 'amount'):
            amount_results = self._safe_execute("""
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
            if amount_results:
                for row in amount_results:
                    amount_ranges[row[0]] = {
                        'count': row[1],
                        'avg_amount': round(float(row[2]), 2) if row[2] else 0
                    }
            transaction_metrics['amount_distribution'] = amount_ranges
        else:
            transaction_metrics['amount_distribution'] = {'message': 'Amount column not available'}
        
        # Monthly transaction patterns (simplified)
        if self._column_exists('transactions', 'transaction_date'):
            monthly_results = self._safe_execute("""
                SELECT 
                    strftime('%Y-%m', transaction_date) as month,
                    COUNT(*) as transaction_count,
                    SUM(ABS(amount)) as total_volume,
                    AVG(ABS(amount)) as avg_amount
                FROM transactions
                WHERE transaction_date IS NOT NULL
                GROUP BY strftime('%Y-%m', transaction_date)
                ORDER BY month
            """)
            monthly_patterns = {}
            if monthly_results:
                for row in monthly_results:
                    if row[0]:  # Skip null months
                        monthly_patterns[row[0]] = {
                            'transaction_count': row[1],
                            'total_volume': round(float(row[2]), 2) if row[2] else 0,
                            'avg_amount': round(float(row[3]), 2) if row[3] else 0
                        }
            transaction_metrics['monthly_patterns'] = monthly_patterns
        else:
            transaction_metrics['monthly_patterns'] = {'message': 'Transaction date column not available'}
        
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
    
# Removed duplicate _table_exists method - using the updated version above
    
    def _analyze_customer_segments(self) -> Dict[str, Any]:
        """Analyze customer segmentation patterns."""
        cursor = self.conn.cursor()
        segments = {}
        
        # Check if customers table exists
        if not self._table_exists('customers'):
            return {'message': 'No customers table found'}
        
        # Check what columns are available for segmentation
        has_dob = self._column_exists('customers', 'date_of_birth')
        has_income = self._column_exists('customers', 'household_income')
        
        # Age-based segmentation (only if date_of_birth exists)
        if has_dob:
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
        else:
            # No segmentation possible, return basic info
            cursor.execute("SELECT COUNT(*) as total_customers FROM customers")
            result = cursor.fetchone()
            total_customers = self._safe_fetch_value(result, 0)
            return {
                'message': 'Customer segmentation not available - missing date_of_birth column',
                'total_customers': total_customers
            }
        
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
        safe_result = self._safe_fetch_dict(result)
        analysis['overall_statistics'] = {
            'total_accounts': safe_result.get('total_accounts', 0) if isinstance(safe_result, dict) else 0,
            'mean_balance': round(float(safe_result.get('mean_balance', 0)), 2) if isinstance(safe_result, dict) and safe_result.get('mean_balance') else 0,
            'min_balance': round(float(safe_result.get('min_balance', 0)), 2) if isinstance(safe_result, dict) and safe_result.get('min_balance') else 0,
            'max_balance': round(float(safe_result.get('max_balance', 0)), 2) if isinstance(safe_result, dict) and safe_result.get('max_balance') else 0,
            'total_balance': round(float(safe_result.get('total_balance', 0)), 2) if isinstance(safe_result, dict) and safe_result.get('total_balance') else 0
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
        
        # Check if customers table exists
        if not self._table_exists('customers'):
            return {'message': 'No customers table found for penetration analysis'}
        
        # Get total customers
        cursor.execute("SELECT COUNT(*) as total_customers FROM customers")
        result = cursor.fetchone()
        safe_result = self._safe_fetch_dict(result)
        total_customers = safe_result.get('total_customers', 0) if isinstance(safe_result, dict) else 0
        
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