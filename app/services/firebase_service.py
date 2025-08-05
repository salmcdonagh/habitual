import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, date


class FirebaseService:
    def __init__(self):
        """Initialize Firebase Admin SDK"""
        if not firebase_admin._apps:
            # In production, this will use service account from environment
            # For local development, you'll need to set GOOGLE_APPLICATION_CREDENTIALS
            if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
                cred = credentials.Certificate(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
            else:
                # For Cloud Run, this will use default credentials
                cred = credentials.ApplicationDefault()
            
            firebase_admin.initialize_app(cred)
        
        self.db = firestore.client()
    
    def verify_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """Verify Firebase ID token and return user info"""
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            print(f"Token verification failed: {e}")
            return None
    
    def get_user_habits(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all habits for a user"""
        try:
            habits_ref = self.db.collection('users').document(user_id).collection('habits')
            habits = habits_ref.stream()
            
            result = []
            for habit in habits:
                habit_data = habit.to_dict()
                habit_data['id'] = habit.id
                result.append(habit_data)
            
            return result
        except Exception as e:
            print(f"Error getting user habits: {e}")
            return []
    
    def save_habit_data(self, user_id: str, habit_data: Dict[str, Any]) -> bool:
        """Save or update habit data for a user"""
        try:
            # Create a main habit document
            habit_ref = self.db.collection('users').document(user_id).collection('habits').document('main')
            
            # Add timestamp for sync tracking
            habit_data['last_updated'] = firestore.SERVER_TIMESTAMP
            habit_data['updated_by'] = user_id
            
            # Ensure dates are properly formatted
            if 'completedDates' in habit_data:
                habit_data['completedDates'] = [str(d) for d in habit_data['completedDates']]
            if 'notDoneDates' in habit_data:
                habit_data['notDoneDates'] = [str(d) for d in habit_data['notDoneDates']]
            
            habit_ref.set(habit_data, merge=True)
            return True
        except Exception as e:
            print(f"Error saving habit data: {e}")
            return False
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile information"""
        try:
            profile_ref = self.db.collection('profiles').document(user_id)
            profile = profile_ref.get()
            
            if profile.exists:
                return profile.to_dict()
            else:
                # Create default profile
                default_profile = {
                    'created_at': firestore.SERVER_TIMESTAMP,
                    'subscription_tier': 'free',
                    'subscription_status': 'active'
                }
                profile_ref.set(default_profile)
                return default_profile
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return None
    
    def update_subscription(self, user_id: str, subscription_data: Dict[str, Any]) -> bool:
        """Update user subscription information"""
        try:
            profile_ref = self.db.collection('profiles').document(user_id)
            subscription_update = {
                'subscription_tier': subscription_data.get('tier', 'free'),
                'subscription_status': subscription_data.get('status', 'active'),
                'stripe_customer_id': subscription_data.get('stripe_customer_id'),
                'subscription_updated_at': firestore.SERVER_TIMESTAMP
            }
            
            profile_ref.update(subscription_update)
            return True
        except Exception as e:
            print(f"Error updating subscription: {e}")
            return False
    
    def sync_habit_data(self, user_id: str, local_data: Dict[str, Any], last_sync: Optional[str] = None) -> Dict[str, Any]:
        """Sync local habit data with Firestore, handling conflicts"""
        try:
            habit_ref = self.db.collection('users').document(user_id).collection('habits').document('main')
            server_data = habit_ref.get()
            
            if not server_data.exists:
                # No server data, save local data
                self.save_habit_data(user_id, local_data)
                return {
                    'status': 'success',
                    'action': 'local_to_server',
                    'data': local_data
                }
            
            server_habit = server_data.to_dict()
            server_timestamp = server_habit.get('last_updated')
            
            # Simple conflict resolution: most recent wins
            # In a production app, you might want more sophisticated merging
            if last_sync and server_timestamp:
                server_time = server_timestamp.timestamp() if hasattr(server_timestamp, 'timestamp') else 0
                local_time = datetime.fromisoformat(last_sync.replace('Z', '+00:00')).timestamp()
                
                if server_time > local_time:
                    # Server data is newer
                    return {
                        'status': 'success',
                        'action': 'server_to_local',
                        'data': server_habit
                    }
            
            # Save local data to server
            self.save_habit_data(user_id, local_data)
            return {
                'status': 'success',
                'action': 'local_to_server',
                'data': local_data
            }
            
        except Exception as e:
            print(f"Error syncing habit data: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }