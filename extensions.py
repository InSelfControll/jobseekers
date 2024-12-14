import logging
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

def init_db(app):
    """Initialize database with SQLAlchemy"""
    try:
        db.init_app(app)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise RuntimeError(f"Failed to initialize database: {str(e)}")
