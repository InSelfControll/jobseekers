import os
import logging
from quart import Quart
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

def create_app():
    app = Quart(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"
    
    # Database configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Register blueprints
    from routes.employer_routes import employer_bp
    from routes.job_routes import job_bp
    from routes.auth_routes import auth_bp
    
    app.register_blueprint(employer_bp)
    app.register_blueprint(job_bp)
    app.register_blueprint(auth_bp)
    
    # Create database tables
    @app.before_serving
    async def create_tables():
        async with app.app_context():
            try:
                db.create_all()
                logger.info("Database tables created successfully")
            except Exception as e:
                logger.error(f"Error creating database tables: {e}")
                raise
    
    return app

app = create_app()

@login_manager.user_loader
def load_user(user_id):
    from models import Employer
    return Employer.query.get(int(user_id))
