
import os
import logging
from flask import Flask, jsonify
from extensions import db, login_manager, init_db, logger

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "dev_key"
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour token expiry
    app.config['WTF_CSRF_SSL_STRICT'] = True
    
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' https: data:; connect-src 'self' https://*.browser-intake-us5-datadoghq.com"
        
        # Set proper MIME types for assets
        if response.mimetype == 'text/plain':
            if response.headers['Content-Disposition'].endswith('.css'):
                response.mimetype = 'text/css'
            elif response.headers['Content-Disposition'].endswith('.js'):
                response.mimetype = 'application/javascript'
        return response

    from flask_wtf.csrf import CSRFProtect, CSRFError
    csrf = CSRFProtect(app)
    
    # CSRF error handler
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return jsonify({'error': 'CSRF token validation failed'}), 400
    
    # Configure database
    if os.environ.get("DATABASE_URL"):
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{os.environ.get('PGUSER')}:{os.environ.get('PGPASSWORD')}@{os.environ.get('PGHOST')}:{os.environ.get('PGPORT')}/{os.environ.get('PGDATABASE')}"
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    try:
        # Initialize database
        init_db(app)
        
        # Initialize login manager
        login_manager.init_app(app)
        login_manager.login_view = 'auth.login'
        
        logger.info("Application initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise RuntimeError(f"Application initialization failed: {str(e)}")
    
    # Register blueprints
    from routes.auth_routes import auth_bp
    from routes.employer_routes import employer_bp
    from routes.job_routes import job_bp
    from routes.admin_routes import admin_bp
    from routes.sso_routes import sso_bp
    from flask import redirect, url_for

    app.register_blueprint(auth_bp)
    app.register_blueprint(employer_bp)
    app.register_blueprint(job_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(sso_bp)

    # Add root route
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))
    
    with app.app_context():
        db.create_all()
        logger.info("Database tables created successfully")
    
    return app

# Create the application instance
app = create_app()

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    from models import Employer
    try:
        return Employer.query.get(int(user_id))
    except Exception as e:
        logger.error(f"Error loading user: {e}")
        return None
