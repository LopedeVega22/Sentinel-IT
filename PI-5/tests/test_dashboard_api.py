import os
import sys
import unittest
import base64
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Mock AWSMqttClient before importing dashboard_soc to avoid AWS connection attempts
import aws_connector
aws_connector.AWSMqttClient = MagicMock()

# Set environment variables for testing
os.environ['DASHBOARD_USER'] = 'admin'
os.environ['DASHBOARD_PASSWORD'] = 'testpass'

from dashboard_soc import app

class TestDashboardAPI(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Create auth header
        auth_string = "admin:testpass"
        self.auth_headers = {
            'Authorization': 'Basic ' + base64.b64encode(auth_string.encode('ascii')).decode('ascii')
        }

    @patch('dashboard_soc.get_logs')
    @patch('dashboard_soc.get_db_stats')
    def test_api_data_returns_200(self, mock_db_stats, mock_logs):
        # Mocking database calls to return empty/default values
        mock_logs.return_value = []
        mock_db_stats.return_value = (0, 0, 0, "No activity")
        
        response = self.client.get('/api/data', headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)
        
        data = response.get_json()
        self.assertIn('logs', data)
        self.assertIn('total_logs', data)
        self.assertIn('threat_level', data)

    @patch('dashboard_soc.get_logs')
    @patch('dashboard_soc.get_db_stats')
    def test_index_returns_200(self, mock_db_stats, mock_logs):
        mock_logs.return_value = []
        mock_db_stats.return_value = (0, 0, 0, "No activity")
        
        response = self.client.get('/', headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sentinel-IT', response.data)

if __name__ == '__main__':
    unittest.main()
