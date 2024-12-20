from flask import Flask
from flask_migrate import Migrate, upgrade
from app import create_app
from extensions import db
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_migrations():
    """Initialize and run database migrations"""
    try:
        app = create_app()
        
        # Ensure migrations directory exists
        if not os.path.exists('migrations'):
            os.makedirs('migrations')
            
        # Initialize migrations
        migrate = Migrate()
        migrate.init_app(app, db, directory='migrations')
        
        with app.app_context():
            try:
                logger.info("Starting database migration...")
                upgrade()
                logger.info("Database migration completed successfully")
            except Exception as e:
                logger.error(f"Error during migration: {e}")
                raise
    except Exception as e:
        logger.error(f"Migration initialization failed: {e}")
        raise

if __name__ == "__main__":
    init_migrations()
