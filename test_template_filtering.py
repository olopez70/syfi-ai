#!/usr/bin/env python3
"""
Unit tests for template filtering functionality.
Tests the exact user flow: Profile Templates -> Template Card -> View Generated Profiles
"""

import sys
import os
import unittest
import json
from unittest.mock import patch, MagicMock

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the web browser module
import web_browser

class TestTemplateFiltering(unittest.TestCase):
    """Test template filtering functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = web_browser.app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
    @patch('web_browser.db_browser')
    def test_api_profiles_with_template_filter(self, mock_db):
        """Test that /api/profiles correctly filters by template_id"""
        
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock query results - simulate 5 profiles for Middle Income template
        mock_cursor.fetchall.return_value = [
            ('PROF001', 'Sarah Johnson', 'Middle class family profile', '2024-01-01', None, 
             'TMPL_56010319', 'Middle Income Suburban Family', 'Family', 'Personal',
             'CUST001', 'Johnson Family', 'Sarah', 'Johnson', None, 'sarah@example.com'),
            ('PROF002', 'Mike Johnson', 'Husband profile', '2024-01-01', None,
             'TMPL_56010319', 'Middle Income Suburban Family', 'Family', 'Personal', 
             'CUST002', 'Mike Johnson', 'Mike', 'Johnson', None, 'mike@example.com'),
            # ... would have 3 more profiles for total of 5
        ]
        
        # Test API call with template_id filter
        response = self.client.get('/api/profiles?template_id=TMPL_56010319')
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['profiles']), 2)  # Based on mock data
        
        # Verify the SQL query was called with template filter
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        # Check that template filter is in the query
        self.assertIn('AND p.template_id = ?', query)
        self.assertIn('TMPL_56010319', params)
        
    @patch('web_browser.db_browser')
    def test_api_profiles_without_template_filter(self, mock_db):
        """Test that /api/profiles returns all profiles when no template_id"""
        
        # Mock database setup
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock 20 total profiles across all templates
        mock_cursor.fetchall.return_value = [f'PROF{i:03d}' for i in range(1, 21)]
        
        # Test API call without template_id
        response = self.client.get('/api/profiles')
        
        # Verify template filter is NOT in the query
        call_args = mock_cursor.execute.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        self.assertNotIn('AND p.template_id = ?', query)
        self.assertEqual(len(params), 0)  # No template parameter
        
    def test_profile_details_page_with_template_params(self):
        """Test that profile-details page loads with template parameters"""
        
        response = self.client.get('/profile-details?template_id=TMPL_56010319&template_name=Middle%20Income%20Suburban%20Family')
        
        self.assertEqual(response.status_code, 200)
        # Check that the page contains the template name
        self.assertIn(b'Middle Income Suburban Family', response.data)


class TestUserFlowSimulation(unittest.TestCase):
    """Simulate the exact user flow with detailed logging"""
    
    def setUp(self):
        """Set up test client"""
        self.app = web_browser.app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
    def test_complete_user_flow_simulation(self):
        """
        Simulate: Navigation Bar -> Profile Templates -> Middle Income Card -> View Generated Profiles
        """
        print("\n=== USER FLOW SIMULATION ===")
        
        # Step 1: Load Profile Templates page
        print("Step 1: Loading /profiles page...")
        response1 = self.client.get('/profiles')
        self.assertEqual(response1.status_code, 200)
        print("✓ Profile Templates page loaded successfully")
        
        # Step 2: Click on Middle Income Suburban Family template card
        # This should navigate to profile-details with template parameters
        print("Step 2: Clicking Middle Income Suburban Family card...")
        template_url = '/profile-details?template_id=TMPL_56010319&template_name=Middle%20Income%20Suburban%20Family'
        response2 = self.client.get(template_url)
        self.assertEqual(response2.status_code, 200)
        print(f"✓ Template details page loaded: {template_url}")
        
        # Step 3: The page should auto-load profiles for this template
        # We need to mock the database for this test
        print("Step 3: Page should automatically call /api/profiles with template_id...")
        
        with patch('web_browser.db_browser') as mock_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_db.get_connection.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            
            # Simulate 5 profiles for Middle Income template
            mock_cursor.fetchall.return_value = [
                ('PROF001', 'Profile 1', 'Desc 1', '2024-01-01', None, 
                 'TMPL_56010319', 'Middle Income Suburban Family', 'Family', 'Personal',
                 'CUST001', 'Customer 1', 'First', 'Last', None, 'email@example.com'),
            ] * 5  # 5 identical profiles for simplicity
            
            # Step 4: Make the API call that JavaScript would make
            api_response = self.client.get('/api/profiles?template_id=TMPL_56010319')
            self.assertEqual(api_response.status_code, 200)
            
            data = json.loads(api_response.data)
            self.assertTrue(data['success'])
            print(f"✓ API returned {len(data['profiles'])} profiles")
            
            # Verify the query included template filter
            mock_cursor.execute.assert_called()
            call_args = mock_cursor.execute.call_args
            query = call_args[0][0]
            params = call_args[0][1] if len(call_args[0]) > 1 else []
            
            print(f"SQL Query executed: {query}")
            print(f"Parameters: {params}")
            
            if 'AND p.template_id = ?' in query and 'TMPL_56010319' in params:
                print("✓ Template filter correctly applied in SQL query")
            else:
                print("❌ Template filter NOT found in SQL query")
                self.fail("Template filter not applied correctly")
        
        print("=== USER FLOW SIMULATION COMPLETE ===\n")


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)