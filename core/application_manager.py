import os
import asyncio
import threading
import logging
from typing import Dict, Any
from services.logging_service import logging_service
from core.service_registry import service_registry

logger = logging_service.get_structured_logger(__name__)

class ApplicationManager:
    def __init__(self):
        self._running = False
        self.app = None
        self.logger = logger
        
        # Register services
        service_registry.register_service('database', required=True)
        service_registry.register_service('ssl', required=False)
        service_registry.register_service('bot', required=False)

    async def _initialize_database(self) -> bool:
        """Initialize database"""
        try:
            from extensions import db
            with self.app.app_context():
                db.create_all()
            return True
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            return False

    async def initialize(self) -> bool:
        """Initialize application and its services using service registry"""
        try:
            self.logger.info("Starting application initialization...")
            
            # Database and other core services are already initialized in create_app()
            
            # Register services
            service_registry.register_service('database', required=True)
            service_registry.register_service('migrations', required=True)
            service_registry.register_service('auth', required=True)
            service_registry.register_service('websocket', required=True)
            service_registry.register_service('ssl', required=False)
            service_registry.register_service('bot', required=False)
            
            # Register initializers
            service_registry.register_initializer('database', lambda: db.init_app(self.app))
            service_registry.register_initializer('migrations', lambda: migrate.init_app(self.app, db))
            service_registry.register_initializer('auth', lambda: login_manager.init_app(self.app))
            service_registry.register_initializer('websocket', lambda: socketio.init_app(self.app))
            
            # Database is already initialized, just mark it as ready
            service_registry.mark_service_ready('database')
            
            # Initialize error handlers
            from core.error_handlers import internal_error, not_found_error
            self.app.register_error_handler(500, internal_error)
            self.app.register_error_handler(404, not_found_error)
            
            # Add security headers
            from core.security import add_security_headers
            self.app.after_request(add_security_headers)
            
            # Initialize SSL if configured
            if self._ssl_required():
                await service_registry._initialize_service('ssl')
            
            # Initialize bot if configured
            if self._bot_required():
                await service_registry._initialize_service('bot')
            
            self._running = True
            self.logger.info("Application initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Application initialization failed: {str(e)}")
            await self.cleanup()
            return False

    def _ssl_required(self) -> bool:
        """Check if SSL is required based on configuration"""
        return bool(self.app.config.get('SSL_REQUIRED', False))

    def _bot_required(self) -> bool:
        """Check if Telegram bot is required based on configuration"""
        return bool(self.app.config.get('TELEGRAM_BOT_REQUIRED', False))

    async def run_flask_app(self):
        """Run Flask application with proper error handling"""
        try:
            # Initialize services first
            if not await self.initialize():
                raise RuntimeError("Failed to initialize services")
            
            self.logger.info("Starting Flask application")
            
            # Run Flask in a separate thread to not block the event loop
            loop = asyncio.get_event_loop()
            self._running = True
            await loop.run_in_executor(None, self._run_flask)
            
        except Exception as e:
            self.logger.error(f"Critical error in Flask application: {e}")
            self._running = False
            await self.cleanup()
            raise

    def _run_flask(self):
        """Run Flask in a separate thread"""
        try:
            self.app.run(
                host='0.0.0.0',
                port=3000,
                debug=False,
                use_reloader=False,
                threaded=True,
                processes=1
            )
        except Exception as e:
            self.logger.error(f"Flask server error: {e}")
            self._running = False

    async def cleanup(self) -> bool:
        """Cleanup using service registry for graceful shutdown"""
        try:
            self.logger.info("Starting application cleanup...")
            self._running = False
            
            # Use service registry to cleanup all services in reverse order
            await service_registry.cleanup_all_services()
            
            self.logger.info("Application cleanup completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Application cleanup failed: {str(e)}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Check application and services health status"""
        return {
            'status': 'healthy' if self._running else 'unhealthy',
            'running': self._running,
            'services': service_registry.get_service_health()
        }
