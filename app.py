import os
from flask import redirect, url_for, jsonify, request, g
from flask_wtf.csrf import CSRFProtect, CSRFError
from extensions import create_app, db, login_manager, logger

# Create the application instance
app = create_app()
csrf = CSRFProtect(app)

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' https: data:; connect-src 'self' https://*.browser-intake-us5-datadoghq.com"
    
    # Set proper MIME types for assets
    if '.js' in request.path:
        response.headers['Content-Type'] = 'application/javascript'
    elif '.css' in request.path:
        response.headers['Content-Type'] = 'text/css'
    return response


@app.route('/.well-known/acme-challenge/<path:path>')
def acme_challenge(path):
    return send_from_directory(app.static_folder + '/.well-known/acme-challenge', path)

# CSRF error handler
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    return jsonify({'error': 'CSRF token validation failed'}), 400

# Register blueprints
from routes.auth_routes import auth_bp
from routes.employer_routes import employer_bp
from routes.job_routes import job_bp
from routes.admin_routes import admin_bp
from routes.sso_routes import sso_bp

app.register_blueprint(auth_bp)
app.register_blueprint(employer_bp)
app.register_blueprint(job_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(sso_bp)

# Add root route
@app.route('/')
def index():
    return redirect(url_for('auth.login'))

# Initialize database tables
with app.app_context():
    db.create_all()
    logger.info("Database tables created successfully")

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    from models import Employer
    from extensions import db
    try:
        return db.session.get(Employer, int(user_id))
    except Exception as e:
        logger.error(f"Error loading user: {e}")
        return None

app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "dev_key"
app.config.update(
    WTF_CSRF_ENABLED=True,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_PATH='/'
)

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    @app.before_request
    def handle_custom_domain():
        host = request.headers.get('Host', '').lower()
        if host != app.config['PRIMARY_DOMAIN']:
            from models import Employer #Import here to avoid circular import
            employer = Employer.query.filter_by(sso_domain=host, domain_verified=True).first()
            if employer:
                g.custom_domain = True
                g.domain_config = {
                    'sso_provider': employer.sso_provider,
                    'sso_config': employer.sso_config
                }
            else:
                g.custom_domain = False

    return app


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)