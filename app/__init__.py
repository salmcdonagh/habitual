from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import os

# Application version
APP_VERSION = "v0.1.0"


def create_app():
    """Application factory function"""
    # Get the directory containing this file
    instance_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    app = Flask(__name__, 
                template_folder=os.path.join(instance_path, 'templates'),
                static_folder=os.path.join(instance_path, 'static'))
    
    # Configure CORS for API endpoints
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5001", 
                "https://habitual-api-rgv222zqha-uc.a.run.app",
                "https://*.run.app"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Endpoint not found'}), 404
        return render_template('index.html'), 404  # SPA fallback
    
    @app.errorhandler(500)
    def internal_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('index.html'), 500  # SPA fallback
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'habitual-api',
            'version': APP_VERSION
        })
    
    # Register routes
    from app.controllers.main_controller import main_bp
    app.register_blueprint(main_bp)
    
    return app