from flask import Blueprint, render_template, request, redirect, url_for, jsonify, g
from app.models.habit_tracker import HabitTracker
from app.middleware.auth import optional_auth, require_auth, check_subscription_tier
from app.services.firebase_service import FirebaseService
import json

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@optional_auth
def home():
    """Home page route - works for both authenticated and anonymous users"""
    if hasattr(g, 'user_id') and g.user_id:
        # Authenticated user - could load from Firestore
        # For now, still use local tracker as fallback
        tracker = HabitTracker()
        is_authenticated = True
        user_email = g.user_email
    else:
        # Anonymous user - use local tracker
        tracker = HabitTracker()
        is_authenticated = False
        user_email = None
    
    return render_template('index.html',
                         started_date=tracker.get_started_date(),
                         frequency=tracker.get_frequency(),
                         counter=tracker.get_counter(),
                         habit_done=tracker.is_done_today(),
                         not_done=tracker.is_not_done_today(),
                         why_text=tracker.get_why_today(),
                         success_percentage=tracker.get_success_percentage(),
                         completed_dates=tracker.get_completed_dates(),
                         not_done_dates=tracker.get_not_done_dates(),
                         why_entries=tracker.get_why_entries(),
                         is_authenticated=is_authenticated,
                         user_email=user_email)


@main_bp.route('/api/sync', methods=['POST'])
@require_auth
def sync_habits():
    """Sync habit data between client and server"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        firebase_service = FirebaseService()
        
        # Get the habit data and last sync timestamp from request
        habit_data = data.get('habitData', {})
        last_sync = data.get('lastSync')
        
        # Perform sync
        sync_result = firebase_service.sync_habit_data(g.user_id, habit_data, last_sync)
        
        return jsonify(sync_result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/api/habits', methods=['GET'])
@require_auth
def get_habits():
    """Get user's habits from Firestore"""
    try:
        firebase_service = FirebaseService()
        habits = firebase_service.get_user_habits(g.user_id)
        
        return jsonify({
            'status': 'success',
            'habits': habits
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/api/habits', methods=['POST'])
@require_auth
def save_habits():
    """Save user's habits to Firestore"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        firebase_service = FirebaseService()
        success = firebase_service.save_habit_data(g.user_id, data)
        
        if success:
            return jsonify({'status': 'success'})
        else:
            return jsonify({'error': 'Failed to save data'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/api/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get user profile and subscription info"""
    try:
        firebase_service = FirebaseService()
        profile = firebase_service.get_user_profile(g.user_id)
        
        if profile:
            return jsonify({
                'status': 'success',  
                'profile': profile
            })
        else:
            return jsonify({'error': 'Profile not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/api/premium-feature', methods=['GET'])
@require_auth
@check_subscription_tier('premium')
def premium_feature():
    """Example premium feature - requires premium subscription"""
    return jsonify({
        'message': 'Welcome to premium features!',
        'tier': g.subscription_tier,
        'features': ['Advanced analytics', 'Multiple habits', 'Export data']
    })


# Legacy route for backward compatibility
@main_bp.route('/toggle-habit', methods=['POST'])
def toggle_habit():
    """Toggle habit completion for today - legacy route"""
    tracker = HabitTracker()
    tracker.toggle_today()
    
    return redirect(url_for('main.home'))