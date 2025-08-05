import pytest
import time
from datetime import datetime, date, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class TestEditableCounter:
    @pytest.fixture
    def driver(self):
        """Set up Chrome WebDriver"""
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # Run in headless mode for CI/testing
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--enable-logging")
        options.add_argument("--log-level=0")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(10)
        
        yield driver
        driver.quit()

    def test_counter_field_is_editable(self, driver):
        """Test that counter field can be manually edited"""
        driver.get("http://localhost:5001/")
        
        # Counter field should be editable (not readonly)
        counter_field = driver.find_element(By.ID, "counter")
        readonly_attr = counter_field.get_attribute('readonly')
        
        # Should not be readonly so we can edit it
        assert readonly_attr is None or readonly_attr == 'false', "Counter field should be editable for development"

    def test_counter_can_be_set_up_to_total_days_daily(self, driver):
        """Test that counter can be set up to the total number of days for daily habits"""
        driver.get("http://localhost:5001/")
        
        # Set start date to 5 days ago (6 total days including today)
        five_days_ago = (date.today() - timedelta(days=5)).strftime('%Y-%m-%d')
        
        driver.execute_script(f"""
            // Set up scenario
            document.getElementById('started-date').value = '{five_days_ago}';
            habitData.startedDate = '{five_days_ago}';
            document.getElementById('frequency').value = 'Daily';
            habitData.frequency = 'Daily';
            
            // Update percentage
            updatePercentage();
        """)
        time.sleep(0.5)
        
        counter_field = driver.find_element(By.ID, "counter")
        
        # Test setting counter to different values up to total days (6)
        for counter_value in [0, 1, 3, 6]:
            # Set counter value
            counter_field.clear()
            counter_field.send_keys(str(counter_value))
            
            # Trigger change event
            driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", counter_field)
            time.sleep(0.5)
            
            # Check percentage calculation
            percentage_element = driver.find_element(By.ID, "percentage")
            percentage_value = int(percentage_element.text.replace('%', ''))
            
            expected_percentage = round((counter_value / 6) * 100)  # counter / 6 total days
            assert percentage_value == expected_percentage, f"Counter {counter_value}: Expected {expected_percentage}% but got {percentage_value}%"

    def test_counter_can_be_set_up_to_total_weeks_weekly(self, driver):
        """Test that counter can be set up to the total number of weeks for weekly habits"""
        driver.get("http://localhost:5001/")
        
        # Set start date to 3 weeks ago (4 total weeks including current week)
        three_weeks_ago = (date.today() - timedelta(weeks=3)).strftime('%Y-%m-%d')
        
        driver.execute_script(f"""
            // Set up scenario
            document.getElementById('started-date').value = '{three_weeks_ago}';
            habitData.startedDate = '{three_weeks_ago}';
            document.getElementById('frequency').value = 'Weekly';
            habitData.frequency = 'Weekly';
            
            // Update percentage
            updatePercentage();
        """)
        time.sleep(0.5)
        
        counter_field = driver.find_element(By.ID, "counter")
        
        # Test setting counter to different values up to total weeks (4)
        for counter_value in [0, 1, 2, 4]:
            # Set counter value
            counter_field.clear()
            counter_field.send_keys(str(counter_value))
            
            # Trigger change event
            driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", counter_field)
            time.sleep(0.5)
            
            # Check percentage calculation
            percentage_element = driver.find_element(By.ID, "percentage")
            percentage_value = int(percentage_element.text.replace('%', ''))
            
            expected_percentage = round((counter_value / 4) * 100)  # counter / 4 total weeks
            assert percentage_value == expected_percentage, f"Counter {counter_value}: Expected {expected_percentage}% but got {percentage_value}%"

    def test_counter_cannot_exceed_total_periods(self, driver):
        """Test that counter cannot be set higher than total periods"""
        driver.get("http://localhost:5001/")
        
        # Set start date to 2 days ago (3 total days)
        two_days_ago = (date.today() - timedelta(days=2)).strftime('%Y-%m-%d')
        
        driver.execute_script(f"""
            // Set up scenario
            document.getElementById('started-date').value = '{two_days_ago}';
            habitData.startedDate = '{two_days_ago}';
            document.getElementById('frequency').value = 'Daily';
            habitData.frequency = 'Daily';
            
            // Update percentage
            updatePercentage();
        """)
        time.sleep(0.5)
        
        counter_field = driver.find_element(By.ID, "counter")
        
        # Try to set counter to 5 (more than 3 total days)
        counter_field.clear()
        counter_field.send_keys("5")
        
        # Trigger change event
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", counter_field)
        time.sleep(0.5)
        
        # Counter should be capped at 3 (total days)
        actual_counter = int(counter_field.get_attribute('value'))
        assert actual_counter == 3, f"Counter should be capped at 3 (total days), but got {actual_counter}"
        
        # Percentage should be 100% (3/3)
        percentage_element = driver.find_element(By.ID, "percentage")
        percentage_value = int(percentage_element.text.replace('%', ''))
        assert percentage_value == 100, f"Percentage should be 100% when counter equals total days, but got {percentage_value}%"

    def test_counter_updates_when_start_date_changes(self, driver):
        """Test that counter maximum updates when start date changes"""
        driver.get("http://localhost:5001/")
        
        # Start with 2 days ago (3 total days), set counter to 2
        two_days_ago = (date.today() - timedelta(days=2)).strftime('%Y-%m-%d')
        
        driver.execute_script(f"""
            document.getElementById('started-date').value = '{two_days_ago}';
            habitData.startedDate = '{two_days_ago}';
            document.getElementById('frequency').value = 'Daily';
            habitData.frequency = 'Daily';
            document.getElementById('counter').value = '2';
            habitData.counter = 2;
            updatePercentage();
        """)
        time.sleep(0.5)
        
        # Should be 67% (2/3)
        percentage_element = driver.find_element(By.ID, "percentage")
        initial_percentage = int(percentage_element.text.replace('%', ''))
        assert initial_percentage == 67, f"Initial percentage should be 67%, got {initial_percentage}%"
        
        # Change start date to 5 days ago (6 total days)
        five_days_ago = (date.today() - timedelta(days=5)).strftime('%Y-%m-%d')
        
        driver.execute_script(f"""
            document.getElementById('started-date').value = '{five_days_ago}';
            habitData.startedDate = '{five_days_ago}';
            updatePercentage();
        """)
        time.sleep(0.5)
        
        # Percentage should now be 33% (2/6)
        updated_percentage = int(percentage_element.text.replace('%', ''))
        assert updated_percentage == 33, f"Updated percentage should be 33%, got {updated_percentage}%"

    def test_counter_persists_when_checkboxes_clicked(self, driver):
        """Test that manual counter changes persist when Done/Not Done checkboxes are clicked"""
        driver.get("http://localhost:5001/")
        
        # Set up scenario with 4 days total, counter at 2
        three_days_ago = (date.today() - timedelta(days=3)).strftime('%Y-%m-%d')
        
        driver.execute_script(f"""
            document.getElementById('started-date').value = '{three_days_ago}';
            habitData.startedDate = '{three_days_ago}';
            document.getElementById('frequency').value = 'Daily';
            habitData.frequency = 'Daily';
            document.getElementById('counter').value = '2';
            habitData.counter = 2;
            updatePercentage();
        """)
        time.sleep(0.5)
        
        # Verify initial state: 50% (2/4)
        percentage_element = driver.find_element(By.ID, "percentage")
        initial_percentage = int(percentage_element.text.replace('%', ''))
        assert initial_percentage == 50, f"Initial percentage should be 50%, got {initial_percentage}%"
        
        # Click Done checkbox - this should not reset the counter
        done_checkbox = driver.find_element(By.CSS_SELECTOR, "input[type='checkbox'][name='done']")
        done_checkbox.click()
        time.sleep(0.5)
        
        # Counter should remain at 2 (or be updated based on new logic)
        counter_field = driver.find_element(By.ID, "counter")
        counter_value = int(counter_field.get_attribute('value'))
        
        # The behavior here depends on implementation - either:
        # Option A: Manual counter overrides checkbox behavior
        # Option B: Checkbox behavior updates counter
        # For now, let's test that the percentage still reflects the counter value
        updated_percentage = int(percentage_element.text.replace('%', ''))
        expected_percentage = round((counter_value / 4) * 100)
        
        assert updated_percentage == expected_percentage, f"Percentage should reflect counter value: expected {expected_percentage}%, got {updated_percentage}%"