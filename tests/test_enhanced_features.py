import pytest
import time
from datetime import datetime, date, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class TestEnhancedFeatures:
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

    def test_started_date_field_exists_and_editable(self, driver):
        """Test that Started date field exists and is editable"""
        driver.get("http://localhost:5001/")
        
        # Look for Started date input field
        date_field = driver.find_element(By.CSS_SELECTOR, "input[type='date']")
        assert date_field is not None, "Started date field should exist"
        
        # Should be editable
        assert date_field.is_enabled(), "Started date field should be editable"
        
        # Should default to today's date
        today_str = date.today().strftime('%Y-%m-%d')
        assert date_field.get_attribute('value') == today_str, f"Should default to today's date: {today_str}"

    def test_frequency_dropdown_exists_with_options(self, driver):
        """Test that frequency dropdown exists with Daily/Weekly options"""
        driver.get("http://localhost:5001/")
        
        # Look for frequency dropdown
        dropdown = driver.find_element(By.CSS_SELECTOR, "select")
        assert dropdown is not None, "Frequency dropdown should exist"
        
        # Check options
        select = Select(dropdown)
        options = [option.text for option in select.options]
        
        assert "Daily" in options, "Dropdown should contain 'Daily' option"
        assert "Weekly" in options, "Dropdown should contain 'Weekly' option"

    def test_counter_field_exists_and_tracks_done_clicks(self, driver):
        """Test that counter field exists and tracks Done button clicks"""
        driver.get("http://localhost:5001/")
        
        # Look for counter field
        counter_field = driver.find_element(By.CSS_SELECTOR, "input[type='number']")
        assert counter_field is not None, "Counter field should exist"
        
        # Should start at 0
        initial_count = int(counter_field.get_attribute('value') or '0')
        
        # Click Done checkbox
        done_checkbox = driver.find_element(By.CSS_SELECTOR, "input[type='checkbox'][name='done']")
        done_checkbox.click()
        
        # Wait for JavaScript to update
        time.sleep(0.5)
        
        # Counter should increment
        updated_count = int(counter_field.get_attribute('value') or '0')
        assert updated_count == initial_count + 1, "Counter should increment when Done is checked"

    def test_not_done_checkbox_and_why_field_exist(self, driver):
        """Test that Not Done checkbox and Why text field exist"""
        driver.get("http://localhost:5001/")
        
        # Look for Not Done checkbox
        not_done_checkbox = driver.find_element(By.CSS_SELECTOR, "input[type='checkbox'][name='not_done']")
        assert not_done_checkbox is not None, "Not Done checkbox should exist"
        
        # Look for Why text field
        why_field = driver.find_element(By.CSS_SELECTOR, "input[type='text'][name='why'], textarea[name='why']")
        assert why_field is not None, "Why text field should exist"

    def test_done_percentage_calculation_javascript(self, driver):
        """Test that percentage is calculated correctly with JavaScript when Done is checked"""
        driver.get("http://localhost:5001/")
        
        # Get initial percentage
        percentage_element = driver.find_element(By.ID, "percentage")
        initial_percentage = percentage_element.text.replace('%', '')
        
        # Click Done checkbox
        done_checkbox = driver.find_element(By.CSS_SELECTOR, "input[type='checkbox'][name='done']")
        done_checkbox.click()
        
        # Wait for JavaScript to update
        time.sleep(0.5)
        
        # Percentage should update
        updated_percentage = percentage_element.text.replace('%', '')
        assert updated_percentage != initial_percentage, "Percentage should update when Done is checked"

    def test_not_done_percentage_calculation_javascript(self, driver):
        """Test that percentage is calculated correctly when Not Done is checked"""
        driver.get("http://localhost:5001/")
        
        # First click Done to establish a baseline
        done_checkbox = driver.find_element(By.CSS_SELECTOR, "input[type='checkbox'][name='done']")
        done_checkbox.click()
        time.sleep(0.5)
        
        # Get percentage after Done is checked (should be 100%)
        percentage_element = driver.find_element(By.ID, "percentage")
        done_percentage = percentage_element.text.replace('%', '')
        
        # Now click Not Done checkbox (should uncheck Done and switch to Not Done)
        not_done_checkbox = driver.find_element(By.CSS_SELECTOR, "input[type='checkbox'][name='not_done']")
        not_done_checkbox.click()
        
        # Wait for JavaScript to update
        time.sleep(0.5)
        
        # Percentage should change from 100% to 0% (0 completed / 1 not done = 0%)
        updated_percentage = percentage_element.text.replace('%', '')
        assert updated_percentage != done_percentage, "Percentage should update when Not Done is checked"
        assert updated_percentage == "0", "Percentage should be 0% when only Not Done is tracked"

    def test_daily_frequency_limits_one_per_day(self, driver):
        """Test that Daily frequency limits Done clicks to 1 per day"""
        driver.get("http://localhost:5001/")
        
        # Ensure Daily is selected
        dropdown = driver.find_element(By.CSS_SELECTOR, "select")
        select = Select(dropdown)
        select.select_by_visible_text("Daily")
        
        # Get counter field
        counter_field = driver.find_element(By.CSS_SELECTOR, "input[type='number']")
        done_checkbox = driver.find_element(By.CSS_SELECTOR, "input[type='checkbox'][name='done']")
        
        # Click Done once
        done_checkbox.click()
        time.sleep(0.5)
        first_count = int(counter_field.get_attribute('value') or '0')
        assert first_count == 1, "Counter should increment to 1 when Done is clicked"
        
        # Uncheck and check again (simulating trying to mark done again same day)
        done_checkbox.click()  # Uncheck
        time.sleep(0.5)
        done_checkbox.click()  # Check again
        time.sleep(0.5)
        
        second_count = int(counter_field.get_attribute('value') or '0')
        
        # Counter should still be 1 (not 2) because we can only mark done once per day
        assert second_count == 1, "Daily frequency should limit to 1 per day, counter should stay at 1"

    def test_weekly_frequency_limits_one_per_week(self, driver):
        """Test that Weekly frequency limits Done clicks to 1 per week"""
        driver.get("http://localhost:5001/")
        
        # Select Weekly frequency
        dropdown = driver.find_element(By.CSS_SELECTOR, "select")
        select = Select(dropdown)
        select.select_by_visible_text("Weekly")
        
        # Get counter field
        counter_field = driver.find_element(By.CSS_SELECTOR, "input[type='number']")
        done_checkbox = driver.find_element(By.CSS_SELECTOR, "input[type='checkbox'][name='done']")
        
        # Click Done once
        done_checkbox.click()
        time.sleep(0.5)
        first_count = int(counter_field.get_attribute('value') or '0')
        assert first_count == 1, "Counter should increment to 1 when Done is clicked"
        
        # Uncheck and check again (simulating trying to mark done again same week)
        done_checkbox.click()  # Uncheck
        time.sleep(0.5)
        done_checkbox.click()  # Check again
        time.sleep(0.5)
        
        second_count = int(counter_field.get_attribute('value') or '0')
        
        # Counter should still be 1 (not 2) because we can only mark done once per week
        assert second_count == 1, "Weekly frequency should limit to 1 per week, counter should stay at 1"

    def test_mutual_exclusivity_done_not_done_checkboxes(self, driver):
        """Test that Done and Not Done checkboxes are mutually exclusive"""
        driver.get("http://localhost:5001/")
        
        done_checkbox = driver.find_element(By.CSS_SELECTOR, "input[type='checkbox'][name='done']")
        not_done_checkbox = driver.find_element(By.CSS_SELECTOR, "input[type='checkbox'][name='not_done']")
        
        # Click Done
        done_checkbox.click()
        time.sleep(0.5)
        
        assert done_checkbox.is_selected(), "Done checkbox should be checked"
        assert not not_done_checkbox.is_selected(), "Not Done checkbox should be unchecked when Done is checked"
        
        # Click Not Done
        not_done_checkbox.click()
        time.sleep(0.5)
        
        assert not done_checkbox.is_selected(), "Done checkbox should be unchecked when Not Done is checked"
        assert not_done_checkbox.is_selected(), "Not Done checkbox should be checked"

    def test_why_field_interaction_with_not_done(self, driver):
        """Test that Why field becomes enabled/visible when Not Done is checked"""
        driver.get("http://localhost:5001/")
        
        not_done_checkbox = driver.find_element(By.CSS_SELECTOR, "input[type='checkbox'][name='not_done']")
        why_field = driver.find_element(By.CSS_SELECTOR, "input[type='text'][name='why'], textarea[name='why']")
        
        # Initially, Why field might be disabled or hidden
        # Click Not Done
        not_done_checkbox.click()
        time.sleep(0.5)
        
        # Why field should be enabled/visible when Not Done is checked
        assert why_field.is_enabled(), "Why field should be enabled when Not Done is checked"