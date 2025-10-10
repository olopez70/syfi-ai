from flask import Flask, render_template, request, jsonify, session, Response
import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import os
import time
import uuid
from datetime import datetime

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from syfi.generators import CustomerGenerator
from syfi.database import DatabaseManager
from syfi.core.schema_migrations import SchemaManager, BulkGenerationTracker
from syfi.exporters.schema_loader import ExportSchemaLoader
from syfi.exporters.export_engine import ExportEngine

app = Flask(__name__)
app.secret_key = 'syfi_ai_database_browser_secret_key'  # Change this in production

# Global database browser instance
db_browser = None
current_database = None

class DatabaseBrowser:
    """Database browser for SyFi AI SQLite databases."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        
        # Initialize bulk generation support
        schema_manager = SchemaManager(db_path)
        schema_manager.ensure_bulk_generation_support()
        
        # Initialize bulk generation tracker
        self.bulk_tracker = BulkGenerationTracker(db_path)
    
    def get_connection(self):
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def search_customers(self, search_params: Dict[str, str]) -> List[Dict[str, Any]]:
        """Search customers with multiple criteria including transaction aggregates."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if this is a transaction-based search
        has_transaction_filters = any(key.startswith('tx_') for key in search_params.keys())
        
        if has_transaction_filters:
            return self._search_customers_by_transactions(search_params)
        else:
            return self._search_customers_basic(search_params)
    
    def _search_customers_basic(self, search_params: Dict[str, str]) -> List[Dict[str, Any]]:
        """Basic customer search without transaction aggregates."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Build dynamic WHERE clause
        where_conditions = []
        params = []
        
        if search_params.get('customer_id'):
            where_conditions.append("customer_id LIKE ?")
            params.append(f"%{search_params['customer_id']}%")
        
        if search_params.get('first_name'):
            where_conditions.append("first_name LIKE ? COLLATE NOCASE")
            params.append(f"%{search_params['first_name']}%")
        
        if search_params.get('last_name'):
            where_conditions.append("last_name LIKE ? COLLATE NOCASE") 
            params.append(f"%{search_params['last_name']}%")
        
        if search_params.get('company_name'):
            where_conditions.append("company_name LIKE ? COLLATE NOCASE")
            params.append(f"%{search_params['company_name']}%")
        
        if search_params.get('email'):
            where_conditions.append("email LIKE ? COLLATE NOCASE")
            params.append(f"%{search_params['email']}%")
        
        if search_params.get('phone'):
            where_conditions.append("phone LIKE ?")
            params.append(f"%{search_params['phone']}%")
        
        if search_params.get('address'):
            where_conditions.append("address LIKE ? COLLATE NOCASE")
            params.append(f"%{search_params['address']}%")
        
        if search_params.get('profile_description'):
            where_conditions.append("profile_description LIKE ? COLLATE NOCASE")
            params.append(f"%{search_params['profile_description']}%")
        
        if search_params.get('profile_metadata'):
            where_conditions.append("metadata LIKE ? COLLATE NOCASE")
            params.append(f"%{search_params['profile_metadata']}%")
        
        if search_params.get('bulk_generation_id'):
            where_conditions.append("bulk_generation_id LIKE ?")
            params.append(f"%{search_params['bulk_generation_id']}%")
        
        if search_params.get('bulk_generation_label'):
            where_conditions.append("bulk_generation_label LIKE ? COLLATE NOCASE")
            params.append(f"%{search_params['bulk_generation_label']}%")
        
        # Build query
        base_query = """
            SELECT customer_id, first_name, last_name, company_name, email, phone, 
                   address, city, state, profile_description,
                   created_date, metadata, bulk_generation_id, bulk_generation_label
            FROM customers
        """
        
        if where_conditions:
            query = base_query + " WHERE " + " AND ".join(where_conditions)
        else:
            query = base_query
        
        query += " ORDER BY last_name, first_name LIMIT 100"
        
        cursor.execute(query, params)
        results = []
        
        for row in cursor.fetchall():
            results.append({
                'customer_id': row['customer_id'],
                'first_name': row['first_name'],
                'last_name': row['last_name'],
                'email': row['email'],
                'phone': row['phone'],
                'address': row['address'],
                'city': row['city'],
                'state': row['state'],
                'profile_description': row['profile_description'],
                'created_date': row['created_date'],
                'metadata': row['metadata'],
                'bulk_generation_id': row['bulk_generation_id'],
                'bulk_generation_label': row['bulk_generation_label']
            })
        
        conn.close()
        return results
    
    def _search_customers_by_transactions(self, search_params: Dict[str, str]) -> List[Dict[str, Any]]:
        """Search customers based on transaction aggregates."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Build transaction aggregate query
        base_customer_fields = """
            c.customer_id, c.first_name, c.last_name, c.company_name, c.email, c.phone,
            c.address, c.city, c.state, c.profile_description,
            c.created_date, c.metadata, c.bulk_generation_id, c.bulk_generation_label
        """
        
        # Build aggregate SELECT fields
        aggregate_fields = []
        
        # Always include basic transaction stats
        aggregate_fields.extend([
            "COUNT(t.transaction_id) as tx_count",
            "COALESCE(SUM(CASE WHEN t.amount > 0 THEN t.amount ELSE 0 END), 0) as tx_total_credits",
            "COALESCE(SUM(CASE WHEN t.amount < 0 THEN ABS(t.amount) ELSE 0 END), 0) as tx_total_debits", 
            "COALESCE(SUM(t.amount), 0) as tx_net_amount",
            "COALESCE(AVG(ABS(t.amount)), 0) as tx_avg_amount"
        ])
        
        # Build WHERE conditions
        where_conditions = []
        having_conditions = []
        params = []
        
        # Basic customer filters
        basic_filters = ['customer_id', 'first_name', 'last_name', 'company_name', 'email', 'phone', 'address', 'profile_description', 'profile_metadata']
        for filter_name in basic_filters:
            if search_params.get(filter_name):
                if filter_name == 'customer_id':
                    where_conditions.append("c.customer_id LIKE ?")
                elif filter_name == 'profile_metadata':
                    where_conditions.append("c.metadata LIKE ? COLLATE NOCASE")
                else:
                    where_conditions.append(f"c.{filter_name} LIKE ? COLLATE NOCASE")
                params.append(f"%{search_params[filter_name]}%")
        
        # Bulk generation filters
        if search_params.get('bulk_generation_id'):
            where_conditions.append("c.bulk_generation_id LIKE ?")
            params.append(f"%{search_params['bulk_generation_id']}%")
        
        if search_params.get('bulk_generation_label'):
            where_conditions.append("c.bulk_generation_label LIKE ? COLLATE NOCASE")
            params.append(f"%{search_params['bulk_generation_label']}%")
        
        # Transaction date range filters
        if search_params.get('tx_start_date'):
            where_conditions.append("DATE(t.transaction_date) >= ?")
            params.append(search_params['tx_start_date'])
            
        if search_params.get('tx_end_date'):
            where_conditions.append("DATE(t.transaction_date) <= ?")
            params.append(search_params['tx_end_date'])
        
        # Transaction type filter
        if search_params.get('tx_type'):
            where_conditions.append("t.transaction_type = ?")
            params.append(search_params['tx_type'])
        
        # Aggregate amount filters (applied in HAVING clause)
        if search_params.get('tx_total_min'):
            try:
                min_amount = float(search_params['tx_total_min'])
                having_conditions.append("ABS(SUM(t.amount)) >= ?")
                params.append(min_amount)
            except ValueError:
                pass
                
        if search_params.get('tx_total_max'):
            try:
                max_amount = float(search_params['tx_total_max'])
                having_conditions.append("ABS(SUM(t.amount)) <= ?")
                params.append(max_amount)
            except ValueError:
                pass
        
        # Transaction count filters
        if search_params.get('tx_count_min'):
            try:
                min_count = int(search_params['tx_count_min'])
                having_conditions.append("COUNT(t.transaction_id) >= ?")
                params.append(min_count)
            except ValueError:
                pass
                
        if search_params.get('tx_count_max'):
            try:
                max_count = int(search_params['tx_count_max'])
                having_conditions.append("COUNT(t.transaction_id) <= ?")
                params.append(max_count)
            except ValueError:
                pass
        
        # Build the complete query
        query = f"""
            SELECT {base_customer_fields}, {', '.join(aggregate_fields)}
            FROM customers c
            JOIN accounts a ON c.customer_id = a.customer_id
            LEFT JOIN transactions t ON a.account_id = t.account_id
        """
        
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
            
        query += " GROUP BY c.customer_id"
        
        if having_conditions:
            query += " HAVING " + " AND ".join(having_conditions)
        
        # Add sorting - default by transaction volume desc
        sort_by = search_params.get('tx_sort_by', 'tx_net_amount')
        sort_order = search_params.get('tx_sort_order', 'DESC')
        query += f" ORDER BY {sort_by} {sort_order}"
        
        query += " LIMIT 100"
        
        cursor.execute(query, params)
        results = []
        
        for row in cursor.fetchall():
            result = {
                'customer_id': row['customer_id'],
                'first_name': row['first_name'],
                'last_name': row['last_name'],
                'email': row['email'],
                'phone': row['phone'],
                'address': row['address'],
                'city': row['city'],
                'state': row['state'],
                'profile_description': row['profile_description'],
                'created_date': row['created_date'],
                'metadata': row['metadata'],
                # Add transaction aggregates
                'tx_count': row['tx_count'],
                'tx_total_credits': float(row['tx_total_credits']),
                'tx_total_debits': float(row['tx_total_debits']),
                'tx_net_amount': float(row['tx_net_amount']),
                'tx_avg_amount': float(row['tx_avg_amount'])
            }
            results.append(result)
        
        conn.close()
        return results
    
    def get_customer_details(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get complete customer details with accounts."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get customer info
        cursor.execute("""
            SELECT * FROM customers WHERE customer_id = ?
        """, (customer_id,))
        
        customer_row = cursor.fetchone()
        if not customer_row:
            conn.close()
            return None
        
        # Convert to dict and handle all possible columns
        customer = dict(customer_row)
        
        # Get customer accounts (handle different schemas)
        # First check what columns exist
        cursor.execute("PRAGMA table_info(accounts)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Build query based on available columns
        select_columns = ['account_id', 'account_type', 'balance', 'is_active', 'created_date']
        if 'account_status' in columns:
            select_columns.insert(3, 'account_status')
        if 'interest_rate' in columns:
            select_columns.append('interest_rate')
            
        query = f"""
            SELECT {', '.join(select_columns)}
            FROM accounts 
            WHERE customer_id = ?
            ORDER BY account_type, created_date
        """
        cursor.execute(query, (customer_id,))
        
        accounts = []
        for row in cursor.fetchall():
            account_data = {
                'account_id': row['account_id'],
                'account_type': row['account_type'],
                'balance': float(row['balance']) if row['balance'] else 0.0,
                'is_active': bool(row['is_active']),
                'created_date': row['created_date'],
            }
            
            # Add optional fields if they exist in the row
            try:
                account_data['account_status'] = row['account_status']
            except (IndexError, KeyError):
                account_data['account_status'] = 'active' if account_data['is_active'] else 'inactive'
                
            try:
                account_data['interest_rate'] = float(row['interest_rate']) if row['interest_rate'] else 0.0
            except (IndexError, KeyError):
                account_data['interest_rate'] = 0.0
                
            accounts.append(account_data)
        
        # Get transaction count for customer
        cursor.execute("""
            SELECT COUNT(*) as transaction_count
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            WHERE a.customer_id = ?
        """, (customer_id,))
        
        transaction_count = cursor.fetchone()['transaction_count']
        
        conn.close()
        
        return {
            'customer': customer,
            'accounts': accounts,
            'transaction_count': transaction_count
        }
    
    def get_recent_customers(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get the most recently created customers sorted by creation date."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if created_date column exists
        cursor.execute("PRAGMA table_info(customers)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Use created_date if available, otherwise use ROWID as a proxy
        if 'created_date' in columns:
            order_column = 'created_date DESC'
        else:
            order_column = 'ROWID DESC'
        
        query = f"""
            SELECT customer_id, first_name, last_name, email, phone, address, 
                   date_of_birth, profile_description, metadata, bulk_generation_id, 
                   bulk_generation_label, created_date
            FROM customers 
            ORDER BY {order_column}
            LIMIT ?
        """
        
        try:
            cursor.execute(query, (limit,))
            results = []
            for row in cursor.fetchall():
                customer_data = dict(row)
                # Format created_date for display if it exists
                if customer_data.get('created_date'):
                    try:
                        if isinstance(customer_data['created_date'], str):
                            # Parse and format the datetime string
                            dt = datetime.fromisoformat(customer_data['created_date'].replace('Z', '+00:00'))
                            customer_data['created_date_display'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            customer_data['created_date_display'] = str(customer_data['created_date'])
                    except (ValueError, TypeError):
                        customer_data['created_date_display'] = str(customer_data['created_date'])
                else:
                    customer_data['created_date_display'] = 'N/A'
                    
                results.append(customer_data)
                
        except sqlite3.Error as e:
            print(f"Database error in get_recent_customers: {e}")
            results = []
        
        conn.close()
        return results
    
    def get_account_details(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get complete account details with transactions."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check what columns exist in accounts table
        cursor.execute("PRAGMA table_info(accounts)")
        account_columns = [row[1] for row in cursor.fetchall()]
        
        # Build dynamic query
        base_select = "a.account_id, a.account_type, a.balance, a.is_active, a.created_date, a.customer_id"
        if 'account_status' in account_columns:
            base_select += ", a.account_status"
        if 'interest_rate' in account_columns:
            base_select += ", a.interest_rate"
        
        # Get account info with customer name
        cursor.execute(f"""
            SELECT {base_select}, c.first_name, c.last_name, c.email
            FROM accounts a
            JOIN customers c ON a.customer_id = c.customer_id
            WHERE a.account_id = ?
        """, (account_id,))
        
        account_row = cursor.fetchone()
        if not account_row:
            conn.close()
            return None
        
        account = dict(account_row)
        
        # Ensure default values for optional fields
        if 'account_status' not in account:
            account['account_status'] = 'active' if account.get('is_active', True) else 'inactive'
        if 'interest_rate' not in account:
            account['interest_rate'] = 0.0
        
        # Get recent transactions (last 50)
        cursor.execute("""
            SELECT transaction_id, transaction_type, amount, description,
                   transaction_date, related_transaction_id
            FROM transactions
            WHERE account_id = ?
            ORDER BY transaction_date DESC, transaction_id DESC
            LIMIT 50
        """, (account_id,))
        
        transactions = []
        for row in cursor.fetchall():
            transactions.append({
                'transaction_id': row['transaction_id'],
                'transaction_type': row['transaction_type'],
                'amount': float(row['amount']) if row['amount'] else 0.0,
                'description': row['description'],
                'transaction_date': row['transaction_date'],
                'related_transaction_id': row['related_transaction_id']
            })
        
        # Get transaction summary
        cursor.execute("""
            SELECT 
                COUNT(*) as total_transactions,
                SUM(CASE WHEN transaction_type IN ('deposit', 'credit') THEN amount ELSE 0 END) as total_credits,
                SUM(CASE WHEN transaction_type IN ('debit', 'withdrawal') THEN amount ELSE 0 END) as total_debits,
                AVG(ABS(amount)) as avg_amount
            FROM transactions
            WHERE account_id = ?
        """, (account_id,))
        
        summary_row = cursor.fetchone()
        transaction_summary = {
            'total_transactions': summary_row['total_transactions'],
            'total_credits': float(summary_row['total_credits']) if summary_row['total_credits'] else 0.0,
            'total_debits': float(summary_row['total_debits']) if summary_row['total_debits'] else 0.0,
            'avg_amount': float(summary_row['avg_amount']) if summary_row['avg_amount'] else 0.0
        }
        
        conn.close()
        
        return {
            'account': account,
            'transactions': transactions,
            'transaction_summary': transaction_summary
        }
    
    def get_profile_templates(self) -> List[Dict[str, Any]]:
        """Get all profile templates from database."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT 
            template_id, name, description, entity_type, category, complexity_level,
            icon, color, typical_income_range, typical_accounts, typical_transactions,
            tags, created_date, metadata
        FROM profile_templates
        ORDER BY category, name
        """)
        
        templates = []
        for row in cursor.fetchall():
            template = dict(row)
            # Parse JSON fields
            import json
            if template['typical_accounts']:
                template['typical_accounts'] = json.loads(template['typical_accounts'])
            if template['typical_transactions']:
                template['typical_transactions'] = json.loads(template['typical_transactions'])
            if template['tags']:
                template['tags'] = json.loads(template['tags'])
            if template['metadata']:
                template['metadata'] = json.loads(template['metadata'])
            templates.append(template)
        
        conn.close()
        return templates

# Global database browser instance
db_browser = None

@app.route('/')
def index():
    """Home page with guidance for creating customers, accounts, and transactions."""
    return render_template('index.html', active_page='home')

@app.route('/customers')
def customers():
    """Customer search and management page."""
    return render_template('customers.html', active_page='customers')

@app.route('/profiles')
def profiles():
    """Profile templates browsing page."""
    return render_template('profiles.html', active_page='profile-templates')

@app.route('/profile-template/<template_id>')
def profile_template_details(template_id):
    """Individual profile template details page."""
    return render_template('profile_template_details.html', 
                         active_page='profile-templates', 
                         template_id=template_id)

@app.route('/builder')
def builder():
    """Redirect to home page for backward compatibility."""
    return render_template('index.html', active_page='home')

@app.route('/bulk-generations')
def bulk_generations():
    """Bulk generations management page."""
    return render_template('bulk_generations.html', active_page='bulk-generations')

@app.route('/export')
def export_data():
    """Data export management page."""
    return render_template('export.html', active_page='export')

@app.route('/profile-details')
def profile_details():
    """Profile details browsing page."""
    return render_template('profile_details.html', active_page='profile-details')

@app.route('/profile-detail/<profile_id>')
def profile_detail(profile_id):
    """Individual profile detail view."""
    return render_template('profile_detail.html', 
                         profile_id=profile_id, 
                         active_page='profile-details')

@app.route('/accounts')
def accounts():
    """Accounts browsing page."""
    return render_template('accounts.html', active_page='accounts')

@app.route('/transactions')
def transactions():
    """Transactions browsing page."""
    return render_template('transactions.html', active_page='transactions')

@app.route('/search')
def search():
    """Search customers endpoint."""
    search_params = {
        'customer_id': request.args.get('customer_id', '').strip(),
        'first_name': request.args.get('first_name', '').strip(),
        'last_name': request.args.get('last_name', '').strip(),
        'company_name': request.args.get('company_name', '').strip(),
        'email': request.args.get('email', '').strip(),
        'phone': request.args.get('phone', '').strip(),
        'address': request.args.get('address', '').strip(),
        'profile_description': request.args.get('profile_description', '').strip(),
        'profile_metadata': request.args.get('profile_metadata', '').strip(),
        'bulk_generation_id': request.args.get('bulk_generation_id', '').strip(),
        'bulk_generation_label': request.args.get('bulk_generation_label', '').strip()
    }
    
    # Remove empty parameters
    search_params = {k: v for k, v in search_params.items() if v}
    
    if db_browser:
        results = db_browser.search_customers(search_params)
        return jsonify({'success': True, 'customers': results})
    else:
        return jsonify({'success': False, 'error': 'Database not connected'})

@app.route('/search/preset/<preset_name>')
def search_preset(preset_name):
    """Search customers using predefined presets."""
    if not db_browser:
        return jsonify({'success': False, 'error': 'Database not connected'})
    
    try:
        if preset_name == 'recent':
            # Get 20 most recently created customers
            results = db_browser.get_recent_customers(limit=20)
            return jsonify({'success': True, 'customers': results})
        else:
            return jsonify({'success': False, 'error': f'Unknown preset: {preset_name}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/customer/<customer_id>')
def customer_details(customer_id):
    """Customer details page."""
    if db_browser:
        details = db_browser.get_customer_details(customer_id)
        if details:
            back_links = [{'url': '/customers', 'icon': 'fas fa-arrow-left', 'text': 'Back to Search'}]
            return render_template('customer_details.html', data=details, active_page='customers', 
                                 show_back_links=True, back_links=back_links)
        else:
            return render_template('error.html', message='Customer not found')
    else:
        return render_template('error.html', message='Database not connected')

@app.route('/account/<account_id>')
def account_details(account_id):
    """Account details page."""
    if db_browser:
        details = db_browser.get_account_details(account_id)
        if details:
            back_links = [
                {'url': f'/customer/{details["account"]["customer_id"]}', 'icon': 'fas fa-user', 'text': 'Customer Details'},
                {'url': '/customers', 'icon': 'fas fa-arrow-left', 'text': 'Back to Search'}
            ]
            return render_template('account_details.html', data=details, active_page='customers', 
                                 show_back_links=True, back_links=back_links)
        else:
            return render_template('error.html', message='Account not found')
    else:
        return render_template('error.html', message='Database not connected')

@app.route('/api/databases')
def list_databases():
    """List available database files."""
    db_files = []
    # Check both current directory and data directory for backward compatibility
    for db_path in [Path('.'), Path('data')]:
        if db_path.exists():
            for db_file in db_path.glob('*.db'):
                db_files.append({
                    'name': db_file.name,
                    'path': str(db_file),
                    'size': db_file.stat().st_size
                })
    return jsonify({'databases': db_files})

@app.route('/connect/<db_name>')
def connect_database(db_name):
    """Connect to a specific database."""
    global db_browser, current_database
    
    # Check for database file in data directory first, then root directory for backward compatibility
    db_path_data = Path('data') / db_name
    db_path_root = Path(db_name)
    
    actual_db_path = None
    if db_path_data.exists():
        actual_db_path = db_path_data
    elif db_path_root.exists():
        actual_db_path = db_path_root
    
    if actual_db_path:
        try:
            db_browser = DatabaseBrowser(str(actual_db_path))
            current_database = db_name
            session['current_database'] = db_name
            return jsonify({'success': True, 'message': f'Connected to {db_name}', 'database': db_name})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    else:
        return jsonify({'success': False, 'error': 'Database file not found'})

@app.route('/api/current-database')
def get_current_database():
    """Get information about the currently connected database."""
    global current_database
    
    if current_database:
        # Parse the database path to get filename and location
        db_path = Path(current_database)
        filename = db_path.name
        location = str(db_path.parent) if db_path.parent != Path('.') else '.'
        
        # Remove .db extension for display name
        display_name = filename.replace('.db', '') if filename.endswith('.db') else filename
        
        return jsonify({
            'success': True, 
            'database': current_database,  # Full path for backward compatibility
            'filename': filename,          # e.g., "syfi_bank3.db"
            'display_name': display_name,  # e.g., "syfi_bank3"
            'location': location,          # e.g., "data"
            'connected': True
        })
    else:
        return jsonify({
            'success': True,
            'database': None,
            'filename': None,
            'display_name': None,
            'location': None,
            'connected': False
        })

@app.route('/api/create-database', methods=['POST'])
def create_database():
    """Create a new database with optional template data."""
    try:
        data = request.get_json()
        db_name = data.get('name', '').strip()
        template = data.get('template', 'empty')
        
        if not db_name:
            return jsonify({'success': False, 'error': 'Database name is required'})
        
        # Validate database name
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', db_name):
            return jsonify({'success': False, 'error': 'Invalid database name. Use only letters, numbers, underscores, and hyphens.'})
        
        # Ensure .db extension
        if not db_name.endswith('.db'):
            db_name += '.db'
        
        # Create in data directory
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        db_path = data_dir / db_name
        
        # Check if database already exists
        if db_path.exists():
            return jsonify({'success': False, 'error': f'Database {db_name} already exists'})
        
        # Create new database connection
        conn = sqlite3.connect(str(db_path))
        
        try:
            # Initialize database with template
            if template == 'banking' or template == 'sample':
                # Create banking schema with customers, accounts, transactions tables
                create_banking_schema(conn, include_sample_data=(template == 'sample'))
            else:
                # Empty database - just create a simple table to initialize
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS database_info (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        version TEXT DEFAULT '1.0'
                    )
                """)
                cursor.execute("INSERT INTO database_info (name, version) VALUES (?, ?)", 
                             (db_name.replace('.db', ''), '1.0'))
                conn.commit()
            
            conn.close()
            
            return jsonify({
                'success': True,
                'message': f'Database {db_name} created successfully',
                'database_path': str(db_path),
                'template': template
            })
            
        except Exception as e:
            conn.close()
            # Clean up failed database file
            if db_path.exists():
                db_path.unlink()
            raise e
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def create_banking_schema(conn, include_sample_data=False):
    """Create banking database schema with optional sample data."""
    cursor = conn.cursor()
    
    # Create customers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            phone TEXT,
            date_of_birth DATE,
            address TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            ssn_hash TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            household_size INTEGER,
            num_adults INTEGER,
            num_children INTEGER,
            num_pets INTEGER,
            household_income DECIMAL(15,2),
            employment_status TEXT,
            marital_status TEXT,
            profile_description TEXT,
            profile_tags TEXT,
            metadata TEXT
        )
    """)
    
    # Create accounts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            account_id TEXT PRIMARY KEY,
            customer_id TEXT,
            account_number TEXT,
            account_type TEXT,
            balance DECIMAL(15,2),
            available_balance DECIMAL(15,2),
            currency TEXT DEFAULT 'USD',
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closed_date DATE,
            is_active BOOLEAN DEFAULT 1,
            interest_rate DECIMAL(5,4),
            credit_limit DECIMAL(15,2),
            metadata TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
        )
    """)
    
    # Create transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            account_id TEXT,
            transaction_type TEXT,
            amount DECIMAL(15,2),
            currency TEXT DEFAULT 'USD',
            description TEXT,
            category TEXT,
            merchant_name TEXT,
            merchant_category TEXT,
            transaction_date TIMESTAMP,
            posted_date TIMESTAMP,
            reference_number TEXT,
            balance_after DECIMAL(15,2),
            related_account_id TEXT,
            related_transaction_id TEXT,
            location TEXT,
            metadata TEXT,
            FOREIGN KEY (account_id) REFERENCES accounts (account_id)
        )
    """)
    
    # Create database info table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS database_info (
            id INTEGER PRIMARY KEY,
            name TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            version TEXT DEFAULT '1.0',
            template TEXT DEFAULT 'banking'
        )
    """)
    
    if include_sample_data:
        # Add sample customer
        cursor.execute("""
            INSERT INTO customers (
                customer_id, first_name, last_name, email, phone, 
                date_of_birth, address, city, state, zip_code,
                household_size, num_adults, num_children, household_income,
                employment_status, marital_status
            ) VALUES (
                'CUST001', 'John', 'Doe', 'john.doe@email.com', '555-0123',
                '1985-06-15', '123 Main St', 'Anytown', 'ST', '12345',
                2, 2, 0, 75000.00, 'employed', 'married'
            )
        """)
        
        # Add sample account
        cursor.execute("""
            INSERT INTO accounts (
                account_id, customer_id, account_number, account_type,
                balance, available_balance, is_active
            ) VALUES (
                'ACC001', 'CUST001', '1234567890', 'checking',
                2500.00, 2500.00, 1
            )
        """)
        
        # Add sample transaction
        cursor.execute("""
            INSERT INTO transactions (
                transaction_id, account_id, transaction_type, amount,
                description, category, transaction_date, balance_after
            ) VALUES (
                'TXN001', 'ACC001', 'credit', 1000.00,
                'Initial Deposit', 'deposit', datetime('now'), 1000.00
            )
        """)
    
    # Insert database info
    cursor.execute("""
        INSERT INTO database_info (name, template) VALUES (?, ?)
    """, (conn.execute("PRAGMA database_list").fetchone()[2], 'banking' if not include_sample_data else 'sample'))
    
    conn.commit()

@app.route('/api/transaction-stats')
def get_transaction_stats():
    """Get basic transaction statistics for the connected database."""
    if not db_browser:
        return jsonify({'success': False, 'error': 'Database not connected'})
    
    try:
        conn = db_browser.get_connection()
        cursor = conn.cursor()
        
        # Get basic transaction statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_transactions,
                COUNT(DISTINCT account_id) as accounts_with_transactions,
                MIN(DATE(transaction_date)) as earliest_date,
                MAX(DATE(transaction_date)) as latest_date,
                COUNT(DISTINCT transaction_type) as transaction_types,
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as total_credits,
                SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as total_debits
            FROM transactions
        """)
        
        stats = dict(cursor.fetchone())
        
        # Get transaction types
        cursor.execute("""
            SELECT DISTINCT transaction_type 
            FROM transactions 
            ORDER BY transaction_type
        """)
        
        transaction_types = [row[0] for row in cursor.fetchall()]
        stats['available_types'] = transaction_types
        
        conn.close()
        
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/entity-stats')
def get_entity_stats():
    """Get entity-specific banking statistics for multi-entity databases."""
    if not db_browser:
        return jsonify({'success': False, 'error': 'No database connected'})
    
    conn = db_browser.get_connection()
    cursor = conn.cursor()
    
    try:
        entities = {}
        
        # Detect entity types by customer names and employment patterns
        cursor.execute("""
            SELECT 
                c.customer_id,
                c.first_name,
                c.last_name,
                c.employment_status,
                c.household_income,
                COUNT(DISTINCT a.account_id) as account_count
            FROM customers c
            LEFT JOIN accounts a ON c.customer_id = a.customer_id
            GROUP BY c.customer_id
        """)
        
        customers = cursor.fetchall()
        
        for customer in customers:
            # Detect entity type based on naming patterns
            entity_type = "Unknown"
            full_name = f"{customer['first_name']} {customer['last_name']}".strip()
            
            if "LLC" in full_name or "Inc" in full_name or "Foundation" in full_name:
                if "Foundation" in full_name or "Center" in full_name or "Alliance" in full_name:
                    entity_type = "Non-Profit"
                elif "Market" in full_name or "Grocers" in full_name or "Supermarket" in full_name:
                    entity_type = "Supermarket"
                elif "Bistro" in full_name or "Cafe" in full_name or "Grill" in full_name or "Kitchen" in full_name or "Vista" in full_name:
                    entity_type = "Restaurant"
                else:
                    entity_type = "Business"
            else:
                entity_type = "Family"
            
            # Get transaction stats for this customer
            cursor.execute("""
                SELECT 
                    COUNT(*) as transaction_count,
                    SUM(ABS(amount)) as total_volume,
                    SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as credits,
                    SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as debits,
                    AVG(ABS(amount)) as avg_transaction_size
                FROM transactions t
                JOIN accounts a ON t.account_id = a.account_id
                WHERE a.customer_id = ?
            """, (customer['customer_id'],))
            
            txn_stats = cursor.fetchone()
            
            if entity_type not in entities:
                entities[entity_type] = {
                    'customers': [],
                    'total_accounts': 0,
                    'total_transactions': 0,
                    'total_volume': 0,
                    'total_credits': 0,
                    'total_debits': 0,
                    'icon': '👥' if entity_type == 'Family' else '🍽️' if entity_type == 'Restaurant' else '🛒' if entity_type == 'Supermarket' else '🏛️' if entity_type == 'Non-Profit' else '🏢',
                    'color': 'success' if entity_type == 'Family' else 'warning' if entity_type == 'Restaurant' else 'info' if entity_type == 'Supermarket' else 'primary' if entity_type == 'Non-Profit' else 'secondary'
                }
            
            entities[entity_type]['customers'].append({
                'customer_id': customer['customer_id'],
                'name': full_name,
                'employment_status': customer['employment_status'],
                'household_income': float(customer['household_income']) if customer['household_income'] else 0,
                'account_count': customer['account_count'],
                'transaction_count': txn_stats['transaction_count'] if txn_stats else 0,
                'transaction_volume': float(txn_stats['total_volume']) if txn_stats and txn_stats['total_volume'] else 0,
                'avg_transaction_size': float(txn_stats['avg_transaction_size']) if txn_stats and txn_stats['avg_transaction_size'] else 0
            })
            
            # Aggregate entity totals
            entities[entity_type]['total_accounts'] += customer['account_count']
            entities[entity_type]['total_transactions'] += txn_stats['transaction_count'] if txn_stats else 0
            entities[entity_type]['total_volume'] += float(txn_stats['total_volume']) if txn_stats and txn_stats['total_volume'] else 0
            entities[entity_type]['total_credits'] += float(txn_stats['credits']) if txn_stats and txn_stats['credits'] else 0
            entities[entity_type]['total_debits'] += float(txn_stats['debits']) if txn_stats and txn_stats['debits'] else 0
        
        return jsonify({'success': True, 'entities': entities})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    
    finally:
        conn.close()


@app.route('/api/profile-templates')
def get_profile_templates():
    """Get profile templates from database."""
    if not db_browser:
        return jsonify({'success': False, 'error': 'Database not connected'})
    
    try:
        # Get templates from database
        templates = db_browser.get_profile_templates()
        
        # Convert to API format
        formatted_templates = []
        for template in templates:
            formatted_template = {
                'id': template['template_id'],
                'template_id': template['template_id'],  # Add this for compatibility
                'name': template['name'],
                'category': template['category'],
                'complexity_level': template['complexity_level'],
                'entity_type': template['entity_type'].title(),
                'icon': template['icon'],
                'color': template['color'],
                'description': template['description'],
                'tags': template['tags'] or [],
                'typical_accounts': template['typical_accounts'] or [],
                'typical_income_range': template['typical_income_range'],
                'typical_transactions': template['typical_transactions'] or []
            }
            formatted_templates.append(formatted_template)
        
        return jsonify({'success': True, 'templates': formatted_templates})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/template-customers/<template_id>')
def get_template_customers(template_id):
    """Get customers generated from a specific template."""
    if not db_browser:
        return jsonify({'success': False, 'error': 'Database not connected'})
    
    try:
        conn = db_browser.get_connection()
        cursor = conn.cursor()
        
        # Get customers linked to profiles from this template
        cursor.execute("""
        SELECT c.customer_id, c.first_name, c.last_name, c.company_name, 
               c.email, c.phone, c.address, c.city, c.state,
               c.created_date, p.profile_id, p.name as profile_name
        FROM customers c
        JOIN profiles p ON c.customer_id = p.customer_id
        WHERE p.template_id = ?
        ORDER BY c.created_date DESC
        """, (template_id,))
        
        customers = []
        for row in cursor.fetchall():
            customer = dict(row)
            # Add display name (company name or full name)
            if customer['company_name']:
                customer['display_name'] = customer['company_name']
            else:
                customer['display_name'] = f"{customer['first_name']} {customer['last_name']}"
            customers.append(customer)
        
        conn.close()
        return jsonify({'success': True, 'customers': customers})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/template-profiles/<template_id>')
def get_template_profiles(template_id):
    """Get profiles generated from a specific template."""
    if not db_browser:
        return jsonify({'success': False, 'error': 'Database not connected'})
    
    try:
        conn = db_browser.get_connection()
        cursor = conn.cursor()
        
        # Get profiles from this template with customer information
        cursor.execute("""
        SELECT p.profile_id, p.name as profile_name, p.description,
               p.created_date, p.customer_id,
               c.first_name, c.last_name, c.company_name,
               c.email, c.phone, c.city, c.state,
               pt.name as template_name, pt.entity_type
        FROM profiles p
        JOIN customers c ON p.customer_id = c.customer_id
        JOIN profile_templates pt ON p.template_id = pt.template_id
        WHERE p.template_id = ?
        ORDER BY p.created_date DESC
        """, (template_id,))
        
        profiles = []
        for row in cursor.fetchall():
            profile = dict(row)
            # Add display name (company name or full name)
            if profile['company_name']:
                profile['display_name'] = profile['company_name']
            else:
                profile['display_name'] = f"{profile['first_name']} {profile['last_name']}"
            profiles.append(profile)
        
        conn.close()
        return jsonify({'success': True, 'profiles': profiles})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/profiles')
def get_profiles():
    """Search and filter profiles with customer and template information."""
    print(f"\n=== API /api/profiles called ===")
    print(f"Request URL: {request.url}")
    print(f"Request args: {dict(request.args)}")
    
    if not db_browser:
        return jsonify({'success': False, 'error': 'Database not connected'})
    
    try:
        
        # Get search parameters
        search_query = request.args.get('search', '').strip()
        profile_id = request.args.get('profile_id', '').strip()
        template_id = request.args.get('template_id', '').strip()
        has_customer = request.args.get('has_customer', '').strip()
        limit = request.args.get('limit', '50')
        
        print(f"Parsed parameters:")
        print(f"  search_query: '{search_query}' (empty: {not search_query})")
        print(f"  profile_id: '{profile_id}' (empty: {not profile_id})")
        print(f"  template_id: '{template_id}' (empty: {not template_id})")
        print(f"  has_customer: '{has_customer}' (empty: {not has_customer})")
        print(f"  limit: '{limit}'")
        
        # Build query to get profiles with related customer and template data
        query = """
            SELECT 
                p.profile_id,
                p.name as profile_name,
                p.description,
                p.created_date,
                p.used_date,
                p.template_id,
                pt.name as template_name,
                pt.entity_type,
                pt.category,
                p.customer_id,
                CASE 
                    WHEN c.company_name IS NOT NULL AND c.company_name != '' 
                    THEN c.company_name 
                    ELSE c.first_name || ' ' || c.last_name 
                END as customer_name,
                c.first_name,
                c.last_name,
                c.company_name,
                c.email
            FROM profiles p
            LEFT JOIN profile_templates pt ON p.template_id = pt.template_id
            LEFT JOIN customers c ON p.customer_id = c.customer_id
            WHERE 1=1
        """
        
        params = []
        
        # Add search filter
        if search_query:
            query += """ AND (
                p.name LIKE ? OR 
                p.description LIKE ? OR 
                pt.name LIKE ? OR
                c.first_name LIKE ? OR
                c.last_name LIKE ? OR
                c.company_name LIKE ?
            )"""
            search_param = f'%{search_query}%'
            params.extend([search_param] * 6)
        
        # Add profile ID filter
        if profile_id:
            query += " AND p.profile_id = ?"
            params.append(profile_id)
        
        # Add template filter
        if template_id:
            query += " AND p.template_id = ?"
            params.append(template_id)
        
        # Add customer association filter
        if has_customer == 'true':
            query += " AND p.customer_id IS NOT NULL"
        elif has_customer == 'false':
            query += " AND p.customer_id IS NULL"
        
        # Add ordering and limit
        query += " ORDER BY p.created_date DESC"
        if limit.isdigit():
            query += " LIMIT ?"
            params.append(int(limit))
        
        print(f"Final SQL query: {query}")
        print(f"Query parameters: {params}")
        
        conn = db_browser.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        print(f"Query returned {len(results)} profiles")
        
        profiles = []
        for row in results:
            profile = {
                'profile_id': row[0],
                'profile_name': row[1],
                'description': row[2],
                'created_date': row[3],
                'used_date': row[4],
                'template_id': row[5],
                'template_name': row[6],
                'entity_type': row[7],
                'category': row[8],
                'customer_id': row[9],
                'customer_name': row[10],
                'first_name': row[11],
                'last_name': row[12],
                'company_name': row[13],
                'email': row[14]
            }
            profiles.append(profile)
        
        conn.close()
        
        print(f"Returning {len(profiles)} profiles to client")
        print(f"=== END API /api/profiles ===\n")
        
        return jsonify({'success': True, 'profiles': profiles})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/profile-customers/<profile_id>')
def get_profile_customers(profile_id):
    """Get the customer associated with a specific profile."""
    if not db_browser:
        return jsonify({'success': False, 'error': 'Database not connected'})
    
    try:
        
        # Get the customer for this profile
        query = """
            SELECT 
                c.customer_id,
                c.first_name,
                c.last_name,
                c.company_name,
                c.email,
                c.phone,
                c.address,
                c.city,
                c.state,
                c.created_date,
                CASE 
                    WHEN c.company_name IS NOT NULL AND c.company_name != '' 
                    THEN c.company_name 
                    ELSE c.first_name || ' ' || c.last_name 
                END as display_name,
                p.profile_id,
                p.name as profile_name
            FROM profiles p
            LEFT JOIN customers c ON p.customer_id = c.customer_id
            WHERE p.profile_id = ?
        """
        
        conn = db_browser.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, (profile_id,))
        result = cursor.fetchone()
        
        if result and result[0]:  # Has associated customer
            customer = {
                'customer_id': result[0],
                'first_name': result[1],
                'last_name': result[2],
                'company_name': result[3],
                'email': result[4],
                'phone': result[5],
                'address': result[6],
                'city': result[7],
                'state': result[8],
                'created_date': result[9],
                'display_name': result[10],
                'profile_id': result[11],
                'profile_name': result[12]
            }
            customers = [customer]
        else:
            customers = []
        
        conn.close()
        return jsonify({'success': True, 'customers': customers})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/customers')
def get_customers():
    """Get customers, optionally filtered by profile_id."""
    if not db_browser:
        return jsonify({'success': False, 'error': 'Database not connected'})
    
    try:
        profile_id = request.args.get('profile_id', '').strip()
        
        if profile_id:
            # Use existing profile-customers endpoint logic
            return get_profile_customers(profile_id)
        else:
            # Get all customers
            query = """
                SELECT 
                    c.customer_id,
                    c.first_name,
                    c.last_name,
                    c.company_name,
                    c.email,
                    c.phone,
                    c.address,
                    c.city,
                    c.state,
                    c.created_date,
                    CASE 
                        WHEN c.company_name IS NOT NULL AND c.company_name != '' 
                        THEN c.company_name 
                        ELSE c.first_name || ' ' || c.last_name 
                    END as display_name
                FROM customers c
                ORDER BY c.created_date DESC
            """
            
            conn = db_browser.get_connection()
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            
            customers = []
            for row in results:
                customer = {
                    'customer_id': row[0],
                    'first_name': row[1],
                    'last_name': row[2],
                    'company_name': row[3],
                    'email': row[4],
                    'phone': row[5],
                    'address': row[6],
                    'city': row[7],
                    'state': row[8],
                    'created_date': row[9],
                    'display_name': row[10]
                }
                customers.append(customer)
            
            conn.close()
            return jsonify({'success': True, 'customers': customers})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/accounts')
def get_accounts():
    """Get accounts, optionally filtered by profile_id."""
    if not db_browser:
        return jsonify({'success': False, 'error': 'Database not connected'})
    
    try:
        profile_id = request.args.get('profile_id', '').strip()
        
        query = """
            SELECT 
                a.account_id,
                a.account_number,
                a.account_type,
                a.balance,
                a.customer_id,
                a.profile_id,
                a.created_date
            FROM accounts a
            WHERE 1=1
        """
        
        params = []
        if profile_id:
            query += " AND a.profile_id = ?"
            params.append(profile_id)
        
        query += " ORDER BY a.created_date DESC"
        
        conn = db_browser.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        accounts = []
        for row in results:
            account = {
                'account_id': row[0],
                'account_number': row[1],
                'account_type': row[2],
                'balance': row[3],
                'customer_id': row[4],
                'profile_id': row[5],
                'created_date': row[6]
            }
            accounts.append(account)
        
        conn.close()
        return jsonify({'success': True, 'accounts': accounts})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/transactions')
def get_transactions():
    """Get transactions, optionally filtered by profile_id."""
    if not db_browser:
        return jsonify({'success': False, 'error': 'Database not connected'})
    
    try:
        profile_id = request.args.get('profile_id', '').strip()
        
        query = """
            SELECT 
                t.transaction_id,
                t.account_id,
                t.transaction_type,
                t.amount,
                t.description,
                t.transaction_date,
                t.profile_id
            FROM transactions t
            WHERE 1=1
        """
        
        params = []
        if profile_id:
            query += " AND t.profile_id = ?"
            params.append(profile_id)
        
        query += " ORDER BY t.transaction_date DESC"
        
        conn = db_browser.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        transactions = []
        for row in results:
            transaction = {
                'transaction_id': row[0],
                'account_id': row[1],
                'transaction_type': row[2],
                'amount': row[3],
                'description': row[4],
                'transaction_date': row[5],
                'profile_id': row[6]
            }
            transactions.append(transaction)
        
        conn.close()
        return jsonify({'success': True, 'transactions': transactions})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/account-analytics/<account_id>')
def get_account_analytics(account_id):
    """Get monthly transaction analytics for a specific account (totals and counts)."""
    if not db_browser:
        return jsonify({'success': False, 'error': 'Database not connected'})
    
    try:
        conn = db_browser.get_connection()
        cursor = conn.cursor()
        
        # Get monthly transaction data for the account
        cursor.execute("""
            SELECT 
                strftime('%Y-%m', transaction_date) as month,
                COUNT(*) as transaction_count,
                SUM(amount) as total_volume,
                SUM(CASE WHEN transaction_type IN ('deposit', 'credit') THEN amount 
                         WHEN transaction_type IN ('debit', 'withdrawal') THEN -amount 
                         ELSE 0 END) as net_amount,
                AVG(amount) as avg_amount
            FROM transactions 
            WHERE account_id = ?
            GROUP BY strftime('%Y-%m', transaction_date)
            ORDER BY month
        """, (account_id,))
        
        monthly_data = cursor.fetchall()
        
        # Format data for Chart.js
        months = []
        transaction_counts = []
        total_amounts = []
        
        for row in monthly_data:
            month_str = row[0]  # YYYY-MM format
            if month_str:  # Make sure we have valid date
                # Convert to readable format (MMM YYYY)
                year, month = month_str.split('-')
                month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                month_label = f"{month_names[int(month)-1]} {year}"
                
                months.append(month_label)
                transaction_counts.append(row[1])  # transaction_count
                total_amounts.append(float(row[3]) if row[3] else 0)  # net_amount (index 3)
        
        # Get account info
        cursor.execute("""
            SELECT account_type, balance, is_active 
            FROM accounts 
            WHERE account_id = ?
        """, (account_id,))
        
        account_info = cursor.fetchone()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'account_id': account_id,
            'account_info': {
                'type': account_info[0] if account_info else 'Unknown',
                'balance': float(account_info[1]) if account_info and account_info[1] else 0,
                'status': 'active' if account_info and account_info[2] else 'inactive'
            },
            'chart_data': {
                'months': months,
                'transaction_counts': transaction_counts,
                'total_amounts': total_amounts
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/create-customer', methods=['POST'])
def create_customer():
    """Create a new customer."""
    if not db_browser:
        return jsonify({'success': False, 'error': 'Database not connected'})
    
    try:
        data = request.json
        conn = db_browser.get_connection()
        cursor = conn.cursor()
        
        # Generate customer ID if not provided
        customer_id = data.get('customer_id')
        if not customer_id:
            import random
            import string
            customer_id = 'CUST' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        # Insert customer
        cursor.execute("""
            INSERT INTO customers (customer_id, first_name, last_name, email, phone, address, date_of_birth)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            customer_id,
            data['first_name'],
            data['last_name'],
            data['email'],
            data.get('phone'),
            data.get('address'),
            data.get('date_of_birth')
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'customer_id': customer_id})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/create-account', methods=['POST'])
def create_account():
    """Create a new account."""
    if not db_browser:
        return jsonify({'success': False, 'error': 'Database not connected'})
    
    try:
        data = request.json
        conn = db_browser.get_connection()
        cursor = conn.cursor()
        
        # Verify customer exists
        cursor.execute("SELECT customer_id FROM customers WHERE customer_id = ?", (data['customer_id'],))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Customer not found'})
        
        # Generate account ID if not provided
        account_id = data.get('account_id')
        if not account_id:
            import random
            import string
            account_id = 'ACCT' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        # Insert account
        cursor.execute("""
            INSERT INTO accounts (account_id, customer_id, account_type, balance, interest_rate, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            account_id,
            data['customer_id'],
            data['account_type'],
            data.get('balance', 0.0),
            data.get('interest_rate', 0.0),
            data.get('is_active', True)
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'account_id': account_id})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/create-transaction', methods=['POST'])
def create_transaction():
    """Create a new transaction."""
    if not db_browser:
        return jsonify({'success': False, 'error': 'Database not connected'})
    
    try:
        data = request.json
        conn = db_browser.get_connection()
        cursor = conn.cursor()
        
        # Verify account exists
        cursor.execute("SELECT account_id FROM accounts WHERE account_id = ?", (data['account_id'],))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Account not found'})
        
        # Generate transaction ID if not provided
        transaction_id = data.get('transaction_id')
        if not transaction_id:
            import random
            import string
            transaction_id = 'TXN' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        
        # Set transaction date if not provided
        transaction_date = data.get('transaction_date')
        if not transaction_date:
            from datetime import datetime
            transaction_date = datetime.now().isoformat()
        
        # Insert transaction
        cursor.execute("""
            INSERT INTO transactions (transaction_id, account_id, transaction_type, amount, description, transaction_date, related_transaction_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            transaction_id,
            data['account_id'],
            data['transaction_type'],
            data['amount'],
            data.get('description'),
            transaction_date,
            data.get('related_transaction_id')
        ))
        
        # Update account balance if it's a deposit or withdrawal
        if data['transaction_type'] in ['deposit', 'credit']:
            cursor.execute("""
                UPDATE accounts SET balance = balance + ? WHERE account_id = ?
            """, (data['amount'], data['account_id']))
        elif data['transaction_type'] in ['withdrawal', 'debit']:
            cursor.execute("""
                UPDATE accounts SET balance = balance - ? WHERE account_id = ?
            """, (data['amount'], data['account_id']))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'transaction_id': transaction_id})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/bulk-generate-customers', methods=['POST'])
def bulk_generate_customers():
    """Generate multiple customers using natural language profile description with bulk tracking."""
    if not db_browser:
        return jsonify({'success': False, 'error': 'Database not connected'})
    
    try:
        data = request.json
        count = data.get('count', 50)
        profile_description = data.get('profile', '')
        label = data.get('label', '')  # Optional user-provided label
        create_accounts = data.get('create_accounts', True)
        create_transactions = data.get('create_transactions', False)
        
        if count > 1000:
            return jsonify({'success': False, 'error': 'Maximum 1000 customers allowed per batch'})
        
        def generate():
            """Generator function for streaming progress updates."""
            bulk_id = None
            try:
                # Create bulk generation tracking record
                operation_type = 'customers'
                if create_accounts and create_transactions:
                    operation_type = 'mixed'
                elif create_accounts:
                    operation_type = 'customers_with_accounts'
                
                bulk_id = db_browser.bulk_tracker.create_bulk_generation(
                    operation_type=operation_type,
                    profile_description=profile_description,
                    label=label if label else None
                )
                
                if not bulk_id:
                    yield f"data: {json.dumps({'error': 'Failed to create bulk generation tracking'})}\n\n"
                    return
                
                yield f"data: {json.dumps({'progress': 0, 'message': f'Starting generation (ID: {bulk_id})...', 'current': 0, 'bulk_id': bulk_id})}\n\n"
                
                # Initialize the customer generator
                generator = CustomerGenerator()
                
                # Parse the profile if provided
                profile_info = None
                if profile_description:
                    profile_info = generator.profile_parser.parse_profile(profile_description)
                
                conn = db_browser.get_connection()
                cursor = conn.cursor()
                
                customers_created = 0
                accounts_created = 0
                transactions_created = 0
                
                # Generate customers in smaller batches for better progress reporting
                batch_size = min(10, count)
                
                for batch_start in range(0, count, batch_size):
                    batch_end = min(batch_start + batch_size, count)
                    batch_count = batch_end - batch_start
                    
                    # Generate customer batch
                    customers, accounts = generator.generate_customers(
                        count=batch_count,
                        accounts_per_customer=3 if create_accounts else 0,
                        profile_description=profile_description
                    )
                    
                    # Insert customers with bulk tracking
                    for customer in customers:
                        try:
                            cursor.execute("""
                                INSERT INTO customers (customer_id, first_name, last_name, email, phone, address, date_of_birth, bulk_generation_id, bulk_generation_label)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                customer.customer_id,
                                customer.first_name,
                                customer.last_name,
                                customer.email,
                                customer.phone,
                                customer.address,
                                customer.date_of_birth.isoformat() if customer.date_of_birth else None,
                                bulk_id,
                                label
                            ))
                            customers_created += 1
                        except sqlite3.IntegrityError:
                            # Skip duplicate customer IDs
                            pass
                    
                    # Insert accounts if requested with bulk tracking
                    if create_accounts:
                        for account in accounts:
                            try:
                                cursor.execute("""
                                    INSERT INTO accounts (account_id, customer_id, account_type, balance, interest_rate, is_active, bulk_generation_id, bulk_generation_label)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    account.account_id,
                                    account.customer_id,
                                    account.account_type.value if hasattr(account.account_type, 'value') else str(account.account_type),
                                    float(account.balance),
                                    float(account.interest_rate) if account.interest_rate else 0.0,
                                    True,
                                    bulk_id,
                                    label
                                ))
                                accounts_created += 1
                            except (sqlite3.IntegrityError, AttributeError):
                                # Skip duplicate account IDs or handle missing attributes
                                pass
                    
                    conn.commit()
                    
                    # Update progress
                    progress = min(100, int((batch_end / count) * 80))  # Reserve 20% for transactions
                    yield f"data: {json.dumps({'progress': progress, 'message': f'Created {customers_created} customers, {accounts_created} accounts...', 'current': customers_created, 'bulk_id': bulk_id})}\n\n"
                    
                    time.sleep(0.1)  # Small delay to show progress
                
                # Generate transactions if requested
                if create_transactions and accounts_created > 0:
                    yield f"data: {json.dumps({'progress': 80, 'message': 'Generating transactions...', 'current': customers_created, 'bulk_id': bulk_id})}\n\n"
                    
                    # Get account data for transaction generation (only from current bulk)
                    cursor.execute("SELECT account_id, customer_id, account_type, balance FROM accounts WHERE bulk_generation_id = ? ORDER BY customer_id", (bulk_id,))
                    account_data = [
                        {
                            'account_id': row[0],
                            'customer_id': row[1], 
                            'account_type': row[2],
                            'balance': row[3]
                        }
                        for row in cursor.fetchall()
                    ]
                    
                    # Generate transactions for the past 6 months
                    from datetime import datetime, timedelta
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=180)  # 6 months
                    
                    transaction_generator = generator  # Use the same generator instance
                    transactions = transaction_generator.generate_transactions_for_period(
                        accounts=account_data,
                        start_date=start_date,
                        end_date=end_date,
                        transactions_per_day=5  # Moderate activity
                    )
                    
                    # Insert transactions with bulk tracking
                    for transaction in transactions:
                        try:
                            cursor.execute("""
                                INSERT INTO transactions (transaction_id, account_id, transaction_type, amount, description, transaction_date, related_transaction_id, bulk_generation_id, bulk_generation_label)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                transaction.transaction_id,
                                transaction.account_id,
                                transaction.transaction_type.value if hasattr(transaction.transaction_type, 'value') else str(transaction.transaction_type),
                                float(transaction.amount),
                                transaction.description,
                                transaction.transaction_date.isoformat() if transaction.transaction_date else datetime.now().isoformat(),
                                transaction.related_transaction_id,
                                bulk_id,
                                label
                            ))
                            transactions_created += 1
                        except (sqlite3.IntegrityError, AttributeError):
                            # Skip duplicate transaction IDs
                            pass
                    
                    conn.commit()
                
                conn.close()
                
                # Update bulk generation statistics
                db_browser.bulk_tracker.update_bulk_generation_stats(
                    bulk_id=bulk_id,
                    customers=customers_created,
                    accounts=accounts_created,
                    transactions=transactions_created,
                    status='completed'
                )
                
                # Final progress update
                yield f"data: {json.dumps({'progress': 100, 'message': f'Complete! Created {customers_created} customers, {accounts_created} accounts, {transactions_created} transactions', 'current': customers_created, 'complete': True, 'bulk_id': bulk_id})}\n\n"
                
            except Exception as e:
                if bulk_id:
                    db_browser.bulk_tracker.update_bulk_generation_stats(
                        bulk_id=bulk_id,
                        customers=0,
                        accounts=0,
                        transactions=0,
                        status='failed'
                    )
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return Response(generate(), mimetype='text/plain')
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/bulk-generations', methods=['GET'])
def get_bulk_generations():
    """Get list of bulk generation operations with their statistics."""
    if not db_browser:
        return jsonify({'success': False, 'error': 'Database not connected'})
    
    try:
        limit = request.args.get('limit', 50, type=int)
        bulk_generations = db_browser.bulk_tracker.get_bulk_generations(limit=limit)
        return jsonify({'success': True, 'bulk_generations': bulk_generations})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/bulk-generation/<bulk_id>', methods=['GET'])
def get_bulk_generation_details(bulk_id):
    """Get detailed information about a specific bulk generation."""
    if not db_browser:
        return jsonify({'success': False, 'error': 'Database not connected'})
    
    try:
        conn = db_browser.get_connection()
        cursor = conn.cursor()
        
        # Get bulk generation info
        cursor.execute("""
            SELECT bulk_id, label, operation_type, profile_description, created_date,
                   total_customers_created, total_accounts_created, total_transactions_created, status
            FROM bulk_generations 
            WHERE bulk_id = ?
        """, (bulk_id,))
        
        bulk_info = cursor.fetchone()
        if not bulk_info:
            return jsonify({'success': False, 'error': 'Bulk generation not found'})
        
        bulk_data = dict(bulk_info)
        
        # Get sample customers from this bulk generation
        cursor.execute("""
            SELECT customer_id, first_name, last_name, email
            FROM customers 
            WHERE bulk_generation_id = ?
            LIMIT 10
        """, (bulk_id,))
        
        customers = [dict(row) for row in cursor.fetchall()]
        
        # Get sample accounts from this bulk generation
        cursor.execute("""
            SELECT account_id, customer_id, account_type, balance
            FROM accounts 
            WHERE bulk_generation_id = ?
            LIMIT 10
        """, (bulk_id,))
        
        accounts = [dict(row) for row in cursor.fetchall()]
        
        # Get transaction summary
        cursor.execute("""
            SELECT COUNT(*) as transaction_count, 
                   SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as total_credits,
                   SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as total_debits
            FROM transactions 
            WHERE bulk_generation_id = ?
        """, (bulk_id,))
        
        transaction_summary = dict(cursor.fetchone()) if cursor.fetchone() else {}
        
        conn.close()
        
        return jsonify({
            'success': True,
            'bulk_generation': bulk_data,
            'sample_customers': customers,
            'sample_accounts': accounts,
            'transaction_summary': transaction_summary
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# Export API Endpoints
@app.route('/api/export/schemas', methods=['GET'])
def get_export_schemas():
    """Get list of available export schemas."""
    try:
        loader = ExportSchemaLoader()
        schemas = loader.list_schemas()
        return jsonify({
            'success': True,
            'schemas': schemas
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/export/schema/<schema_name>', methods=['GET'])
def get_export_schema_details(schema_name):
    """Get detailed information about a specific export schema."""
    try:
        loader = ExportSchemaLoader()
        schema = loader.get_schema(schema_name)
        
        if not schema:
            return jsonify({'success': False, 'error': 'Schema not found'}), 404
        
        # Convert schema to dict for JSON response
        schema_dict = {
            'name': schema.name,
            'description': schema.description,
            'version': schema.version,
            'format': schema.format,
            'encoding': schema.encoding,
            'delimiter': schema.delimiter,
            'include_headers': schema.include_headers,
            'tables': []
        }
        
        for table in schema.tables or []:
            table_dict = {
                'table_name': table.table_name,
                'export_name': table.export_name,
                'sort_by': table.sort_by,
                'filters': table.filters,
                'fields': []
            }
            
            for field in table.fields:
                field_dict = {
                    'source_field': field.source_field,
                    'target_field': field.target_field,
                    'data_type': field.data_type,
                    'format': field.format,
                    'default_value': field.default_value,
                    'transform': field.transform
                }
                table_dict['fields'].append(field_dict)
            
            schema_dict['tables'].append(table_dict)
        
        return jsonify({
            'success': True,
            'schema': schema_dict
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/export/preview', methods=['POST'])
def preview_export():
    """Preview export data without creating files."""
    if not db_browser:
        return jsonify({'success': False, 'error': 'No database connected'})
    
    try:
        data = request.get_json()
        schema_name = data.get('schema_name')
        limit = data.get('limit', 10)
        
        if not schema_name:
            return jsonify({'success': False, 'error': 'Schema name is required'})
        
        loader = ExportSchemaLoader()
        schema = loader.get_schema(schema_name)
        
        if not schema:
            return jsonify({'success': False, 'error': 'Schema not found'})
        
        # Validate schema
        errors = loader.validate_schema(schema)
        if errors:
            return jsonify({'success': False, 'error': 'Schema validation failed', 'validation_errors': errors})
        
        # Create export engine and preview data
        engine = ExportEngine(db_browser.db_path)
        preview_result = engine.preview_export(schema, limit)
        
        return jsonify(preview_result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/export/execute', methods=['POST'])
def execute_export():
    """Execute export and create files."""
    if not db_browser:
        return jsonify({'success': False, 'error': 'No database connected'})
    
    try:
        data = request.get_json()
        schema_name = data.get('schema_name')
        output_dir = data.get('output_dir', 'exports')
        
        if not schema_name:
            return jsonify({'success': False, 'error': 'Schema name is required'})
        
        loader = ExportSchemaLoader()
        schema = loader.get_schema(schema_name)
        
        if not schema:
            return jsonify({'success': False, 'error': 'Schema not found'})
        
        # Validate schema
        errors = loader.validate_schema(schema)
        if errors:
            return jsonify({'success': False, 'error': 'Schema validation failed', 'validation_errors': errors})
        
        # Create export engine and execute export
        engine = ExportEngine(db_browser.db_path)
        result = engine.export_data(schema, output_dir)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/export/download/<filename>', methods=['GET'])
def download_export_file(filename):
    """Download an exported file."""
    from flask import send_file
    import os.path
    
    try:
        # Security: only allow files from exports directory
        exports_dir = Path('exports')
        file_path = exports_dir / filename
        
        # Check if file exists and is in the exports directory
        if not file_path.exists() or not str(file_path.resolve()).startswith(str(exports_dir.resolve())):
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        # Determine mime type based on extension
        mime_type = 'application/octet-stream'
        if filename.endswith('.csv'):
            mime_type = 'text/csv'
        elif filename.endswith('.json'):
            mime_type = 'application/json'
        elif filename.endswith('.xml'):
            mime_type = 'application/xml'
        elif filename.endswith('.xlsx'):
            mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif filename.endswith('.sql'):
            mime_type = 'application/sql'
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype=mime_type
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/export/download-all', methods=['POST'])
def download_all_export_files():
    """Create and download a ZIP file containing all files from the latest export of a schema."""
    import zipfile
    import tempfile
    import glob
    from flask import send_file
    
    try:
        data = request.get_json()
        schema = data.get('schema')
        format_type = data.get('format')
        
        if not schema or not format_type:
            return jsonify({'success': False, 'error': 'Schema and format are required'}), 400
        
        exports_dir = Path('exports')
        if not exports_dir.exists():
            return jsonify({'success': False, 'error': 'No exports directory found'}), 404
        
        # Find all files that match the schema pattern (most recent export)
        # Pattern: *_{schema}_{timestamp}.{extension}
        pattern = f"*_{schema}_*.{format_type}" if format_type == 'csv' else f"*_{schema}_*.*"
        
        # Get all matching files and find the most recent timestamp group
        matching_files = list(exports_dir.glob(pattern))
        
        if not matching_files:
            return jsonify({'success': False, 'error': f'No export files found for schema {schema}'}), 404
        
        # Group files by timestamp (assuming format: prefix_schema_timestamp.ext)
        timestamp_groups = {}
        for file_path in matching_files:
            # Extract timestamp from filename: table_schema_timestamp.ext
            parts = file_path.stem.split('_')
            if len(parts) >= 3:
                timestamp = parts[-1]  # Last part should be timestamp
                if timestamp not in timestamp_groups:
                    timestamp_groups[timestamp] = []
                timestamp_groups[timestamp].append(file_path)
        
        # Get the most recent timestamp group
        if not timestamp_groups:
            return jsonify({'success': False, 'error': f'No valid export files found for schema {schema}'}), 404
        
        latest_timestamp = max(timestamp_groups.keys())
        files_to_zip = timestamp_groups[latest_timestamp]
        
        # Create temporary ZIP file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_zip:
            with zipfile.ZipFile(tmp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in files_to_zip:
                    zipf.write(file_path, file_path.name)
            
            # Generate ZIP filename
            zip_filename = f"{schema}_export_{format_type}_{latest_timestamp}.zip"
            
            # Send the ZIP file
            return send_file(
                tmp_zip.name,
                as_attachment=True,
                download_name=zip_filename,
                mimetype='application/zip'
            )
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/export/download-selected', methods=['POST'])
def download_selected_export_files():
    """Create and download a ZIP file containing selected export files."""
    import zipfile
    import tempfile
    from flask import send_file
    
    try:
        data = request.get_json()
        selected_files = data.get('files', [])
        
        if not selected_files:
            return jsonify({'success': False, 'error': 'No files selected'}), 400
        
        exports_dir = Path('exports')
        if not exports_dir.exists():
            return jsonify({'success': False, 'error': 'No exports directory found'}), 404
        
        # Validate all selected files exist and are in the exports directory
        files_to_zip = []
        for filename in selected_files:
            file_path = exports_dir / filename
            if not file_path.exists() or not str(file_path.resolve()).startswith(str(exports_dir.resolve())):
                return jsonify({'success': False, 'error': f'File not found or invalid: {filename}'}), 404
            files_to_zip.append(file_path)
        
        # Create temporary ZIP file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_zip:
            with zipfile.ZipFile(tmp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in files_to_zip:
                    zipf.write(file_path, file_path.name)
            
            # Generate ZIP filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"selected_exports_{timestamp}.zip"
            
            # Send the ZIP file
            return send_file(
                tmp_zip.name,
                as_attachment=True,
                download_name=zip_filename,
                mimetype='application/zip'
            )
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/export/files', methods=['GET'])
def list_export_files():
    """List available export files."""
    try:
        exports_dir = Path('exports')
        if not exports_dir.exists():
            exports_dir.mkdir(exist_ok=True)
            return jsonify({'success': True, 'files': []})
        
        files = []
        for file_path in exports_dir.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    'filename': file_path.name,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'extension': file_path.suffix.lower()
                })
        
        # Sort by modification date, newest first
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'success': True,
            'files': files
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    # Default to multi_entity_demo.db to showcase diverse banking patterns
    default_db = 'data/multi_entity_demo.db'
    if not Path(default_db).exists():
        # Fallback to syfi_bank3.db for backward compatibility
        default_db = 'data/syfi_bank3.db'
        if not Path(default_db).exists():
            default_db = 'syfi_bank3.db'
    
    if Path(default_db).exists():
        db_browser = DatabaseBrowser(default_db)
        current_database = default_db
        print(f"🏦 SyFi AI Web Interface Connected to: {default_db}")
        if 'multi_entity' in default_db:
            print("✨ Showcasing multi-entity banking patterns:")
            print("   • Middle Income Suburban Family")  
            print("   • Small Local Restaurant Business")
            print("   • Local Supermarket")
            print("   • Large Non-Profit Organization")
        print(f"🌐 Web interface available at: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)