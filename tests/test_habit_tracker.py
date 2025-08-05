import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class TestHabitTracker:
    @pytest.fixture
    def driver(self):
        """Set up Chrome WebDriver"""
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # Run in headless mode for CI/testing
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(10)
        
        yield driver
        driver.quit()

    def test_daily_habit_exists_on_page(self, driver):
        """Test that a 'daily habit' exists on the page"""
        driver.get("http://localhost:5001/")
        
        # Look for text indicating a daily habit
        page_source = driver.page_source.lower()
        assert "daily habit" in page_source, "Page should contain 'daily habit' text"

    def test_done_checkbox_exists(self, driver):
        """Test that a 'Done' checkbox exists for the daily habit"""
        driver.get("http://localhost:5001/")
        
        # Look for a checkbox with "Done" label or similar
        checkbox = driver.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
        assert checkbox is not None, "Page should contain a checkbox"
        
        # Check if there's associated text indicating it's for "Done"
        page_source = driver.page_source.lower()
        assert "done" in page_source, "Page should contain 'Done' text near checkbox"

    def test_percentage_statistic_exists(self, driver):
        """Test that percentage statistic is displayed"""
        driver.get("http://localhost:5001/")
        
        # Look for percentage statistic (could be "0%" initially)
        page_source = driver.page_source
        # Should contain a percentage value (% symbol)
        assert "%" in page_source, "Page should display a percentage statistic"

    def test_checkbox_click_updates_percentage(self, driver):
        """Test that clicking the Done checkbox updates the percentage statistic"""
        driver.get("http://localhost:5001/")
        
        # Get initial percentage value by searching page source
        initial_page_source = driver.page_source
        
        # Find and click the checkbox
        checkbox = driver.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
        checkbox.click()
        
        # Wait for the page to update (might need a short delay for AJAX)
        time.sleep(1)
        
        # Get updated page source
        updated_page_source = driver.page_source
        
        # The page content should change when checkbox is clicked
        assert initial_page_source != updated_page_source, "Page should update when checkbox is clicked"