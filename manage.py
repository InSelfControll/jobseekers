from flask import Flask
from flask_migrate import upgrade
from app import create_app
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migrations():
    """Run database migrations programmatically"""
    try:
        app = create_app()
        with app.app_context():
            logger.info("Starting database migration...")
            upgrade()
            logger.info("Database migration completed successfully")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migrations()
