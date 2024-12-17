
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

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO()

def init_db(app):
    """Initialize database with SQLAlchemy"""
    try:
        db.init_app(app)
        migrate.init_app(app, db)
        logger.info("Database initialized successfully")
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
