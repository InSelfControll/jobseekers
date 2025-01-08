from flask import Flask
from flask_migrate import Migrate, upgrade, init as migrate_init
from app import create_app
from extensions import db
import logging
import os
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_migrations():
    """Initialize and run database migrations"""
    try:
        # Await the create_app coroutine
        app = await create_app()
        
        # Ensure instance folder exists
        instance_path = os.path.join(os.path.dirname(__file__), 'instance')
        os.makedirs(instance_path, exist_ok=True)
        
        # Initialize migrations
        migrate = Migrate()
        migrate.init_app(app, db, directory='migrations')
        
        with app.app_context():
            try:
                logger.info("Starting database migration process...")
                
                # Initialize migrations if not already done
                if not os.path.exists('migrations'):
                    logger.info("Initializing new migration repository...")
                    migrate_init(directory='migrations')
                    
                # Import Flask-Migrate command module
                from flask_migrate import stamp, revision, migrate as migrate_command
                
                # Create initial migration
                logger.info("Creating migration...")
                migrate_command(directory='migrations', message='Initial migration')
                
                # Apply migrations
                logger.info("Applying migrations...")
                upgrade(directory='migrations')
                
                logger.info("Database migration completed successfully")
            except Exception as e:
                logger.error(f"Error during migration: {e}")
                raise
    except Exception as e:
        logger.error(f"Migration initialization failed: {e}")
        raise

if __name__ == "__main__":
    # Run the async function using asyncio
    asyncio.run(init_migrations())
