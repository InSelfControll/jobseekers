
from app import create_app
from extensions import db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize database with proper error handling"""
    try:
        app = create_app()
        with app.app_context():
            db.create_all()
            logger.info("Database tables created successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

if __name__ == "__main__":
    init_database()
