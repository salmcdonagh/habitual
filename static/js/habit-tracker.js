// Core habit tracking functionality (from original app)

// Calculate percentage based on current data
function calculatePercentage() {
    const startDate = new Date(habitData.startedDate);
    const today = new Date();
    
    let totalPeriods = 0;
    let completedPeriods = habitData.counter; // Use counter value directly
    
    if (habitData.frequency === 'Daily') {
        // Calculate days between start date and today (inclusive)
        const diffTime = Math.abs(today - startDate);
        const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
        totalPeriods = diffDays + 1; // +1 to include both start and end date
    } else if (habitData.frequency === 'Weekly') {
        // Calculate weeks between start date and today (inclusive)
        const diffTime = Math.abs(today - startDate);
        const diffWeeks = Math.floor(diffTime / (1000 * 60 * 60 * 24 * 7));
        totalPeriods = diffWeeks + 1; // +1 to include both start and end week
    }
    
    if (totalPeriods <= 0) return 0;
    
    // Calculate percentage: counter / total_periods_since_start * 100
    // This gives the actual success rate over the entire time period
    return Math.round((completedPeriods / totalPeriods) * 100);
}

// Calculate total periods since start date
function getTotalPeriods() {
    const startDate = new Date(habitData.startedDate);
    const today = new Date();
    
    if (habitData.frequency === 'Daily') {
        const diffTime = Math.abs(today - startDate);
        const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
        return diffDays + 1;
    } else if (habitData.frequency === 'Weekly') {
        const diffTime = Math.abs(today - startDate);
        const diffWeeks = Math.floor(diffTime / (1000 * 60 * 60 * 24 * 7));
        return diffWeeks + 1;
    }
    return 1;
}

// Load habit data from localStorage
function loadFromLocalStorage() {
    try {
        const savedData = localStorage.getItem('habitData');
        if (savedData) {
            const parsedData = JSON.parse(savedData);
            
            // Update habitData object
            habitData.startedDate = parsedData.startedDate || habitData.startedDate;
            habitData.frequency = parsedData.frequency || habitData.frequency;
            habitData.counter = parsedData.counter || habitData.counter;
            habitData.completedDates = parsedData.completedDates || habitData.completedDates;
            habitData.notDoneDates = parsedData.notDoneDates || habitData.notDoneDates;
            habitData.whyEntries = parsedData.whyEntries || habitData.whyEntries;
            
            updateUIFromData();
            return true; // Successfully loaded
        }
    } catch (e) {
        console.warn('Failed to load from localStorage:', e);
    }
    return false; // No data or failed to load
}

// Save habit data to localStorage
function saveToLocalStorage() {
    try {
        const dataToSave = {
            startedDate: habitData.startedDate,
            frequency: habitData.frequency,
            counter: habitData.counter,
            completedDates: habitData.completedDates,
            notDoneDates: habitData.notDoneDates,
            whyEntries: habitData.whyEntries
        };
        localStorage.setItem('habitData', JSON.stringify(dataToSave));
    } catch (e) {
        console.warn('Failed to save to localStorage:', e);
    }
}

// Update percentage display
function updatePercentage() {
    const percentage = calculatePercentage();
    document.getElementById('percentage').textContent = percentage + '%';
}

// Get current period key
function getCurrentPeriodKey() {
    const today = new Date();
    if (habitData.frequency === 'Daily') {
        return today.toISOString().split('T')[0]; // YYYY-MM-DD
    } else if (habitData.frequency === 'Weekly') {
        const startOfWeek = new Date(today);
        startOfWeek.setDate(today.getDate() - today.getDay()); // Start of week (Sunday)
        return startOfWeek.toISOString().split('T')[0];
    }
    return today.toISOString().split('T')[0];
}

// Check if current period is already tracked
function isCurrentPeriodTracked() {
    const periodKey = getCurrentPeriodKey();
    return habitData.completedDates.includes(periodKey) || 
           habitData.notDoneDates.includes(periodKey);
}

// Initialize the application
function initializeApp() {
    // Load saved data from localStorage first
    loadFromLocalStorage();
    
    // Initialize counter max value and update percentage
    const initialTotalPeriods = getTotalPeriods();
    document.getElementById('counter').setAttribute('max', initialTotalPeriods);
    updatePercentage();
    
    // Set up event listeners
    setupEventListeners();
}

// Set up all event listeners
function setupEventListeners() {
    // Handle Done checkbox
    document.getElementById('done-checkbox').addEventListener('change', function() {
        const periodKey = getCurrentPeriodKey();
        const notDoneCheckbox = document.getElementById('not-done-checkbox');
        
        if (this.checked) {
            // Uncheck Not Done
            notDoneCheckbox.checked = false;
            document.getElementById('why-field').style.display = 'none';
            
            // Remove from not done dates if present
            const notDoneIndex = habitData.notDoneDates.indexOf(periodKey);
            if (notDoneIndex > -1) {
                habitData.notDoneDates.splice(notDoneIndex, 1);
            }
            
            // Add to completed dates if not already there
            if (!habitData.completedDates.includes(periodKey)) {
                habitData.completedDates.push(periodKey);
                habitData.counter++;
                document.getElementById('counter').value = habitData.counter;
            }
        } else {
            // Remove from completed dates
            const index = habitData.completedDates.indexOf(periodKey);
            if (index > -1) {
                habitData.completedDates.splice(index, 1);
                habitData.counter = Math.max(0, habitData.counter - 1);
                document.getElementById('counter').value = habitData.counter;
            }
        }
        
        updatePercentage();
        saveHabitData();
    });

    // Handle Not Done checkbox
    document.getElementById('not-done-checkbox').addEventListener('change', function() {
        const periodKey = getCurrentPeriodKey();
        const doneCheckbox = document.getElementById('done-checkbox');
        const whyField = document.getElementById('why-field');
        
        if (this.checked) {
            // Uncheck Done
            doneCheckbox.checked = false;
            whyField.style.display = 'block';
            
            // Remove from completed dates if present
            const completedIndex = habitData.completedDates.indexOf(periodKey);
            if (completedIndex > -1) {
                habitData.completedDates.splice(completedIndex, 1);
                habitData.counter = Math.max(0, habitData.counter - 1);
                document.getElementById('counter').value = habitData.counter;
            }
            
            // Add to not done dates if not already there
            if (!habitData.notDoneDates.includes(periodKey)) {
                habitData.notDoneDates.push(periodKey);
            }
        } else {
            whyField.style.display = 'none';
            
            // Remove from not done dates
            const index = habitData.notDoneDates.indexOf(periodKey);
            if (index > -1) {
                habitData.notDoneDates.splice(index, 1);
            }
        }
        
        updatePercentage();
        saveHabitData();
    });

    // Handle frequency change
    document.getElementById('frequency').addEventListener('change', function() {
        habitData.frequency = this.value;
        updatePercentage();
        saveHabitData();
    });

    // Handle start date change
    document.getElementById('started-date').addEventListener('change', function() {
        habitData.startedDate = this.value;
        
        // Update counter max value based on new start date
        const totalPeriods = getTotalPeriods();
        const counterField = document.getElementById('counter');
        counterField.setAttribute('max', totalPeriods);
        
        // Cap current counter value if it exceeds new maximum
        if (habitData.counter > totalPeriods) {
            habitData.counter = totalPeriods;
            counterField.value = totalPeriods;
        }
        
        updatePercentage();
        saveHabitData();
    });

    // Handle counter change
    document.getElementById('counter').addEventListener('change', function() {
        const newValue = parseInt(this.value) || 0;
        const totalPeriods = getTotalPeriods();
        
        // Cap counter at total periods
        if (newValue > totalPeriods) {
            this.value = totalPeriods;
            habitData.counter = totalPeriods;
        } else if (newValue < 0) {
            this.value = 0;
            habitData.counter = 0;
        } else {
            habitData.counter = newValue;
        }
        
        updatePercentage();
        saveHabitData();
    });

    // Add event listener for why text changes
    document.getElementById('why-text').addEventListener('change', function() {
        const today = new Date().toISOString().split('T')[0];
        habitData.whyEntries[today] = this.value;
        saveHabitData();
    });

    // Close modal when clicking outside
    window.onclick = function(event) {
        const modal = document.getElementById('auth-modal');
        if (event.target === modal) {
            closeModal();
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});