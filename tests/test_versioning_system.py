import unittest
import json
import re
from app import create_app


class TestVersioningSystem(unittest.TestCase):
    """Comprehensive behavioral tests for the application versioning system"""

    def setUp(self):
        """Set up test client"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        """Clean up test context"""
        self.ctx.pop()

    def test_version_api_endpoint_accessibility(self):
        """Test that /api/version endpoint is accessible and returns proper format"""
        response = self.client.get('/api/version')
        self.assertEqual(response.status_code, 200, "Version API should be accessible")
        self.assertEqual(response.content_type, 'application/json')
        
        data = json.loads(response.data)
        self.assertIn('version', data, "API response should contain version field")
        
        # Should match semantic versioning pattern
        version_pattern = r'^v\d+\.\d+\.\d+$'
        self.assertRegex(data['version'], version_pattern, 
                        f"API version '{data['version']}' should follow vX.Y.Z format")

    def test_health_endpoint_contains_version(self):
        """Test that health endpoint includes version information"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200, "Health endpoint should be accessible")
        self.assertEqual(response.content_type, 'application/json')
        
        data = json.loads(response.data)
        self.assertIn('version', data, "Health endpoint should include version")
        self.assertIn('status', data, "Health endpoint should include status")
        self.assertEqual(data['status'], 'healthy', "Health should report healthy status")
        
        # Version should follow semantic versioning
        version_pattern = r'^v\d+\.\d+\.\d+$'
        self.assertRegex(data['version'], version_pattern, 
                        "Health endpoint version should follow vX.Y.Z format")

    def test_version_consistency_between_endpoints(self):
        """Test that version is consistent between API and health endpoints"""
        # Get version from API endpoint
        api_response = self.client.get('/api/version')
        api_data = json.loads(api_response.data)
        api_version = api_data['version']
        
        # Get version from health endpoint
        health_response = self.client.get('/health')
        health_data = json.loads(health_response.data)
        health_version = health_data['version']
        
        self.assertEqual(api_version, health_version, 
                        "Version should be consistent between API and health endpoints")

    def test_home_page_displays_version(self):
        """Test that the home page displays the version number"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200, "Home page should be accessible")
        
        html_content = response.data.decode('utf-8')
        
        # Get expected version from API
        api_response = self.client.get('/api/version')
        api_data = json.loads(api_response.data)
        expected_version = api_data['version']
        
        self.assertIn(expected_version, html_content, 
                     f"Home page HTML should contain version {expected_version}")

    def test_version_format_is_semantic(self):
        """Test that version follows semantic versioning specification"""
        response = self.client.get('/api/version')
        data = json.loads(response.data)
        version = data['version']
        
        # Parse semantic version components
        match = re.match(r'^v(\d+)\.(\d+)\.(\d+)$', version)
        self.assertIsNotNone(match, f"Version {version} should match vMAJOR.MINOR.PATCH")
        
        major, minor, patch = match.groups()
        
        # All parts should be valid integers
        self.assertTrue(major.isdigit(), "Major version should be numeric")
        self.assertTrue(minor.isdigit(), "Minor version should be numeric") 
        self.assertTrue(patch.isdigit(), "Patch version should be numeric")
        
        # Should not be v0.0.0 (indicates actual versioning)
        version_tuple = (int(major), int(minor), int(patch))
        self.assertGreater(sum(version_tuple), 0, "Version should be greater than v0.0.0")

    def test_version_appears_in_page_header(self):
        """Test that version is prominently displayed on the home page"""
        response = self.client.get('/')
        html_content = response.data.decode('utf-8')
        
        # Get version from API
        api_response = self.client.get('/api/version')
        api_data = json.loads(api_response.data)
        version = api_data['version']
        
        # Look for version in header contexts
        header_found = (
            re.search(rf'<h1[^>]*>.*{re.escape(version)}.*</h1>', html_content, re.DOTALL | re.IGNORECASE) or
            re.search(rf'<title[^>]*>.*{re.escape(version)}.*</title>', html_content, re.DOTALL | re.IGNORECASE) or
            re.search(rf'<header[^>]*>.*{re.escape(version)}.*</header>', html_content, re.DOTALL | re.IGNORECASE) or
            version in html_content  # Fallback: just ensure it's somewhere on the page
        )
        
        self.assertTrue(header_found, f"Version {version} should be visible on the home page")

    def test_api_json_structure(self):
        """Test that API endpoints return well-structured JSON"""
        # Test version API structure
        response = self.client.get('/api/version')
        data = json.loads(response.data)
        
        required_fields = ['version', 'service']
        for field in required_fields:
            self.assertIn(field, data, f"Version API should include {field} field")
        
        # Test health API structure  
        response = self.client.get('/health')
        data = json.loads(response.data)
        
        required_fields = ['status', 'service', 'version']
        for field in required_fields:
            self.assertIn(field, data, f"Health API should include {field} field")

    def test_version_endpoints_return_same_service_name(self):
        """Test that all endpoints identify the same service"""
        # Get service from version endpoint
        api_response = self.client.get('/api/version')
        api_data = json.loads(api_response.data)
        api_service = api_data.get('service')
        
        # Get service from health endpoint
        health_response = self.client.get('/health')
        health_data = json.loads(health_response.data)
        health_service = health_data.get('service')
        
        self.assertEqual(api_service, health_service, 
                        "Service name should be consistent across endpoints")
        self.assertIsNotNone(api_service, "Service name should be defined")


if __name__ == '__main__':
    unittest.main()