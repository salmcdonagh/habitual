from datetime import datetime, date
import json
import os


class HabitTracker:
    def __init__(self, data_file='habit_data.json'):
        self.data_file = data_file
        self.data = self._load_data()
    
    def _load_data(self):
        """Load habit data from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'completed_dates': [], 
            'not_done_dates': [],
            'why_entries': {},
            'start_date': str(date.today()),
            'frequency': 'Daily',
            'counter': 0
        }
    
    def _save_data(self):
        """Save habit data to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f)
    
    def get_started_date(self):
        """Get the started date"""
        return self.data.get('start_date', str(date.today()))
    
    def get_frequency(self):
        """Get the frequency (Daily/Weekly)"""
        return self.data.get('frequency', 'Daily')
    
    def get_counter(self):
        """Get the counter value"""
        return self.data.get('counter', 0)
    
    def get_completed_dates(self):
        """Get list of completed dates"""
        return self.data.get('completed_dates', [])
    
    def get_not_done_dates(self):
        """Get list of not done dates"""
        return self.data.get('not_done_dates', [])
    
    def get_why_entries(self):
        """Get why entries dictionary"""
        return self.data.get('why_entries', {})
    
    def is_done_today(self):
        """Check if habit is marked done for today"""
        today = str(date.today())
        return today in self.data.get('completed_dates', [])
    
    def is_not_done_today(self):
        """Check if habit is marked not done for today"""
        today = str(date.today())
        return today in self.data.get('not_done_dates', [])
    
    def get_why_today(self):
        """Get why entry for today if exists"""
        today = str(date.today())
        return self.data.get('why_entries', {}).get(today, '')
    
    def toggle_today(self):
        """Toggle habit completion for today"""
        today = str(date.today())
        completed_dates = self.data.get('completed_dates', [])
        
        if today in completed_dates:
            completed_dates.remove(today)
        else:
            completed_dates.append(today)
        
        self.data['completed_dates'] = completed_dates
        self._save_data()
    
    def get_success_percentage(self):
        """Calculate success percentage since start date"""
        completed_dates = self.data.get('completed_dates', [])
        not_done_dates = self.data.get('not_done_dates', [])
        
        total_tracked = len(completed_dates) + len(not_done_dates)
        
        if total_tracked == 0:
            return 0
        
        # Calculate percentage: completed / (completed + not_done) * 100
        percentage = round((len(completed_dates) / total_tracked) * 100)
        return percentage