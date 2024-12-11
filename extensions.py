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
        if parsed.scheme == "postgresql":
            # Create new components with asyncpg
            new_components = list(parsed)
            new_components[0] = "postgresql+asyncpg"
            
            # Remove problematic parameters from query
            if parsed.query:
                from urllib.parse import parse_qs, urlencode
                query_params = parse_qs(parsed.query)
                # Remove problematic parameters
                for param in ['sslmode', 'target_session_attrs']:
                    query_params.pop(param, None)
                new_components[4] = urlencode(query_params, doseq=True)
            
            # Construct the new URL
            cleaned_url = urlunparse(new_components)
            logger.info(f"Database URL cleaned successfully")
            return cleaned_url
            
        return url
    except Exception as e:
        logger.error(f"Error cleaning database URL: {e}")
        raise

def init_db(app):
    """Initialize database with SQLAlchemy"""
    try:
        # Initialize SQLAlchemy with the app
        db.init_app(app)
        
        # Get and clean database URL
        db_url = clean_database_url(os.environ.get("DATABASE_URL"))
        logger.info("Database URL cleaned and ready")
        
        # Create async engine
        engine = create_async_engine(
            db_url,
            echo=True,
            future=True,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10
        )
        
        # Create async session factory
        async_session = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("Database initialization successful")
        return engine, async_session
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
