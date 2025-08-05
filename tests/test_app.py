import urllib.request
import urllib.error


class TestApp:
    def test_home_page_returns_200(self):
        """Test that the home page returns a 200 status code"""
        url = "http://localhost:5001/"
        
        try:
            response = urllib.request.urlopen(url)
            assert response.getcode() == 200
        except urllib.error.URLError:
            # If the server isn't running, the test should fail
            assert False, "Could not connect to server at http://localhost:5001/"