import os
import logging
from quart import Quart
from extensions import login_manager, init_db, logger, Base
from contextlib import asynccontextmanager

def create_app():
    app = Quart(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "dev_key"
    
    # Database configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    
    # Initialize extensions
    engine, async_session = init_db(app)
    app.engine = engine
    app.async_session = async_session
    
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
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all, bind=engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    @app.teardown_appcontext
    async def shutdown_session(exception=None):
        if hasattr(app, 'async_session'):
            await app.async_session.remove()
    
    return app

# Create the application instance
app = create_app()

@login_manager.user_loader
async def load_user(user_id):
    from models import Employer
    try:
        async with app.async_session() as session:
            user = await session.get(Employer, int(user_id))
            await session.refresh(user)
            return user
    except Exception:
        return None

async def get_db():
    async with app.async_session() as session:
        yield session

# Context manager for application context
@asynccontextmanager
async def get_app_context():
    async with app.app_context():
        yield app
