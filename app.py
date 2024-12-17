import logging
from datetime import timedelta
from flask import Flask, redirect, url_for, jsonify, request, g, send_from_directory
from flask_session import Session
from flask_wtf.csrf import CSRFProtect, CSRFError
from extensions import db, login_manager
from routes.auth_routes import auth_bp
from routes.employer_routes import employer_bp
from routes.job_routes import job_bp
from routes.admin_routes import admin_bp
from routes.sso_routes import sso_bp
from models import Employer
import os

def create_app():
    """Create and configure the Flask application."""
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True
    )
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Log startup information
    logger.info("Starting Flask application...")
    
    # Log startup information
    logger.info("Starting Flask application...")
    
    app = Flask(__name__)
    logger.info("Loading configuration...")
    app.config.from_object('config.Config')
    
    # Initialize SSL service
    try:
        from services.ssl_service import setup_cert_renewal_check
        setup_cert_renewal_check()
        logger.info("SSL certificate renewal service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize SSL service: {e}")
    
    # Register error handlers
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f'Server Error: {error}')
        return jsonify(error="Internal Server Error"), 500
        
    @app.errorhandler(404)
    def not_found_error(error):
        logger.error(f'Not Found: {error}')
        return jsonify(error="Not Found"), 404
    
    # Configure for ASGI server
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    app.config['SERVER_NAME'] = None  # Let Hypercorn handle the binding
    app.config['APPLICATION_ROOT'] = '/'
    app.config['DEBUG'] = True  # Enable debug mode for better error tracking
    
    # Enable debug logging
    if app.debug:
        app.logger.setLevel(logging.DEBUG)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    app.permanent_session_lifetime = timedelta(days=14)
    app.config.update(
        SESSION_PERMANENT=True,
        SESSION_TYPE='filesystem',
        SESSION_FILE_DIR='flask_session',
        SESSION_FILE_THRESHOLD=500,
        SESSION_COOKIE_SECURE=False,  # Set to False for development
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        WTF_CSRF_TIME_LIMIT=3600,
        WTF_CSRF_SSL_STRICT=False  # Set to False for development
    )
    
    Session(app)
    
    # Initialize CSRF protection
    csrf = CSRFProtect(app)
    csrf.init_app(app)
    
    # Ensure CSRF token is available in all templates
    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)
    
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' https: data:; connect-src 'self' https://*.browser-intake-us5-datadoghq.com"
        return response

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'CSRF token validation failed', 'code': 'CSRF_ERROR'}), 400
        return jsonify({'error': 'Security validation failed. Please try again.'}), 400

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(employer_bp)
    app.register_blueprint(job_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(sso_bp)

    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(Employer, int(user_id))
        except Exception as e:
            logger.error(f"Error loading user: {e}")
            return None

    app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "dev_key"
    
    @app.before_request
    def handle_custom_domain():
        host = request.headers.get('Host', '').lower()
        if host != app.config.get('PRIMARY_DOMAIN'):
            employer = Employer.query.filter_by(sso_domain=host, domain_verified=True).first()
            if employer:
                g.custom_domain = True
                g.domain_config = {
                    'sso_provider': employer.sso_provider,
                    'sso_config': employer.sso_config,
                    'ssl_enabled': employer.ssl_enabled,
                    'domain': employer.sso_domain
                }
            else:
                g.custom_domain = False

    return app