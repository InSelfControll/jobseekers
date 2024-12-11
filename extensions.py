import logging
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from urllib.parse import urlparse, urlunparse

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize extensions
db = SQLAlchemy()
Base = declarative_base()
login_manager = LoginManager()

def clean_database_url(url):
    """Clean and format database URL for async connection"""
    if not url:
        raise ValueError("DATABASE_URL environment variable is not set")
    
    try:
        # Parse the URL
        parsed = urlparse(url)
        
        # Convert to async format if needed
        if parsed.scheme == "postgresql" or parsed.scheme == "postgres":
            # Create new components with asyncpg
            new_components = list(parsed)
            new_components[0] = "postgresql+asyncpg"
            
            # Construct the new URL without query parameters
            # This ensures compatibility with asyncpg
            cleaned_url = urlunparse((
                new_components[0],  # scheme
                new_components[1],  # netloc
                new_components[2],  # path
                '',                # params
                '',                # query
                ''                 # fragment
            ))
            logger.info("Database URL cleaned successfully")
            return cleaned_url
            
        return url
    except Exception as e:
        logger.error(f"Error cleaning database URL: {e}")
        raise ValueError(f"Failed to clean database URL: {str(e)}")

def init_db(app):
    """Initialize database with SQLAlchemy"""
    try:
        # Get database URL
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL environment variable is not set")
        
        logger.info("Initializing database connections...")
        
        # Configure async SQLAlchemy engine
        async_url = clean_database_url(db_url)
        logger.debug(f"Using async URL format (scheme only): {urlparse(async_url).scheme}")
        
        engine = create_async_engine(
            async_url,
            echo=True,
            future=True,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10
        )
        logger.info("Async engine created successfully")
        
        # Create async session factory
        async_session = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False
        )
        logger.info("Async session factory created successfully")
        
        return engine, async_session
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise RuntimeError(f"Failed to initialize database: {str(e)}")
