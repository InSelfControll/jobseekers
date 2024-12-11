import os
import logging
from quart import Quart, current_app
from extensions import login_manager, init_db, logger, Base
from contextlib import asynccontextmanager

def create_app():
    app = Quart(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "dev_key"
    
    # Database configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Initialize extensions
    try:
        engine, session_factory = init_db(app)
        app.engine = engine
        app.session_factory = session_factory
        logger.info("Database engine and session factory initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
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
async def load_user(user_id):
    from models import Employer
    try:
        async with app.session_factory() as session:
            user = await session.get(Employer, int(user_id))
            if user:
                await session.refresh(user)
            return user
    except Exception as e:
        logger.error(f"Error loading user: {e}")
        return None

async def get_db():
    if not hasattr(current_app, 'session_factory'):
        raise RuntimeError("Database session not initialized")
    async with current_app.session_factory() as session:
        yield session