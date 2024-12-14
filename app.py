
import os
import logging
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from extensions import db, init_db, login_manager, logger
from services.email_service import mail
from itsdangerous import URLSafeTimedSerializer

csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "dev_key"
    app.config['WTF_CSRF_ENABLED'] = True
    
    # Email configuration
    app.config['MAIL_SERVER'] = os.environ.get('SMTP_SERVER', 'smtp.yourserver.com')
    app.config['MAIL_PORT'] = int(os.environ.get('SMTP_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('SMTP_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get('SMTP_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('SMTP_PASSWORD')
    app.ts = URLSafeTimedSerializer(app.secret_key)
    
    mail.init_app(app)
    
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
        csrf.init_app(app)
        logger.info("Application initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise RuntimeError(f"Application initialization failed: {str(e)}")
    
    # Register blueprints
    from routes.auth_routes import auth_bp
    from routes.employer_routes import employer_bp
    from routes.job_routes import job_bp
    from routes.admin_routes import admin_bp
    from flask import redirect, url_for

    app.register_blueprint(auth_bp)
    app.register_blueprint(employer_bp)
    app.register_blueprint(job_bp)
    app.register_blueprint(admin_bp)

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
