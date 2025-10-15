# Python Project Instructions

This is a Python project with a basic structure for development.

## Project Structure

- `main.py` - Main entry point
- `src/` - Source code directory  
- `tests/` - Test directory
- `requirements.txt` - Python dependencies
- `.gitignore` - Git ignore file
- `README.md` - Project documentation

## Virtual Environment activiation
Activate the virtual environment with:
```bash
source .venv/bin/activate
```

## Running the Project

Use the VS Code task "Run Python Project" or run from terminal:
```bash
/home/orlando/Projects/syfi-ai/.venv/bin/python main.py
```

## Testing

Run tests with:
```bash
/home/orlando/Projects/syfi-ai/.venv/bin/python -m pytest tests/ -v
```

Work through each checklist item systematically.
Keep communication concise and focused.
Follow development best practices.
Utilize Gang of Four design patterns where applicable.
Apply the Don't Repeat Yourself (DRY) principle to avoid code duplication.
Adhere to Core Principles of software design, including: Separation of Concerns, Single Responsibility Principle, and Interface Segregation Principle, Open/Closed Principle, and Dependency Inversion Principle, Liskov Substitution Principle.

## Git Workflow and Branch Management

### Branch Naming Convention
**CRITICAL**: All feature branches must follow the standardized naming convention for consistent project management.

#### Required Branch Naming Pattern
```
feature/issue-{number}-{brief-description}
```

#### Examples
- `feature/issue-10-production-hardening` - Production hardening implementation
- `feature/issue-5-improve-test-coverage` - Test coverage improvements
- `feature/issue-1-story-redesign-home-page-for-improved-user-experie` - UI redesign work

#### Branch Management Rules
1. **Issue-Based Development**: Every feature branch must correspond to a GitHub issue
2. **Descriptive Names**: Use kebab-case with clear, concise descriptions
3. **Consistent Prefixes**: Always use `feature/issue-{number}-` prefix
4. **Length Consideration**: Keep descriptions brief but meaningful
5. **No Direct Main Commits**: All changes must go through feature branches and pull requests

#### Workflow Steps
```bash
# Create new feature branch from main
git checkout main
git pull origin main
git checkout -b feature/issue-{number}-{description}

# Rename existing branch if needed
git branch -m old-branch-name feature/issue-{number}-{description}

# Work on feature, commit changes
git add .
git commit -m "feat(issue-{number}): implement feature description"

# Push feature branch
git push origin feature/issue-{number}-{description}
```

Code changes should be tested and verified using existing test suites. If a test suite does not exist for the changed code, create one.

## Database Schema Management Guidelines

### Schema-Aware Development Rules
**CRITICAL**: All database operations must be schema-aware to prevent runtime errors due to missing tables/columns.

#### Database Access Pattern
```python
# ❌ AVOID: Direct hardcoded database queries
cursor.execute("SELECT status FROM accounts WHERE account_id = ?", (id,))

# ✅ PREFER: Schema-aware database access
from src.syfi.database.schema_aware_db import SchemaAwareConnection
db = SchemaAwareConnection(db_path)
if db.column_exists('accounts', 'status'):
    # Use status column
else:
    # Fallback logic or use alternative columns
```

#### Required Practices
1. **Always Check Table Existence**: Use `db.table_exists(table_name)` before queries
2. **Validate Column Availability**: Use `db.column_exists(table, column)` for optional columns  
3. **Provide Graceful Fallbacks**: Handle missing tables/columns without crashing
4. **Use Adaptive Queries**: Build queries that work with different schema versions
5. **Schema Version Compatibility**: Test code against multiple schema versions

#### Schema Evolution Strategy
- **Required Columns**: Must exist in all schema versions (customer_id, account_id, etc.)
- **Optional Columns**: May not exist (status, is_active, profile_description, etc.)  
- **Legacy Support**: Code must work with minimal and extended schemas
- **Migration Path**: Use `SchemaManager` for version detection and validation

#### Testing Requirements  
- **Multi-Schema Tests**: Test components against different database schemas
- **Missing Column Tests**: Verify graceful handling of missing optional columns
- **Empty Database Tests**: Ensure components work with minimal/empty schemas
- **Schema Validation**: Validate expected vs actual schema before operations

#### Common Schema Variations
```python
# Account Status: Multiple possible column names
status_column = 'status' if db.column_exists('accounts', 'status') else 'is_active' 

# Customer Profiles: Optional advanced columns
has_profiles = db.column_exists('customers', 'profile_description')

# Transaction Dates: May use different date column names  
date_column = 'transaction_date' if db.column_exists('transactions', 'transaction_date') else 'created_date'
```

### Schema Manager Usage
```python
from src.syfi.database.schema_manager import get_schema_manager, SCHEMA_DEFINITIONS

# Validate compatibility before operations
schema_manager = get_schema_manager(db_path)
required_schema = SCHEMA_DEFINITIONS[SchemaVersion.V1_2_ENHANCED]
issues = schema_manager.validate_schema_compatibility(required_schema)

if issues['missing_tables'] or issues['missing_columns']:
    # Handle schema incompatibility gracefully
    logger.warning(f"Schema compatibility issues: {issues}")
```

Code changes should be tested and verified using existing test suites. If a test suite does not exist for the changed code, create one.

## Production Hardening Guidelines

### Error Handling & Resilience Standards
**CRITICAL**: All code must implement enterprise-grade error handling and resilience patterns.

#### Exception Handling Framework
```python
# ✅ PREFER: Custom SyFi exceptions with context
from src.syfi.exceptions import SyFiDatabaseError, SyFiValidationError, SyFiConfigurationError

try:
    # Database operation
    result = db.safe_execute(query, params)
except sqlite3.Error as e:
    raise SyFiDatabaseError(f"Database query failed: {query}") from e
except Exception as e:
    raise SyFiUnexpectedError("Unexpected error during operation") from e
```

#### Required Error Handling Practices
1. **Custom Exception Hierarchy**: Use SyFi-specific exceptions with context preservation
2. **Graceful Degradation**: Provide meaningful fallbacks for non-critical failures
3. **Input Validation**: Validate all inputs before processing with clear error messages
4. **Resource Cleanup**: Ensure proper cleanup in finally blocks or context managers
5. **Circuit Breakers**: Implement circuit breaker patterns for external dependencies

### Logging & Monitoring Standards
**CRITICAL**: Replace all print statements with structured logging.

#### Structured Logging Pattern
```python
# ❌ AVOID: Print statements
print(f"Processing {count} records")

# ✅ PREFER: Structured logging with context
import logging
logger = logging.getLogger(__name__)

logger.info("Processing records", extra={
    "operation": "data_processing",
    "record_count": count,
    "correlation_id": request_id,
    "performance": {
        "start_time": start_time.isoformat(),
        "duration_ms": duration_ms
    }
})
```

#### Required Logging Practices
1. **Structured JSON Logs**: Use structured logging with consistent field names
2. **Correlation IDs**: Include correlation IDs for request tracing across components
3. **Performance Metrics**: Log operation timing and resource usage
4. **Error Context**: Include full error context with stack traces for debugging
5. **Audit Trail**: Log all data access, modifications, and export operations

### Security & Validation Standards
**CRITICAL**: All inputs must be validated and sanitized for security.

#### Input Security Pattern
```python
# ✅ PREFER: Comprehensive input validation
from src.syfi.security import validate_input, sanitize_path, prevent_sql_injection

def process_export_request(table_name: str, file_path: str):
    # Validate table name against whitelist
    if not validate_input.is_valid_table_name(table_name):
        raise SyFiValidationError(f"Invalid table name: {table_name}")
    
    # Sanitize file path to prevent directory traversal
    safe_path = sanitize_path(file_path)
    
    # Use parameterized queries to prevent SQL injection
    query = "SELECT * FROM ? WHERE status = ?"
    # Note: Table names can't be parameterized, so validate against whitelist
```

#### Required Security Practices
1. **Input Validation**: Validate all user inputs against defined schemas and business rules
2. **SQL Injection Prevention**: Use parameterized queries and input sanitization
3. **Path Traversal Protection**: Validate and sanitize all file path operations
4. **Data Encryption**: Encrypt sensitive data at rest using appropriate encryption
5. **Access Control**: Implement role-based access control for all operations

### Performance & Optimization Standards
**CRITICAL**: All code must handle enterprise-scale datasets efficiently.

#### Performance Pattern
```python
# ✅ PREFER: Streaming and caching for large datasets
from src.syfi.performance import CacheManager, StreamingProcessor

cache = CacheManager()
processor = StreamingProcessor(batch_size=1000)

# Cache frequently accessed schema metadata
@cache.memoize(ttl=300)  # 5 minute cache
def get_table_schema(table_name):
    return db.get_table_info(table_name)

# Stream process large datasets
def process_large_export(query, file_path):
    with processor.stream_query(query) as stream:
        with open(file_path, 'w') as f:
            for batch in stream:
                # Process batch without loading entire dataset in memory
                processed_batch = transform_batch(batch)
                write_batch_to_file(f, processed_batch)
```

#### Required Performance Practices
1. **Memory Efficiency**: Use streaming for large datasets to prevent memory exhaustion
2. **Database Optimization**: Implement connection pooling and query optimization
3. **Caching Strategy**: Cache frequently accessed data with appropriate TTL
4. **Resource Monitoring**: Monitor memory, CPU, and I/O usage during operations
5. **Load Testing**: Validate performance under enterprise-scale load scenarios

### Configuration & Environment Standards
**CRITICAL**: All configuration must be environment-aware and secure.

#### Configuration Management Pattern
```python
# ✅ PREFER: Environment-aware configuration
from src.syfi.config import get_config, Environment

config = get_config()

# Environment-specific settings
if config.environment == Environment.PRODUCTION:
    log_level = "WARNING"
    enable_debug_features = False
elif config.environment == Environment.DEVELOPMENT:
    log_level = "DEBUG"
    enable_debug_features = True

# Secure credential handling
database_url = config.get_secret("DATABASE_URL")  # From secure store
api_key = config.get_secret("API_KEY")  # Never log or expose
```

#### Required Configuration Practices
1. **Environment Separation**: Separate configuration for dev/test/prod environments
2. **Secret Management**: Store sensitive configuration in secure credential stores
3. **Feature Flags**: Use feature flags for gradual rollout of new functionality
4. **Configuration Validation**: Validate all configuration at startup with clear errors
5. **Hot Reload**: Support runtime configuration updates without service restart

### Testing & Quality Assurance Standards
**CRITICAL**: All production code must have comprehensive test coverage.

#### Production Testing Pattern
```python
# ✅ PREFER: Comprehensive test coverage with production scenarios
import pytest
from src.syfi.testing import load_test, security_test, performance_test

class TestProductionScenarios:
    @load_test(concurrent_users=10, duration="60s")
    def test_concurrent_export_operations(self):
        """Test system handles concurrent export operations without degradation."""
        
    @security_test(inputs=["malicious_sql", "path_traversal", "xss_payload"])
    def test_input_validation_security(self, malicious_input):
        """Test system properly validates and sanitizes malicious inputs."""
        
    @performance_test(dataset_size=100000, max_duration="30s")
    def test_large_dataset_performance(self):
        """Test system processes large datasets within performance targets."""
```

#### Required Testing Practices
1. **Load Testing**: Test with enterprise-scale data volumes and concurrent users
2. **Security Testing**: Test against common security vulnerabilities and attack vectors
3. **Performance Testing**: Validate performance targets under realistic load conditions
4. **Integration Testing**: Test complete workflows across all system components
5. **Monitoring Testing**: Validate that monitoring and alerting systems function correctly

### Deployment & Operations Standards
**CRITICAL**: All deployments must support zero-downtime updates and monitoring.

#### Operational Pattern
```python
# ✅ PREFER: Health checks and monitoring endpoints
from src.syfi.monitoring import HealthChecker, MetricsCollector

health_checker = HealthChecker()
metrics = MetricsCollector()

@app.route("/health")
def health_check():
    """Health check endpoint for load balancer and monitoring."""
    status = health_checker.check_all_systems()
    return jsonify(status), 200 if status["healthy"] else 503

@app.route("/metrics")
def metrics_endpoint():
    """Metrics endpoint for monitoring system performance."""
    return jsonify(metrics.get_current_metrics())
```

#### Required Operational Practices
1. **Health Checks**: Implement comprehensive health check endpoints for all services
2. **Metrics Collection**: Collect and expose key performance and business metrics
3. **Graceful Shutdown**: Handle shutdown signals gracefully with proper cleanup
4. **Rolling Deployments**: Support zero-downtime deployments with proper validation
5. **Monitoring Integration**: Integrate with monitoring and alerting systems

Code changes should be tested and verified using existing test suites. If a test suite does not exist for the changed code, create one.

## Web Application Design Guidelines

### Design Philosophy
SyFi AI is a professional financial data generation tool. All web interfaces must reflect the trustworthy, sophisticated aesthetic of a modern fintech serving financial institutions using the established Radar Blue color palette.

### Visual Design Standards

#### Color Palette (Radar Blue Theme)
Use CSS custom properties from `base.css`:
- **Primary Colors**:
  - `var(--radar-blue-primary)`: `#b6c8e4` (main brand blue)
  - `var(--radar-blue-dark)`: `#1a2e5c` (headers, emphasis)
  - `var(--radar-blue-medium)`: `#7494ca` (accents, links)
  - `var(--radar-blue-light)`: `#e8eef7` (backgrounds)
  - `var(--radar-blue-lighter)`: `#f8fafc` (page backgrounds)
  - `var(--radar-accent)`: `#9bb2d9` (subtle accents)
- **Text Colors**:
  - Primary: `var(--text-primary)` (`#2c3e50`)
  - Secondary: `var(--text-secondary)` (`#64748b`)
- **Status Colors**:
  - Success: `var(--success)` (`#10b981`)
  - Warning: `var(--warning)` (`#f59e0b`)
  - Danger: `var(--danger)` (`#ef4444`)
- **Card Backgrounds**: `rgba(255, 255, 255, 0.95)` with backdrop-filter blur

#### Typography
- **Font Stack**: `'Montserrat', 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif`
- **Font Imports**: Always include Montserrat from Google Fonts
- **Preconnect**: Include `preconnect` links for performance
- **Hierarchy**: 
  - Page titles: `2.25rem, font-weight: 300`
  - Section titles: `1.25rem, font-weight: 600`
  - Body text: `1rem, line-height: 1.6`
  - Small text: `0.875rem`
- **Code/Data**: Use monospace font for database names, file paths, technical identifiers

#### Layout Principles
- **Clean Grid**: Use Bootstrap's 12-column grid consistently
- **White Space**: Generous padding and margins for readability
- **Card-Based**: Group related content in subtle bordered cards
- **Professional Spacing**: 
  - Section padding: `2rem 0`
  - Card padding: `2rem`
  - Element margins: `1rem` to `1.5rem`

### Component Standards

#### Cards and Content Containers
```css
.card, .search-card, .builder-card {
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
    border: none;
    border-radius: 8px;
    overflow: hidden;
    backdrop-filter: blur(10px);
    background: rgba(255, 255, 255, 0.95);
}

.card-header {
    border: none;
    font-weight: 600;
    letter-spacing: -0.3px;
}

.card-header.bg-primary {
    background: var(--radar-blue-dark) !important;
    color: white;
}
```

#### Navigation and Tab Patterns
- Use Bootstrap nav-tabs with Font Awesome icons
- Structure: `<i class="fas fa-icon me-2"></i>Tab Label`
- Active states use radar blue colors
- Tab content in `.tab-content` containers

#### Status Indicators and Badges
- Database connection status with colored indicators
- Success states: `var(--success)` green
- Warning states: `var(--warning)` amber
- Error states: `var(--danger)` red
- Icons: Font Awesome with consistent sizing (`me-2` spacing)

#### Forms and Inputs
- Bootstrap form classes with custom focus styles
- Consistent `border-radius: 8px`
- Proper label hierarchy and required field indicators

### Interactive Elements

#### Buttons
- **Primary Actions**: Bootstrap `btn-primary` 
- **Secondary Actions**: `btn-outline-secondary`
- **Subtle Actions**: Custom styled links with hover effects
- **No Flashy Effects**: Minimal transitions (0.2s ease maximum)

#### Hover States
- Subtle elevation: `translateY(-2px)`
- Soft shadows: `rgba(0, 0, 0, 0.08)`
- Color changes should be minimal and professional

### Responsive Design
- **Mobile First**: Design for mobile, enhance for desktop
- **Breakpoints**: Follow Bootstrap's standard breakpoints
- **Hide Complexity**: Hide detailed stats on mobile, show essential info only
- **Touch Targets**: Minimum 44px for interactive elements

### Content Guidelines

#### Language and Tone
- **Professional**: Use banking/financial terminology appropriately
- **Clear**: Avoid jargon, explain technical concepts
- **Concise**: Short descriptions, bullet points over paragraphs
- **Action-Oriented**: Use verbs for buttons and links ("Manage", "View", "Export")

#### Data Display
- **Consistent Formatting**: Numbers, dates, and currencies
- **Loading States**: Show shimmer effects or spinners for async content
- **Empty States**: Provide helpful guidance when no data exists
- **Error States**: Clear, actionable error messages

### Forbidden Design Elements
❌ **Avoid These**:
- Bright gradients or flashy colors
- Complex animations or transitions
- Busy backgrounds or patterns  
- Multiple competing call-to-action buttons
- Inconsistent icon styles or sizes
- Comic or casual fonts
- Neon or high-contrast color schemes

### Page Structure Templates

#### Standard Page Structure
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Page Title - SyFi AI Database Browser</title>
    
    <!-- Font and CSS imports -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/base.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/shared_navigation_styles.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/page-specific.css') }}">
</head>
<body class="bg-light">
    {% include 'shared_navigation.html' %}
    
    <div class="container mt-4">
        <!-- Main card container -->
        <div class="card">
            <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                <h4 class="mb-0">
                    <i class="fas fa-icon me-2"></i>Page Title
                </h4>
            </div>
            <div class="card-body">
                <!-- Page content -->
            </div>
        </div>
    </div>
</body>
</html>
```

#### Tabbed Interface Pattern
```html
<!-- Tab Navigation -->
<ul class="nav nav-tabs nav-fill" id="mainTabs" role="tablist">
    <li class="nav-item" role="presentation">
        <button class="nav-link active" id="tab1" data-bs-toggle="tab" data-bs-target="#content1" type="button" role="tab">
            <i class="fas fa-icon me-2"></i>Tab Name
        </button>
    </li>
</ul>

<!-- Tab Content -->
<div class="tab-content" id="tabsContent">
    <div class="tab-pane fade show active" id="content1" role="tabpanel">
        <!-- Tab content -->
    </div>
</div>
```

### Implementation Notes
- Always include proper semantic HTML
- Ensure WCAG 2.1 AA accessibility compliance
- Test responsiveness on mobile devices
- Validate CSS for cross-browser compatibility
- Use consistent class naming conventions
- Include focus states for keyboard navigation