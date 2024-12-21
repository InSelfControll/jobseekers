import logging
from datetime import timedelta
from flask import Flask, redirect, url_for, jsonify, request, g, send_from_directory, abort
from flask_login import current_user
from flask_session import Session
from flask_wtf.csrf import CSRFProtect, CSRFError, generate_csrf
from flask_migrate import Migrate
from extensions import db, login_manager
from routes.auth_routes import auth_bp
from routes.employer_routes import employer_bp
from routes.job_routes import job_bp
from routes.admin_routes import admin_bp
from routes.sso_routes import sso_bp
from models import Employer
import os
import asyncio
from bot.telegram_bot import start_bot
from services.monitoring_service import bot_monitor

def create_app():
    # Create an event loop for async operations
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
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
    
    app.config['DEBUG'] = True  # Enable debug mode for better error tracking
    
    # Enable debug logging
    if app.debug:
        app.logger.setLevel(logging.DEBUG)
    
    # Initialize extensions
    # Initialize database and migrations
    db.init_app(app)
    migrate = Migrate(app, db)
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
    
    # Initialize security components
    from secops.sec import init_csrf
    init_csrf(app)
    
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
    
    # Initialize Telegram bot asynchronously
    async def init_telegram_bot():
        try:
            await start_bot()
            app.logger.info("Telegram bot initialized successfully")
            bot_monitor.set_status("running")
        except Exception as e:
            app.logger.error(f"Failed to initialize Telegram bot: {e}")
            bot_monitor.set_status("error")
            bot_monitor.record_error(f"Bot initialization failed: {e}")

    @app.before_first_request
    def start_telegram_bot():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(init_telegram_bot())

    def is_admin_user():
        if not current_user.is_authenticated:
            return False
        allowed_admins = ['admin@hostme.co.il', 'admin@aijobsearch.tech']
        return current_user.email in allowed_admins

    @app.before_request
    def restrict_admin_access():
        if request.path.startswith('/admin/bot-monitoring'):
            if not is_admin_user():
                abort(403)  # Forbidden
    
    @app.before_request
    def handle_custom_domain():
        host = request.headers.get('Host', '').lower()
        if host != app.config.get('PRIMARY_DOMAIN'):
            # For development: Handle localhost testing
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
                
                # Setup domain if not already configured
                if not employer.ssl_enabled:
                    from services.domain_service import DomainService
                    domain_service = DomainService()
                    try:
                        # Use A record instead of CNAME
                        domain_service.dns_record_type = 'A'
                        domain_service.dns_target = '127.0.0.1'  # Replace with actual IP in production
                        success, message = domain_service.setup_custom_domain(employer.id)
                        if not success:
                            logger.error(f"Domain setup failed: {message}")
                    except Exception as e:
                        logger.error(f"Domain setup failed with exception: {e}")
            else:
                g.custom_domain = False

    return app
