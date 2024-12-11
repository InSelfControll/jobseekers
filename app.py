import os
import logging
from quart import Quart, current_app
from extensions import db, login_manager, init_db, logger, Base
from contextlib import asynccontextmanager

def create_app():
    app = Quart(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "dev_key"
    
    # Initialize extensions
    try:
        # Setup database URL
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL environment variable is not set")
        
        # Configure Flask-SQLAlchemy
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)
        logger.info("Flask-SQLAlchemy initialized successfully")
        
        # Initialize async database
        engine, session_factory = init_db(app)
        app.engine = engine
        app.session_factory = session_factory
        logger.info("Async database initialized successfully")
        
        # Initialize login manager
        # Initialize login manager (only once)
        login_manager.init_app(app)
        login_manager.login_view = 'auth.login'
        logger.info("Login manager initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise RuntimeError(f"Application initialization failed: {str(e)}")
    
    # Register blueprints
    from routes.employer_routes import employer_bp
    from routes.job_routes import job_bp
    from routes.auth_routes import auth_bp
    
    app.register_blueprint(employer_bp)
    app.register_blueprint(job_bp)
    app.register_blueprint(auth_bp)
    
    @app.before_serving
    async def create_tables():
        try:
            async with app.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    return app

# Create the application instance
app = create_app()

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login (sync version)"""
    from models import Employer
    try:
        return Employer.query.get(int(user_id))
    except Exception as e:
        logger.error(f"Error loading user: {e}")
        return None

@asynccontextmanager
async def get_db():
    """Async context manager for database sessions"""
    if not hasattr(current_app, 'session_factory'):
        raise RuntimeError("Database session not initialized")
    try:
        async with current_app.session_factory() as session:
            yield session
    except Exception as e:
        logger.error(f"Database session error: {e}")
        raise RuntimeError(f"Failed to create database session: {str(e)}")