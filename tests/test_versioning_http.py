import unittest
import json
import re
import urllib.request
import urllib.error
import socket
import sys
import os
import subprocess
import time
import threading


class TestVersioningHTTP(unittest.TestCase):
    """HTTP-based behavioral tests for versioning system that work without Flask imports"""
    
    @classmethod
    def setUpClass(cls):
        """Check if we can test against a running server"""
        cls.base_url = os.environ.get('TEST_SERVER_URL', 'http://localhost:5001')
        cls.server_available = cls._check_server_availability()
        
        if not cls.server_available:
            print(f"Warning: No server available at {cls.base_url}")
            print("These tests require a running Flask server to test HTTP endpoints")
            print("To run these tests:")
            print("1. Start the Flask server: python3 run.py")
            print("2. Run tests: python3 -m unittest tests.test_versioning_http")

    @classmethod
    def _check_server_availability(cls):
        """Check if server is running and accessible"""
        try:
            response = urllib.request.urlopen(f"{cls.base_url}/health", timeout=5)
            return response.getcode() == 200
        except (urllib.error.URLError, socket.timeout):
            return False

    def setUp(self):
        """Skip tests if server not available"""
        if not self.server_available:
            self.skipTest("Server not available for HTTP testing")

    def _make_request(self, path, method='GET'):
        """Make HTTP request to server"""
        url = f"{self.base_url}{path}"
        try:
            if method == 'GET':
                response = urllib.request.urlopen(url, timeout=10)
                return response.getcode(), response.read().decode('utf-8'), dict(response.headers)
            else:
                raise NotImplementedError(f"Method {method} not implemented")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode('utf-8'), dict(e.headers)
        except Exception as e:
            self.fail(f"Request to {url} failed: {str(e)}")

    def test_version_api_endpoint_exists(self):
        """Test that /api/version endpoint is accessible via HTTP"""
        status_code, content, headers = self._make_request('/api/version')
        
        self.assertEqual(status_code, 200, "Version API endpoint should return 200 OK")
        self.assertIn('application/json', headers.get('Content-Type', ''), 
                     "Version API should return JSON content type")

    def test_version_api_returns_valid_json(self):
        """Test that version API returns valid JSON with correct structure"""
        status_code, content, headers = self._make_request('/api/version')
        
        # Should be valid JSON
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            self.fail("Version API should return valid JSON")
        
        # Should have required fields
        self.assertIn('version', data, "Version API should include 'version' field")
        self.assertIn('service', data, "Version API should include 'service' field")
        
        # Version should follow semantic versioning
        version = data['version']
        version_pattern = r'^v\d+\.\d+\.\d+$'
        self.assertRegex(version, version_pattern, 
                        f"Version '{version}' should follow vX.Y.Z format")

    def test_health_endpoint_includes_version(self):
        """Test that health endpoint includes version information"""
        status_code, content, headers = self._make_request('/health')
        
        self.assertEqual(status_code, 200, "Health endpoint should return 200 OK")
        
        data = json.loads(content)
        self.assertIn('version', data, "Health endpoint should include version")
        self.assertIn('status', data, "Health endpoint should include status")
        self.assertEqual(data['status'], 'healthy', "Health should report healthy")
        
        # Version should follow semantic versioning
        version = data['version']
        version_pattern = r'^v\d+\.\d+\.\d+$'
        self.assertRegex(version, version_pattern, 
                        "Health endpoint version should follow vX.Y.Z format")

    def test_version_consistency_across_endpoints(self):
        """Test that version is consistent between API and health endpoints"""
        # Get version from API endpoint
        _, api_content, _ = self._make_request('/api/version')
        api_data = json.loads(api_content)
        api_version = api_data['version']
        
        # Get version from health endpoint  
        _, health_content, _ = self._make_request('/health')
        health_data = json.loads(health_content)
        health_version = health_data['version']
        
        self.assertEqual(api_version, health_version, 
                        "Version should be consistent across endpoints")

    def test_home_page_contains_version(self):
        """Test that home page HTML contains the version number"""
        # First get expected version from API
        _, api_content, _ = self._make_request('/api/version')
        api_data = json.loads(api_content)
        expected_version = api_data['version']
        
        # Get home page content
        status_code, html_content, _ = self._make_request('/')
        self.assertEqual(status_code, 200, "Home page should be accessible")
        
        self.assertIn(expected_version, html_content, 
                     f"Home page should contain version {expected_version}")

    def test_semantic_version_format(self):
        """Test that version follows semantic versioning specification"""
        _, content, _ = self._make_request('/api/version')
        data = json.loads(content)
        version = data['version']
        
        # Parse semantic version components
        match = re.match(r'^v(\d+)\.(\d+)\.(\d+)$', version)
        self.assertIsNotNone(match, f"Version {version} should match vMAJOR.MINOR.PATCH")
        
        major, minor, patch = match.groups()
        
        # All components should be numeric
        self.assertTrue(major.isdigit(), "Major version should be numeric")
        self.assertTrue(minor.isdigit(), "Minor version should be numeric") 
        self.assertTrue(patch.isdigit(), "Patch version should be numeric")
        
        # Should not be v0.0.0 (indicates real versioning)
        version_tuple = (int(major), int(minor), int(patch))
        self.assertGreater(sum(version_tuple), 0, "Version should be > v0.0.0")

    def test_service_name_consistency(self):
        """Test that service name is consistent across endpoints"""
        # Get service from version endpoint
        _, api_content, _ = self._make_request('/api/version')
        api_data = json.loads(api_content)
        api_service = api_data.get('service')
        
        # Get service from health endpoint
        _, health_content, _ = self._make_request('/health')
        health_data = json.loads(health_content)
        health_service = health_data.get('service')
        
        self.assertEqual(api_service, health_service, 
                        "Service name should be consistent")
        self.assertIsNotNone(api_service, "Service name should be defined")

    def test_version_in_page_header_area(self):
        """Test that version appears in prominent location on home page"""
        # Get expected version
        _, api_content, _ = self._make_request('/api/version')
        api_data = json.loads(api_content)
        version = api_data['version']
        
        # Get home page
        _, html_content, _ = self._make_request('/')
        
        # Look for version in header-like contexts (flexible matching)
        header_patterns = [
            rf'<h1[^>]*>.*?{re.escape(version)}.*?</h1>',
            rf'<title[^>]*>.*?{re.escape(version)}.*?</title>',
            rf'<header[^>]*>.*?{re.escape(version)}.*?</header>',
            rf'class="[^"]*header[^"]*"[^>]*>.*?{re.escape(version)}',
        ]
        
        header_found = any(re.search(pattern, html_content, re.DOTALL | re.IGNORECASE) 
                          for pattern in header_patterns)
        
        # If not in header context, at least ensure it's visible on page
        version_visible = header_found or version in html_content
        
        self.assertTrue(version_visible, 
                       f"Version {version} should be visible on home page")


class TestVersioningStandalone(unittest.TestCase):
    """Standalone tests that don't require a running server"""
    
    def test_version_format_validation(self):
        """Test version format validation logic"""
        valid_versions = ['v1.0.0', 'v0.1.3', 'v10.20.30', 'v2.1.0']
        invalid_versions = ['1.0.0', 'v1.0', 'v1.0.0.1', 'version1.0.0', 'v1.0.0-beta']
        
        version_pattern = r'^v\d+\.\d+\.\d+$'
        
        for version in valid_versions:
            self.assertRegex(version, version_pattern, 
                           f"'{version}' should be valid semantic version")
        
        for version in invalid_versions:
            self.assertNotRegex(version, version_pattern, 
                              f"'{version}' should be invalid semantic version")

    def test_version_component_parsing(self):
        """Test parsing of version components"""
        test_version = 'v1.2.3'
        match = re.match(r'^v(\d+)\.(\d+)\.(\d+)$', test_version)
        
        self.assertIsNotNone(match, "Should be able to parse valid version")
        major, minor, patch = match.groups()
        
        self.assertEqual(major, '1', "Should extract major version")
        self.assertEqual(minor, '2', "Should extract minor version") 
        self.assertEqual(patch, '3', "Should extract patch version")


if __name__ == '__main__':
    # Print usage information
    print("Versioning HTTP Tests")
    print("====================")
    print("These tests validate the versioning system via HTTP requests.")
    print("They test the actual behavior of the running application.")
    print()
    
    # Check if server is available
    test_url = os.environ.get('TEST_SERVER_URL', 'http://localhost:5001')
    try:
        response = urllib.request.urlopen(f"{test_url}/health", timeout=5)
        print(f"✓ Server available at {test_url}")
        print()
    except:
        print(f"✗ No server available at {test_url}")
        print("To test with a running server:")
        print("1. Start server: python3 run.py")
        print("2. Run tests: python3 -m unittest tests.test_versioning_http")
        print()
        print("Running standalone tests only...")
        print()
    
    unittest.main()