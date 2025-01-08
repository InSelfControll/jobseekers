from flask import Flask
from auth.routes import auth_bp
from admin.routes import admin_bp
from employer.routes import employer_bp
from job.routes import job_bp
from sso.routes import sso_bp

def init_routes(app: Flask):
    """Initialize and register all application blueprints"""
    # Register authentication and SSO blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(sso_bp)
    
    # Register core feature blueprints
    app.register_blueprint(employer_bp)
    app.register_blueprint(job_bp)
    
    # Register admin blueprint
    app.register_blueprint(admin_bp)