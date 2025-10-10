# SyFi AI Database Browser - Web Interface

A Flask-based web application for browsing and exploring SyFi AI SQLite databases through a user-friendly interface.

## Features

### 🔍 **Customer Search**
- Search by Customer ID, Name, Email, Phone, Address
- Search by Profile Description and Profile Metadata
- **Advanced Transaction Search**: Find customers by transaction volumes, amounts, and patterns
- Real-time search with partial matching (case-insensitive)
- Results limited to 100 customers for performance

### 📊 **Transaction-Based Search**
- **Amount Filters**: Min/max total transaction amounts for specified periods
- **Transaction Count Filters**: Find customers by number of transactions
- **Date Range Filtering**: Search within specific time periods
- **Transaction Type Filtering**: Filter by deposit, withdrawal, transfer, payment types
- **Quick Presets**: High-volume customers, frequent users, dormant accounts, recent activity
- **Flexible Sorting**: Sort by net amount, transaction count, credits, debits, or customer name

### 👤 **Customer Details View**
- Complete customer profile information
- Enhanced schema support (22 columns) with backward compatibility
- Customer demographics (age, occupation, education, income)
- Risk assessment (credit score, risk category)
- Profile metadata display with JSON formatting
- Account summary with count and transaction totals

### 🏦 **Account Management**
- List all customer accounts with balances and status
- Account type categorization (checking, savings, credit, loan)
- Active/inactive status indicators
- Interest rate display for applicable accounts
- Account creation dates and balance history

### 💳 **Account Details View**
- Complete account information and ownership
- Transaction summary statistics
- Last 50 transactions with type, amount, and descriptions
- Credit/debit transaction highlighting
- Running balance calculations
- Related transaction tracking

### 🗄️ **Multi-Database Support**
- Dynamic database selection from available .db files
- File size display for database selection
- Connection status indicators
- Schema compatibility across database versions

## Getting Started

### Prerequisites
- Python 3.8+
- SyFi AI project with virtual environment
- Flask 2.3+ (automatically installed)

### Quick Start

1. **Using the launcher script:**
   ```bash
   ./start_web_browser.sh
   ```

2. **Manual start:**
   ```bash
   source .venv/bin/activate
   python web_browser.py
   ```

3. **Open your browser:**
   - Navigate to http://localhost:5000
   - Or http://127.0.0.1:5000

### Database Connection

1. Select a database from the dropdown menu
2. Click "Connect" to establish connection
3. The status indicator will show connection state
4. Begin searching once connected

## Interface Guide

### Search Page
- **Basic Search**: Enter partial matches in any field
- **Advanced Search**: Use multiple criteria for refined results
- **Clear Form**: Reset all search fields
- **Results Table**: Click "View" to see customer details

### Customer Details
- **Profile Information**: Complete customer demographics
- **Account Overview**: Visual cards showing all accounts
- **Navigation**: Direct links to individual account details

### Account Details  
- **Account Summary**: Balance, status, and ownership info
- **Transaction Analytics**: Credits, debits, averages, totals
- **Transaction History**: Chronological list with descriptions
- **Customer Link**: Quick navigation back to customer profile

## Database Compatibility

### Supported Schemas
- **Legacy Schema**: 13-column customer table (backward compatible)
- **Enhanced Schema**: 22-column customer table with profiles
- **Account Variations**: Handles missing columns gracefully

### Supported Databases
- `syfi_banking.db` - Legacy format
- `profile_test.db` - Profile-only format
- `enhanced_demo.db` - Full enhanced schema
- `syfi_bank3.db` - Business case scenarios
- Any `.db` file in the project directory

## Technical Details

### Architecture
- **Backend**: Flask web framework
- **Frontend**: Bootstrap 5 + vanilla JavaScript
- **Database**: SQLite with dynamic schema detection
- **Templates**: Jinja2 templating engine

### Key Components
- `DatabaseBrowser` class: Core database operations
- Dynamic column detection for schema compatibility
- RESTful API endpoints for search and navigation
- Responsive design for desktop and mobile

### Security Features
- SQL injection protection via parameterized queries
- Input sanitization and validation
- Safe HTML rendering with auto-escaping
- Development server (not for production use)

### Performance Optimizations
- Search result limits (100 customers)
- Transaction history limits (50 most recent)
- Efficient JOIN queries for related data
- Connection pooling with proper cleanup

## API Endpoints

### Web Pages
- `GET /` - Main search interface
- `GET /customer/<id>` - Customer details page
- `GET /account/<id>` - Account details page

### API Endpoints
- `GET /api/databases` - List available database files
- `GET /connect/<db_name>` - Connect to specific database
- `GET /search?params` - Search customers with criteria

### Error Handling
- `GET /error` - Generic error page for invalid requests
- Custom 404/500 error handling
- Graceful schema compatibility fallbacks

## Troubleshooting

### Common Issues

**"Database not connected"**
- Select database from dropdown and click Connect
- Verify database file exists and is readable
- Check file permissions on .db files

**"No such column" errors**
- Database uses different schema version
- Web interface automatically handles most compatibility issues
- Check database structure with SQLite browser if needed

**"Import flask could not be resolved"**
- Ensure Flask is installed: `pip install flask`
- Activate virtual environment before starting
- Check requirements.txt for version compatibility

### Development Mode
- Flask runs in debug mode with auto-reload
- Error traces displayed in browser for debugging
- Console logs show request/response information
- Database connection state tracked globally

## Contributing

The web interface supports the complete SyFi AI ecosystem:
- Backward compatibility with all database formats
- Extensible search and filtering capabilities
- Mobile-responsive design principles
- Clean separation of concerns (MVC pattern)

For enhancements or bug reports, ensure compatibility with:
- Multiple database schema versions
- Various customer profile types
- Different account and transaction structures
- Cross-browser functionality (modern browsers)

## License

Part of the SyFi AI project - Synthetic Banking Data Generation and Analysis System.