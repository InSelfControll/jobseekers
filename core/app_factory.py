import os
from datetime import timedelta
from flask import Flask, jsonify, redirect, url_for, request, abort, g
from flask_login import current_user
from flask_session import Session

from core.error_handlers import register_error_handlers as register_core_error_handlers
from core.db_utils import cleanup_session, rollback_session
from services.logging_service import logging_service
from services.ssl_service import SSLService
from services.bot_service import BotService
from services.base import BaseServiceManager
from models import Employer
from extensions import init_app, db, login_manager

logger = logging_service.get_structured_logger(__name__)

def configure_session(app):
    """Configure session management settings"""
    app.permanent_session_lifetime = timedelta(days=14)
    app.config.update(
        SESSION_PERMANENT=True,
        SESSION_TYPE='filesystem',
        SESSION_FILE_DIR='flask_session',
        SESSION_FILE_THRESHOLD=500,
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        WTF_CSRF_TIME_LIMIT=3600,
        WTF_CSRF_SSL_STRICT=True,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=1),
        SESSION_COOKIE_NAME='secure_session',
        SESSION_COOKIE_PATH='/',
        SESSION_REFRESH_EACH_REQUEST=True
    )
    Session(app)

def register_error_handlers(app):
    """Register application error handlers"""
    register_core_error_handlers(app)

    # Register teardown handlers
    @app.teardown_request
    def cleanup_request(exc):
        if exc:
            logger.error(f'Request error occurred: {exc}')
            rollback_session()
        cleanup_session()

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        if exception:
            logger.error(f'Application context error: {exception}')
        cleanup_session()
def configure_security_headers(app):
    """Configure security headers for all responses"""
    @app.after_request
    def add_security_headers(response):
        response.headers.update({
            'X-Content-Type-Options': 'nosniff',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Content-Security-Policy': "default-src 'self' 'unsafe-inline' 'unsafe-eval' https: data:; connect-src 'self' https://*.browser-intake-us5-datadoghq.com"
        })
        return response

def setup_user_loader(app):
    """Configure user loader for Flask-Login"""
    @login_manager.user_loader
    def load_user(user_id):
        try:
            if not user_id:
                logger.error("User ID is None")
                return None
            try:
                user_id_int = int(user_id)
            except ValueError:
                logger.error(f"Invalid user ID format: {user_id}")
                return None
            
            try:
                user = db.session.get(Employer, user_id_int)
                if user is None:
                    logger.warning(f"No user found with ID: {user_id}")
                return user
            except (db.exc.SQLAlchemyError, db.exc.DBAPIError) as e:
                logger.error(f"Database error loading user {user_id}: {e}")
                return None

def configure_admin_access(app):
    """Configure admin access control"""
    def is_admin_user():
        if not current_user.is_authenticated:
            return False
        allowed_admins = ['admin@hostme.co.il', 'admin@aijobsearch.tech']
        return current_user.email in allowed_admins

    @app.before_request
    def restrict_admin_access():
        if request.path.startswith('/admin/bot-monitoring'):
            if not is_admin_user():
                abort(403)

def handle_custom_domains(app):
    """Handle custom domain configurations"""
    @app.before_request
    def handle_custom_domain():
        host = request.headers.get('Host', '').lower()
        if host != app.config.get('PRIMARY_DOMAIN'):
            if host.startswith('localhost') or host.startswith('127.0.0.1'):
                g.custom_domain = False
                return

            employer = Employer.query.filter_by(sso_domain=host).first()
            if employer and employer.domain_verified:
                g.custom_domain = True
                g.domain_config = {
                    'sso_provider': employer.sso_provider,
                    'sso_config': employer.sso_config,
                    'ssl_enabled': employer.ssl_enabled,
                    'domain': employer.sso_domain
                }
                
                if not employer.ssl_enabled:
                    from services.domain_service import DomainService
                    domain_service = DomainService()
                    try:
                        ip_address = '127.0.0.1'
                        if all(part.isdigit() and 0 <= int(part) <= 255 
                              for part in ip_address.split('.')):
                            domain_service.dns_record_type = 'A'
                            domain_service.dns_target = ip_address
                        else:
                            domain_service.dns_record_type = 'CNAME'
                            domain_service.dns_target = request.host
                        success, message = domain_service.setup_custom_domain(employer.id)
                        if not success:
                            logger.error(f"Domain setup failed: {message}")
                    except Exception as e:
                        logger.error(f"Domain setup failed with exception: {e}")
            else:
                g.custom_domain = False

def create_app():
    """Create and configure Flask application."""
    logger.info("Starting Flask application...")
    
    # Initialize Flask app
    app = Flask(__name__)
    logger.info("Loading configuration...")
    app.config.from_object('config.Config')
    
    # Configure template paths
    app.template_folder = 'templates'
    app.static_folder = 'static'
    # Configure session management
    configure_session(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Configure security headers
    configure_security_headers(app)
    
    # Initialize extensions and security
    from routes import init_routes
    from secops.sec import init_csrf
    init_app(app)
    init_csrf(app)
    init_routes(app)
    
    # Set up user loader
    setup_user_loader(app)
    
    # Configure admin access
    configure_admin_access(app)
    
    # Handle custom domains
    handle_custom_domains(app)
    
    # Root route
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))
    
    # Initialize services
    service_manager = ServiceManager()
    service_manager.initialize_services()
    app.service_manager = service_manager
    
    # Set secret key
    app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "dev_key"
    
    return app