import os
from flask import Flask, jsonify, render_template, redirect, url_for
from flask_login import current_user
from flask_wtf.csrf import CSRFProtect
from services.logging_service import logging_service
from core.application_manager import ApplicationManager
from werkzeug.middleware.proxy_fix import ProxyFix
from models.job_seeker import JobSeeker
from auth.routes import auth_bp
from extensions import db, migrate, login_manager, init_app as init_extensions

logger = logging_service.get_structured_logger(__name__)

async def create_app():
    """Application factory function"""
    app = Flask(__name__,
                static_url_path='/static',
                static_folder='static')
    try:
        # Load configuration
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-testing')
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SERVER_NAME'] = None  # Allow all hostnames
        csrf = CSRFProtect()
        csrf.init_app(app)
        # Fix referrer check issues
        app.config['WTF_CSRF_SSL_STRICT'] = False
        app.config['WTF_CSRF_CHECK_DEFAULT'] = True
        app.config['WTF_CSRF_METHODS'] = ['POST', 'PUT', 'PATCH', 'DELETE']
        
        # Support for proxy headers
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
        
        # Initialize extensions
        init_extensions(app)
        
        # Create database tables
        with app.app_context():
            db.create_all()
            logger.info("Database tables created successfully")

        # Register error handlers
        @app.errorhandler(404)
        def not_found_error(error):
            return jsonify({"error": "Not found", "message": str(error)}), 404

        @app.errorhandler(500)
        def internal_error(error):
            return jsonify({"error": "Internal server error", "message": str(error)}), 500

        # Add a health check endpoint
        @app.route('/health')
        def health_check():
            return jsonify({"status": "healthy"}), 200

        @app.route('/')
        def index():
            if current_user.is_authenticated:
                return redirect(url_for('employer.dashboard'))
            return redirect(url_for('auth.login'))

        # Register blueprints
        app.register_blueprint(auth_bp, url_prefix='/auth')
        
        # Import and register employer blueprint
        from models.employer.routes import employer_bp
        app.register_blueprint(employer_bp, url_prefix='/employer')
        
        # Initialize using ApplicationManager
        app_manager = ApplicationManager()
        app_manager.app = app
        
        return app
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
