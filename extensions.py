
import logging
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from datetime import timedelta

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize extensions with async support
db = SQLAlchemy(
    engine_options={
        'pool_pre_ping': True,
        'pool_size': 10,
        'max_overflow': 20,
        'pool_recycle': 300,
        'echo': True  # Enable SQL logging
    }
)
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO(cors_allowed_origins="*", async_mode='asgi', manage_session=False)

# Configure async session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

def setup_async_session(app):
    """Create async session factory after app is created"""
    try:
        database_url = app.config['SQLALCHEMY_DATABASE_URI']
        if not database_url.startswith('postgresql+asyncpg://'):
            database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')
        
        engine = create_async_engine(
            database_url,
            echo=True,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
        return async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    except Exception as e:
        logger.error(f"Failed to setup async session: {str(e)}")
        raise

def init_db(app):
    """Initialize database with SQLAlchemy and Flask-Migrate"""
    try:
        db.init_app(app)
        migrate.init_app(app, db, directory='migrations')
        with app.app_context():
            try:
                db.engine.connect()
                logger.info("Successfully connected to database")
            except Exception as conn_error:
                logger.error(f"Failed to connect to database: {conn_error}")
                raise
        logger.info("Database and migrations initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise RuntimeError(f"Failed to initialize database: {str(e)}")

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "dev_key"
    app.config.update(
        WTF_CSRF_ENABLED=True,
        WTF_CSRF_TIME_LIMIT=3600,
        WTF_CSRF_SSL_STRICT=True,
        PERMANENT_SESSION_LIFETIME=timedelta(days=14),
        MIME_TYPES={
            '.js': 'application/javascript',
            '.css': 'text/css',
            '.html': 'text/html'
        }
    )

    # Configure database
    if os.environ.get("DATABASE_URL"):
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
    else:
        app.config[
            'SQLALCHEMY_DATABASE_URI'] = f"postgresql://{os.environ.get('PGUSER')}:{os.environ.get('PGPASSWORD')}@{os.environ.get('PGHOST')}:{os.environ.get('PGPORT')}/{os.environ.get('PGDATABASE')}"

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    try:
        init_db(app)
        login_manager.init_app(app)
        login_manager.login_view = 'auth.login'
        socketio.init_app(app)
        logger.info("Application initialized successfully")
        return app
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise RuntimeError(f"Application initialization failed: {str(e)}")
