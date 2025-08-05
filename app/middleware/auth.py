from functools import wraps
from flask import request, jsonify, g
from app.services.firebase_service import FirebaseService


def require_auth(f):
    """Decorator to require Firebase authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        id_token = auth_header.split('Bearer ')[1]
        firebase_service = FirebaseService()
        
        user_info = firebase_service.verify_token(id_token)
        if not user_info:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Store user info in Flask's g object for use in the route
        g.user_id = user_info['uid']
        g.user_email = user_info.get('email')
        g.user_info = user_info
        
        return f(*args, **kwargs)
    
    return decorated_function


def optional_auth(f):
    """Decorator for optional authentication (allows both authenticated and anonymous access)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            id_token = auth_header.split('Bearer ')[1]
            firebase_service = FirebaseService()
            
            user_info = firebase_service.verify_token(id_token)
            if user_info:
                g.user_id = user_info['uid']
                g.user_email = user_info.get('email')
                g.user_info = user_info
            else:
                g.user_id = None
        else:
            g.user_id = None
        
        return f(*args, **kwargs)
    
    return decorated_function


def check_subscription_tier(required_tier='premium'):
    """Decorator to check if user has required subscription tier"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'user_id') or not g.user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            firebase_service = FirebaseService()
            profile = firebase_service.get_user_profile(g.user_id)
            
            if not profile:
                return jsonify({'error': 'User profile not found'}), 404
            
            user_tier = profile.get('subscription_tier', 'free')
            
            # Simple tier checking (you might want more sophisticated logic)
            tier_hierarchy = {'free': 0, 'premium': 1, 'enterprise': 2}
            required_level = tier_hierarchy.get(required_tier, 1)
            user_level = tier_hierarchy.get(user_tier, 0)
            
            if user_level < required_level:
                return jsonify({
                    'error': 'Subscription upgrade required',
                    'required_tier': required_tier,
                    'current_tier': user_tier
                }), 403
            
            g.subscription_tier = user_tier
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator