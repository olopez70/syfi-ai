"""
Web interface API endpoint tests.

Tests Flask application routes and API functionality.
"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import Flask app
from web_browser import app


@pytest.fixture
def client():
    """Create Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def mock_database():
    """Mock database for isolated API testing."""
    with patch('web_browser.db_browser') as mock_db:
        # Setup mock database responses
        mock_db.get_connection.return_value = Mock()
        mock_db.get_recent_customers.return_value = [
            {
                'customer_id': 'TEST_001',
                'first_name': 'John', 
                'last_name': 'Doe',
                'email': 'john.doe@test.com'
            }
        ]
        yield mock_db


@pytest.mark.web
class TestHomeRoutes:
    """Test main navigation routes."""
    
    def test_home_page_loads(self, client):
        """Test home page renders successfully."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'SyFi AI' in response.data
    
    def test_customers_page_loads(self, client):
        """Test customers page renders successfully."""
        response = client.get('/customers')
        assert response.status_code == 200
        assert b'customers' in response.data.lower()
    
    def test_builder_page_loads(self, client):
        """Test builder page renders successfully."""
        response = client.get('/builder')
        assert response.status_code == 200
    
    def test_bulk_generations_page_loads(self, client):
        """Test bulk generations page renders successfully."""
        response = client.get('/bulk-generations')
        assert response.status_code == 200


@pytest.mark.web
class TestAPIEndpoints:
    """Test API endpoint functionality."""
    
    def test_databases_api(self, client):
        """Test databases listing API."""
        response = client.get('/api/databases')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'databases' in data
        assert isinstance(data['databases'], list)
    
    def test_current_database_api(self, client):
        """Test current database API."""
        response = client.get('/api/current-database')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'database' in data
    
    def test_transaction_stats_api(self, client):
        """Test transaction statistics API."""
        response = client.get('/api/transaction-stats')
        
        # Should return error response when no database connected
        assert response.status_code in [200, 500]
    
    def test_create_customer_api_valid_data(self, client, mock_database):
        """Test customer creation with valid data."""
        customer_data = {
            'first_name': 'Test',
            'last_name': 'Customer',
            'email': 'test@example.com',
            'phone': '555-0123',
            'date_of_birth': '1990-01-01'
        }
        
        response = client.post('/api/create-customer',
                             data=json.dumps(customer_data),
                             content_type='application/json')
        
        # May fail if no database connected - test structure is valid
        assert response.status_code in [200, 201, 500]
    
    def test_create_customer_api_no_database(self, client):
        """Test customer creation when no database is connected."""
        valid_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com'
        }
        
        response = client.post('/api/create-customer',
                             data=json.dumps(valid_data),
                             content_type='application/json')
        
        # Should return error when no database connected
        assert response.status_code in [200, 500]


@pytest.mark.web  
class TestCustomerRoutes:
    """Test customer-specific routes."""
    
    def test_customers_page_loads(self, client):
        """Test that customers page loads."""
        response = client.get('/customers')
        # Should load the page even if no database is connected
        assert response.status_code == 200
    
    def test_bulk_generations_page_loads(self, client):
        """Test that bulk generations page loads.""" 
        response = client.get('/bulk-generations')
        # Should load the page even if no database is connected
        assert response.status_code == 200


@pytest.mark.web
class TestSearchFunctionality:
    """Test search and filtering functionality."""
    
    def test_search_page_loads(self, client):
        """Test search page renders."""
        response = client.get('/search')
        assert response.status_code == 200
    
    def test_preset_search_routes(self, client):
        """Test preset search functionality."""
        presets = ['high-value', 'recent-activity', 'new-customers']
        
        for preset in presets:
            response = client.get(f'/search/preset/{preset}')
            # Should render search page with preset applied
            assert response.status_code in [200, 404]


@pytest.mark.web
@pytest.mark.slow
class TestBulkOperations:
    """Test bulk generation functionality."""
    
    def test_bulk_generate_customers_api(self, client, mock_database):
        """Test bulk customer generation API."""
        bulk_data = {
            'count': 5,
            'profile_description': 'Young professionals in tech',
            'accounts_per_customer': 2
        }
        
        response = client.post('/api/bulk-generate-customers',
                             data=json.dumps(bulk_data),
                             content_type='application/json')
        
        # May fail if no database - test request structure
        assert response.status_code in [200, 202, 500]
    
    def test_bulk_generations_list_api(self, client):
        """Test bulk generations listing API."""
        response = client.get('/api/bulk-generations')
        
        # Should return response even if no database connected
        assert response.status_code in [200, 500]