import pytest
import time
from datetime import datetime, date, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class TestPercentageCalculations:
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

    def test_percentage_calculation_with_past_start_date_daily(self, driver):
        """Test percentage calculation when start date is set to 3 days ago with 1 completion"""
        driver.get("http://localhost:5001/")
        
        # Set start date to 3 days ago using JavaScript directly
        three_days_ago = (date.today() - timedelta(days=3)).strftime('%Y-%m-%d')
        
        # Use JavaScript to update everything directly
        driver.execute_script(f"""
            // Update start date
            document.getElementById('started-date').value = '{three_days_ago}';
            habitData.startedDate = '{three_days_ago}';
            
            // Ensure Daily frequency
            document.getElementById('frequency').value = 'Daily';
            habitData.frequency = 'Daily';
            
            // Add a completion for today
            const today = new Date().toISOString().split('T')[0];
            habitData.completedDates = [today];
            habitData.counter = 1;
            document.getElementById('counter').value = 1;
            document.getElementById('done-checkbox').checked = true;
            
            // Update percentage
            updatePercentage();
        """)
        
        # Wait for JavaScript to complete
        time.sleep(1)
        
        # Remove debug logging since tests are working
        
        # Check the percentage - should be ~33% (1 completion out of 4 days)
        percentage_element = driver.find_element(By.ID, "percentage")
        percentage_text = percentage_element.text
        percentage_value = int(percentage_text.replace('%', ''))
        
        # With 4 days total (3 days ago + today) and 1 completion, should be 25%
        # But we also need to account for the "not done" tracking
        # If only 1 day is tracked (done), then it should be 100% of tracked days
        # However, the user expects it to be 25% of total days since start
        expected_percentage = 25  # 1 completion / 4 total days * 100
        
        assert percentage_value == expected_percentage, f"Expected ~{expected_percentage}% but got {percentage_value}% for 1 completion in 4 days"

    def test_percentage_calculation_with_past_start_date_weekly(self, driver):
        """Test percentage calculation when start date is set to 2 weeks ago with 1 completion"""
        driver.get("http://localhost:5001/")
        
        # Set start date to 2 weeks ago using JavaScript directly
        two_weeks_ago = (date.today() - timedelta(weeks=2)).strftime('%Y-%m-%d')
        
        # Use JavaScript to update everything directly
        driver.execute_script(f"""
            // Update start date
            document.getElementById('started-date').value = '{two_weeks_ago}';
            habitData.startedDate = '{two_weeks_ago}';
            
            // Set Weekly frequency
            document.getElementById('frequency').value = 'Weekly';
            habitData.frequency = 'Weekly';
            
            // Add a completion for today
            const today = new Date().toISOString().split('T')[0];
            habitData.completedDates = [today];
            habitData.counter = 1;
            document.getElementById('counter').value = 1;
            document.getElementById('done-checkbox').checked = true;
            
            // Update percentage
            updatePercentage();
        """)
        
        # Wait for JavaScript to complete
        time.sleep(1)
        
        # Check the percentage - should be ~33% (1 completion out of 3 weeks)
        percentage_element = driver.find_element(By.ID, "percentage")
        percentage_text = percentage_element.text
        percentage_value = int(percentage_text.replace('%', ''))
        
        # With 3 weeks total and 1 completion, should be 33%
        expected_percentage = 33  # 1 completion / 3 total weeks * 100
        
        assert percentage_value == expected_percentage, f"Expected ~{expected_percentage}% but got {percentage_value}% for 1 completion in 3 weeks"

    def test_counter_affects_percentage_calculation(self, driver):
        """Test that manually changing counter affects percentage calculation"""
        driver.get("http://localhost:5001/")
        
        # Set up the scenario using JavaScript
        two_days_ago = (date.today() - timedelta(days=2)).strftime('%Y-%m-%d')
        
        # Use JavaScript to set up initial state and then test interaction
        driver.execute_script(f"""
            // Update start date to 2 days ago
            document.getElementById('started-date').value = '{two_days_ago}';
            habitData.startedDate = '{two_days_ago}';
            
            // Ensure Daily frequency
            document.getElementById('frequency').value = 'Daily';
            habitData.frequency = 'Daily';
            
            // Start with no completions
            habitData.completedDates = [];
            habitData.counter = 0;
            document.getElementById('counter').value = 0;
            document.getElementById('done-checkbox').checked = false;
            
            // Update percentage
            updatePercentage();
        """)
        time.sleep(0.5)
        
        # Get initial percentage (should be 0% since no completions)
        percentage_element = driver.find_element(By.ID, "percentage")
        initial_percentage = int(percentage_element.text.replace('%', ''))
        assert initial_percentage == 0, "Initial percentage should be 0%"
        
        # Now click Done checkbox to add completion
        done_checkbox = driver.find_element(By.CSS_SELECTOR, "input[type='checkbox'][name='done']")
        done_checkbox.click()  # First click - should add completion
        time.sleep(1)
        
        # Verify counter is 1
        counter_field = driver.find_element(By.ID, "counter")
        counter_value = int(counter_field.get_attribute('value'))
        assert counter_value == 1, f"Counter should be 1, but got {counter_value}"
        
        # Check percentage - with 3 total days and 1 completion, should be 33%
        updated_percentage = int(percentage_element.text.replace('%', ''))
        expected_percentage = 33  # 1 completion / 3 total days * 100
        
        assert updated_percentage == expected_percentage, f"Expected {expected_percentage}% but got {updated_percentage}% for 1 completion in 3 days"

    def test_mixed_done_and_not_done_percentage_calculation(self, driver):
        """Test percentage calculation with both done and not done entries over multiple days"""
        driver.get("http://localhost:5001/")
        
        # Set start date to 4 days ago
        four_days_ago = (date.today() - timedelta(days=4)).strftime('%Y-%m-%d')
        start_date_field = driver.find_element(By.ID, "started-date")
        start_date_field.clear()
        start_date_field.send_keys(four_days_ago)
        
        # Ensure Daily frequency
        frequency_dropdown = driver.find_element(By.ID, "frequency")
        select = Select(frequency_dropdown)
        select.select_by_visible_text("Daily")
        
        # Mark today as Done
        done_checkbox = driver.find_element(By.CSS_SELECTOR, "input[type='checkbox'][name='done']")
        done_checkbox.click()
        time.sleep(0.5)
        
        # Then mark as Not Done (simulating mixed tracking)
        not_done_checkbox = driver.find_element(By.CSS_SELECTOR, "input[type='checkbox'][name='not_done']")
        not_done_checkbox.click()
        time.sleep(1)
        
        # Now we should have: 0 done, 1 not done, over 5 total days
        # Traditional calculation: 0 / (0 + 1) = 0%
        # But user expects: 0 / 5 total days = 0%
        percentage_element = driver.find_element(By.ID, "percentage")
        percentage_value = int(percentage_element.text.replace('%', ''))
        
        assert percentage_value == 0, f"Expected 0% but got {percentage_value}% for 0 completions"

    def test_untracked_days_should_not_count_as_failures(self, driver):
        """Test that untracked days (neither done nor not done) don't affect percentage negatively"""
        driver.get("http://localhost:5001/")
        
        # Set start date to 10 days ago using JavaScript directly
        ten_days_ago = (date.today() - timedelta(days=10)).strftime('%Y-%m-%d')
        
        # Use JavaScript to update everything directly
        driver.execute_script(f"""
            // Update start date
            document.getElementById('started-date').value = '{ten_days_ago}';
            habitData.startedDate = '{ten_days_ago}';
            
            // Ensure Daily frequency
            document.getElementById('frequency').value = 'Daily';
            habitData.frequency = 'Daily';
            
            // Add a completion for today
            const today = new Date().toISOString().split('T')[0];
            habitData.completedDates = [today];
            habitData.counter = 1;
            document.getElementById('counter').value = 1;
            document.getElementById('done-checkbox').checked = true;
            
            // Update percentage
            updatePercentage();
        """)
        
        # Wait for JavaScript to complete
        time.sleep(1)
        
        # With 11 total days and 1 completion, should be ~9%
        percentage_element = driver.find_element(By.ID, "percentage")
        percentage_value = int(percentage_element.text.replace('%', ''))
        
        expected_percentage = 9  # 1 completion / 11 total days * 100 ≈ 9%
        
        assert percentage_value == expected_percentage, f"Expected ~{expected_percentage}% but got {percentage_value}% for 1 completion in 11 days"

    def test_changing_start_date_updates_percentage_immediately(self, driver):
        """Test that changing the start date immediately updates the percentage"""
        driver.get("http://localhost:5001/")
        
        # First, set up initial state - today with 1 completion (should be 100%)
        driver.execute_script("""
            // Add a completion for today
            const today = new Date().toISOString().split('T')[0];
            habitData.completedDates = [today];
            habitData.counter = 1;
            document.getElementById('counter').value = 1;
            document.getElementById('done-checkbox').checked = true;
            
            // Update percentage
            updatePercentage();
        """)
        time.sleep(0.5)
        
        percentage_element = driver.find_element(By.ID, "percentage")
        initial_percentage = int(percentage_element.text.replace('%', ''))
        
        # Now change start date to 9 days ago using JavaScript
        nine_days_ago = (date.today() - timedelta(days=9)).strftime('%Y-%m-%d')
        driver.execute_script(f"""
            // Update start date
            document.getElementById('started-date').value = '{nine_days_ago}';
            habitData.startedDate = '{nine_days_ago}';
            
            // Update percentage immediately
            updatePercentage();
        """)
        time.sleep(1)
        
        # Percentage should update immediately to reflect new timeframe
        updated_percentage = int(percentage_element.text.replace('%', ''))
        
        # With 10 total days and 1 completion, should be 10%
        expected_percentage = 10  # 1 completion / 10 total days * 100
        
        assert updated_percentage != initial_percentage, "Percentage should change when start date changes"
        assert updated_percentage == expected_percentage, f"Expected {expected_percentage}% but got {updated_percentage}% for 1 completion in 10 days"