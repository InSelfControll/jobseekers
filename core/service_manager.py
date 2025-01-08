import os
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import timedelta
from flask import Flask
from services.logging_service import logging_service
from core.service_registry import service_registry
from services.bot_service import BotService
from core.service_interface import ServiceInterface
from extensions import db, init_app
from flask_migrate import Migrate, upgrade

logger = logging_service.get_structured_logger(__name__)

class UnifiedServiceManager(ServiceInterface):
    """Unified service manager combining functionality from app.py and main.py"""
    
    def __init__(self):
        super().__init__()
        self.app = None
        
        # Register required services
        service_registry.register_service('ssl', required=True)
        service_registry.register_service('bot', required=True)
        service_registry.register_service('database', required=True)
        
    async def initialize_all_services(self) -> bool:
        """Initialize all required services"""
        try:
            logger.info("Starting service initialization...")
            
            # Initialize Flask app
            if not await self.initialize_flask_app():
                return False
                
            # Initialize Database
            if not await self.initialize_database():
                return False
                
            # Initialize services through registry
            ssl_success = await service_registry._initialize_service('ssl')
            bot_success = await service_registry._initialize_service('bot')
            
            status_report = self.get_status_report()
            logger.info("Service initialization completed", extra={"status": status_report})
            
            return all([ssl_success, bot_success])
            
        except Exception as e:
            logger.error(f"Service initialization failed: {e}")
            return False
            
    async def initialize_flask_app(self) -> bool:
        """Initialize Flask application"""
        try:
            self.app = Flask(__name__)
            self.app.config.from_object('config.Config')
            
            # Session configuration
            self.app.config.update(
                SESSION_PERMANENT=True,
                SESSION_TYPE='filesystem',
                SESSION_FILE_DIR='flask_session',
                SESSION_FILE_THRESHOLD=500,
                SESSION_COOKIE_SECURE=True,
                SESSION_COOKIE_HTTPONLY=True,
                SESSION_COOKIE_SAMESITE='Lax',
                PERMANENT_SESSION_LIFETIME=timedelta(hours=1),
                SESSION_COOKIE_NAME='secure_session',
                SESSION_COOKIE_PATH='/',
                SESSION_REFRESH_EACH_REQUEST=True
            )
            
            # Initialize extensions
            init_app(self.app)
            
            return True
            
        except Exception as e:
            logger.error(f"Flask app initialization failed: {e}")
            return False
            
    async def initialize_database(self) -> bool:
        """Initialize database with migrations"""
        try:
            migrate = Migrate(self.app, db, directory='migrations')
            
            with self.app.app_context():
                # Create tables
                db.create_all()
                
                # Handle migrations
                if not os.path.exists('migrations'):
                    os.system('flask db init')
                    
                try:
                    upgrade()
                except Exception as migration_error:
                    logger.warning(f"Migration warning: {migration_error}")
                    
            self.status.set_service_ready('database', True)
            return True
            
        except Exception as e:
            error_msg = f"Database initialization failed: {e}"
            logger.error(error_msg)
            self.status.set_service_ready('database', False, error_msg)
            return False
            
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all services"""
        health_status = {
            'status': 'healthy',
            'services': {}
        }
        
        for service_name in self.status.services_ready.keys():
            service_status = self.status.get_service_status(service_name)
            health_status['services'][service_name] = {
                'status': 'healthy' if service_status['ready'] else 'unhealthy',
                'error': service_status['error'],
                'last_init_time': service_status['initialization_time']
            }
            
            if not service_status['ready'] and self.required_services.get(service_name, False):
                health_status['status'] = 'unhealthy'
                
        return health_status
        
    async def cleanup_all_services(self):
        """Clean up all services during shutdown"""
        logger.info("Starting service cleanup...")
        
        # Cleanup services through registry
        await service_registry.cleanup_service('ssl')
        await service_registry.cleanup_service('bot')
        
        # Cleanup database
        if self.app:
            with self.app.app_context():
            
        # Cleanup database connections
        if self.app:
            with self.app.app_context():
                db.session.remove()
                
        logger.info("Service cleanup completed")
        
    def run_flask_app(self, host='0.0.0.0', port=3000):
        """Run Flask application"""
        if not self.app:
            raise RuntimeError("Flask app not initialized")
            
        try:
            self.app.run(
                host=host,
                port=port,
                debug=False,
                use_reloader=False,
                threaded=True
            )
        except Exception as e:
            logger.error(f"Flask server error: {e}")
            raise
            
    async def start(self):
        """Start all services and run the application"""
        try:
            if not await self.initialize_all_services():
                raise RuntimeError("Service initialization failed")
                
            self._running = True
            self.run_flask_app()
            
        except Exception as e:
            logger.error(f"Application startup failed: {e}")
            await self.cleanup_all_services()
            raise
            
    def stop(self):
        """Stop all services gracefully"""
        self._running = False
        asyncio.create_task(self.cleanup_all_services())from typing import Dict, Any
import logging
from services.logging_service import logging_service
from services.ssl_service import SSLService
from services.bot_service import BotService
from core.base_service_manager import BaseServiceManager

logger = logging_service.get_structured_logger(__name__)

class ServiceManager:
    """Manages all application services through service registry"""
    def __init__(self):
        self.logger = logging_service.get_structured_logger(__name__)
        
    async def initialize_services(self):
        """Initialize all required services through service registry"""
        try:
            return await service_registry.initialize_all_required_services()
        except Exception as e:
            self.logger.error(f"Service initialization failed: {e}")
            return False

    async def cleanup(self) -> bool:
        """Cleanup all services"""
        try:
            if self.ssl_service:
                await self.ssl_service.cleanup()
            if self.bot_service:
                await self.bot_service.cleanup()
            return True
        except Exception as e:
            logger.error(f"Service cleanup failed: {e}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Check services health status"""
        return {
            'ssl': self.ssl_service.is_healthy if self.ssl_service else False,
            'bot': self.bot_service.is_healthy if self.bot_service else False
        }
