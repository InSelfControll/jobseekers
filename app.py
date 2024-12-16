
from flask import Flask, redirect, url_for, jsonify, request, g, send_from_directory
from flask_wtf.csrf import CSRFProtect, CSRFError
from extensions import db, login_manager, logger
from routes.auth_routes import auth_bp
from routes.employer_routes import employer_bp
from routes.job_routes import job_bp
from routes.admin_routes import admin_bp
from routes.sso_routes import sso_bp
from models import Employer
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf = CSRFProtect(app)
    
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
        return jsonify({'error': 'CSRF token validation failed'}), 400

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
