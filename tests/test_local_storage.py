import pytest
import time
import json
from datetime import datetime, date, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class TestLocalStorage:
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
        
        # Clear local storage before each test
        driver.get("http://localhost:5001/")
        driver.execute_script("localStorage.clear();")
        
        yield driver
        driver.quit()

    def test_habit_state_is_saved_to_local_storage(self, driver):
        """Test that habit state is automatically saved to localStorage when changed"""
        driver.get("http://localhost:5001/")
        
        # Change start date using JavaScript to avoid date format issues
        two_days_ago = (date.today() - timedelta(days=2)).strftime('%Y-%m-%d')
        
        driver.execute_script(f"""
            document.getElementById('started-date').value = '{two_days_ago}';
            document.getElementById('started-date').dispatchEvent(new Event('change'));
            
            document.getElementById('frequency').value = 'Weekly';
            document.getElementById('frequency').dispatchEvent(new Event('change'));
            
            document.getElementById('counter').value = '1';
            document.getElementById('counter').dispatchEvent(new Event('change'));
        """)
        time.sleep(0.5)
        
        # Mark as done
        done_checkbox = driver.find_element(By.CSS_SELECTOR, "input[type='checkbox'][name='done']")
        done_checkbox.click()
        
        time.sleep(1)  # Allow time for localStorage save
        
        # Check that data was saved to localStorage
        saved_data = driver.execute_script("return localStorage.getItem('habitData');")
        assert saved_data is not None, "Habit data should be saved to localStorage"
        
        # Parse the saved data
        habit_data = json.loads(saved_data)
        
        assert habit_data['startedDate'] == two_days_ago, "Start date should be saved"
        assert habit_data['frequency'] == 'Weekly', "Frequency should be saved"
        assert habit_data['counter'] == 2, "Counter should be saved (1 initial + 1 from Done click)"
        assert len(habit_data['completedDates']) > 0, "Completed dates should be saved"

    def test_habit_state_is_loaded_from_local_storage_on_page_load(self, driver):
        """Test that habit state is restored from localStorage when page loads"""
        driver.get("http://localhost:5001/")
        
        # Set up initial state in localStorage
        three_days_ago = (date.today() - timedelta(days=3)).strftime('%Y-%m-%d')
        today = date.today().strftime('%Y-%m-%d')
        
        test_data = {
            'startedDate': three_days_ago,
            'frequency': 'Weekly',
            'counter': 2,
            'completedDates': [today],
            'notDoneDates': [],
            'whyEntries': {}
        }
        
        # Save test data to localStorage
        driver.execute_script(f"localStorage.setItem('habitData', '{json.dumps(test_data)}');")
        
        # Reload the page to test restoration
        driver.refresh()
        time.sleep(1)
        
        # Check if form fields were restored
        start_date_field = driver.find_element(By.ID, "started-date")
        assert start_date_field.get_attribute('value') == three_days_ago, "Start date should be restored"
        
        frequency_dropdown = driver.find_element(By.ID, "frequency")
        assert frequency_dropdown.get_attribute('value') == 'Weekly', "Frequency should be restored"
        
        counter_field = driver.find_element(By.ID, "counter")
        assert counter_field.get_attribute('value') == '2', "Counter should be restored"
        
        done_checkbox = driver.find_element(By.CSS_SELECTOR, "input[type='checkbox'][name='done']")
        assert done_checkbox.is_selected(), "Done checkbox should be restored if today is completed"

    def test_percentage_is_recalculated_after_loading_from_storage(self, driver):
        """Test that percentage is correctly calculated after loading from localStorage"""
        driver.get("http://localhost:5001/")
        
        # Set up state: 8 days ago, Weekly frequency, counter=1 (should be 50% since 2 weeks total)
        eight_days_ago = (date.today() - timedelta(days=8)).strftime('%Y-%m-%d')
        
        test_data = {
            'startedDate': eight_days_ago,
            'frequency': 'Weekly',
            'counter': 1,
            'completedDates': [],
            'notDoneDates': [],
            'whyEntries': {}
        }
        
        # Save to localStorage and reload
        driver.execute_script(f"localStorage.setItem('habitData', '{json.dumps(test_data)}');")
        driver.refresh()
        time.sleep(1)
        
        # Check percentage calculation
        percentage_element = driver.find_element(By.ID, "percentage")
        percentage_value = int(percentage_element.text.replace('%', ''))
        
        # With weekly frequency, 8 days ago = at least 1 full week ago, so 2 total weeks, counter=1 = 50%
        expected_percentage = 50
        assert percentage_value == expected_percentage, f"Expected {expected_percentage}% but got {percentage_value}%"

    def test_storage_survives_browser_refresh(self, driver):
        """Test that localStorage persists across browser refreshes"""
        driver.get("http://localhost:5001/")
        
        # Make changes to the form
        yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        driver.execute_script(f"""
            document.getElementById('started-date').value = '{yesterday}';
            document.getElementById('frequency').value = 'Daily';
            document.getElementById('counter').value = '1';
            
            // Trigger events to save to localStorage
            document.getElementById('started-date').dispatchEvent(new Event('change'));
            document.getElementById('frequency').dispatchEvent(new Event('change'));
            document.getElementById('counter').dispatchEvent(new Event('change'));
        """)
        time.sleep(1)
        
        # Refresh browser
        driver.refresh()
        time.sleep(1)
        
        # Verify data persisted
        start_date_field = driver.find_element(By.ID, "started-date")
        frequency_dropdown = driver.find_element(By.ID, "frequency")
        counter_field = driver.find_element(By.ID, "counter")
        
        assert start_date_field.get_attribute('value') == yesterday, "Start date should persist after refresh"
        assert frequency_dropdown.get_attribute('value') == 'Daily', "Frequency should persist after refresh"
        assert counter_field.get_attribute('value') == '1', "Counter should persist after refresh"

    def test_storage_handles_checkbox_state_persistence(self, driver):
        """Test that Done/Not Done checkbox states are saved and restored"""
        driver.get("http://localhost:5001/")
        
        # Mark as not done with a reason
        not_done_checkbox = driver.find_element(By.CSS_SELECTOR, "input[type='checkbox'][name='not_done']")
        not_done_checkbox.click()
        time.sleep(0.5)
        
        # Enter a reason
        why_field = driver.find_element(By.ID, "why-text")
        why_field.send_keys("Was too busy today")
        
        # Trigger save
        driver.execute_script("document.getElementById('why-text').dispatchEvent(new Event('change'));")
        time.sleep(1)
        
        # Refresh page
        driver.refresh()
        time.sleep(1)
        
        # Check if checkbox state and reason were restored
        not_done_checkbox = driver.find_element(By.CSS_SELECTOR, "input[type='checkbox'][name='not_done']")
        assert not_done_checkbox.is_selected(), "Not Done checkbox should be restored"
        
        why_field = driver.find_element(By.ID, "why-text")
        assert why_field.get_attribute('value') == "Was too busy today", "Why text should be restored"
        
        # Why field should be visible
        why_field_container = driver.find_element(By.ID, "why-field")
        assert why_field_container.is_displayed(), "Why field should be visible when Not Done is checked"

    def test_storage_fallback_when_no_saved_data(self, driver):
        """Test that app works normally when no localStorage data exists"""
        driver.get("http://localhost:5001/")
        
        # Explicitly clear localStorage
        driver.execute_script("localStorage.clear();")
        driver.refresh()
        time.sleep(1)
        
        # Check that default values are used
        start_date_field = driver.find_element(By.ID, "started-date")
        today_str = date.today().strftime('%Y-%m-%d')
        assert start_date_field.get_attribute('value') == today_str, "Should default to today when no saved data"
        
        frequency_dropdown = driver.find_element(By.ID, "frequency")
        assert frequency_dropdown.get_attribute('value') == 'Daily', "Should default to Daily when no saved data"
        
        counter_field = driver.find_element(By.ID, "counter")
        assert counter_field.get_attribute('value') == '0', "Should default to 0 counter when no saved data"
        
        # Percentage should be calculable
        percentage_element = driver.find_element(By.ID, "percentage")
        percentage_text = percentage_element.text
        assert percentage_text.endswith('%'), "Percentage should be displayed even without saved data"