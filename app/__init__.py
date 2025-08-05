from flask import Flask
import os


def create_app():
    """Application factory function"""
    # Get the directory containing this file
    instance_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    app = Flask(__name__, 
                template_folder=os.path.join(instance_path, 'templates'),
                static_folder=os.path.join(instance_path, 'static'))
    
    # Register routes
    from app.controllers.main_controller import main_bp
    app.register_blueprint(main_bp)
    
    return app