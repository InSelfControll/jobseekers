import logging
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from flask_login import LoginManager

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize extensions
Base = declarative_base()
login_manager = LoginManager()

def init_db(app):
    """Initialize database with SQLAlchemy"""
    # Create async engine
    engine = create_async_engine(
        app.config["SQLALCHEMY_DATABASE_URI"],
        echo=True,
    )
    
    # Create async session factory
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    return engine, async_session
