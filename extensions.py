import os
from contextlib import contextmanager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO
from services.logging_service import logging_service

logger = logging_service.get_structured_logger(__name__)

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO()

def init_app(app):
    """Initialize Flask extensions"""
    try:
        # Ensure instance folder exists
        instance_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance')
        os.makedirs(instance_path, exist_ok=True)
        
        # Set database URI if not already set
        if 'SQLALCHEMY_DATABASE_URI' not in app.config:
            db_path = os.path.join(instance_path, 'app.db')
            app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Initialize extensions
        db.init_app(app)
        migrate.init_app(app, db)
        login_manager.init_app(app)
        socketio.init_app(app, 
                     cors_allowed_origins="*",
                     async_mode='threading',
                     manage_session=False,
                     logger=True,
                     engineio_logger=True)
        
        # Test database connection within app context
        with app.app_context():
            try:
                db.engine.connect()
                logger.info("Database connection successful")
            except Exception as e:
                logger.error(f"Database connection failed: {e}")
                raise
    except Exception as e:
        logger.error(f"Failed to initialize extensions: {e}")
        raise

    @login_manager.user_loader
    def load_user(user_id):
        from models.employer import Employer
        return Employer.query.get(int(user_id))

def init_database(app):
    """Initialize database and tenant databases after core extensions are set up"""
    try:
        db.init_app(app)
        migrate.init_app(app, db, directory='migrations')
        
        with app.app_context():
            try:
                # Connect to main database
                db.engine.connect()
                logger.info("Successfully connected to main database")
                
                # Create or verify main tables
                db.create_all()
                logger.info("Main database tables created successfully")
                
                # Initialize tenant databases
                # Import model only when needed
                from models import Employer
                employers = Employer.query.all()
                for employer in employers:
                    if employer.tenant_id:
                        tenant_db_url = app.config['SQLALCHEMY_DATABASE_URI'].replace(
                            app.config['SQLALCHEMY_DATABASE_NAME'],
                            f"tenant_{employer.tenant_id}"
                        )
                        tenant_engine = db.create_engine(tenant_db_url)
                        try:
                            tenant_engine.connect()
                            logger.info(f"Connected to tenant database for {employer.company_name}")
                        except Exception as tenant_error:
                            logger.error(f"Failed to connect to tenant database for {employer.company_name}: {tenant_error}")
                            
            except Exception as conn_error:
                logger.error(f"Failed to connect to database: {conn_error}")
                raise
                
        logger.info("Database and migrations initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise RuntimeError(f"Failed to initialize database: {str(e)}")

def get_tenant_db_session(tenant_id):
    """Get a database session for a specific tenant"""
    try:
        # Import Flask current_app only when needed
        from flask import current_app
        from sqlalchemy.orm import sessionmaker
        
        tenant_db_url = current_app.config['SQLALCHEMY_DATABASE_URI'].replace(
            current_app.config['SQLALCHEMY_DATABASE_NAME'],
            f"tenant_{tenant_id}"
        )
        tenant_engine = db.create_engine(tenant_db_url)
        Session = sessionmaker(bind=tenant_engine)
        return Session()
    except Exception as e:
        logger.error(f"Failed to get tenant database session: {e}")
        raise
def cleanup_extensions():
    """Cleanup all extensions during shutdown"""
    logger.info("Starting extensions cleanup...")
    
    try:
        # Only cleanup if we have an application context
        if current_app:
            with current_app.app_context():
                # Cleanup database sessions
                if hasattr(db, 'session'):
                    db.session.remove()
                
                # Close database engine connections
                if hasattr(db, 'engine') and db.engine:
                    db.engine.dispose()
                
                # Cleanup socketio connections
                if socketio:
                    socketio.stop()
        
        logger.info("Extensions cleanup completed successfully")
    except Exception as e:
        logger.error(f"Error during extensions cleanup: {e}")
        # Log error but don't raise to allow cleanup to continue

@contextmanager
def tenant_session_scope(tenant_id):
    """Context manager for handling tenant database sessions"""
    session = None
    try:
        session = get_tenant_db_session(tenant_id)
        yield session
        session.commit()
    except Exception as e:
        if session:
            session.rollback()
        logger.error(f"Error in tenant session for tenant {tenant_id}: {e}")
        raise
    finally:
        if session:
            session.close()
def create_async_session_factory(app):
    """Create async session factory after app is created"""
    try:
        # Import async dependencies only when needed
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
        
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
        
        async_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Register cleanup handler
        async def cleanup_async_engine():
            await engine.dispose()
            
        app.teardown_appcontext(lambda _: asyncio.create_task(cleanup_async_engine()))
        
        return async_session_factory
    except Exception as e:
        logger.error(f"Failed to setup async session: {str(e)}")
        raise RuntimeError(f"Async session factory creation failed: {str(e)}")
