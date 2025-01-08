import os
import sys
import signal
import asyncio
from typing import Optional
from config import config
from core.service_manager import UnifiedServiceManager
from core.app_factory import create_app
from core.bot_factory import BotFactory
from services.logging_service import logging_service

logger = logging_service.get_structured_logger(__name__)

class Runner:
    def __init__(self):
        self.service_manager: Optional[UnifiedServiceManager] = None
        self.bot_factory: Optional[BotFactory] = None
        self.shutdown_event = asyncio.Event()
        self.app = None

    async def handle_shutdown(self, sig: signal.Signals):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received shutdown signal {sig.name}")
        self.shutdown_event.set()

        if self.service_manager:
            await self.service_manager.cleanup_all_services()

        if self.bot_factory:
            await self.bot_factory.cleanup()

        # Stop the event loop
        loop = asyncio.get_running_loop()
        loop.stop()

    async def setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown"""
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(self.handle_shutdown(s))
            )

    async def initialize_services(self):
        """Initialize all required services"""
        try:
            # Initialize service manager
            self.service_manager = UnifiedServiceManager()
            if not await self.service_manager.initialize_all_services():
                logger.error("Failed to initialize services")
                return False

            # Create Flask app
            self.app = create_app()
            if not self.app:
                logger.error("Failed to create Flask app")
                return False

            # Initialize bot
            self.bot_factory = await BotFactory.get_instance()
            bot_app = await self.bot_factory.create_bot()
            if not bot_app:
                logger.error("Failed to create Telegram bot")
                return False

            return True

        except Exception as e:
            logger.error(f"Service initialization failed: {e}")
            return False

    async def run_services(self):
        """Run all services concurrently"""
        try:
            # Start Flask app in a separate thread
            flask_task = asyncio.create_task(
                asyncio.to_thread(
                    self.app.run,
                    host='0.0.0.0',
                    port=int(os.getenv('PORT', 3000)),
                    debug=False,
                    use_reloader=False
                )
            )

            # Start bot polling
            bot_task = asyncio.create_task(
                self.bot_factory._application.run_polling(
                    drop_pending_updates=True,
                    close_loop=False
                )
            )

            # Wait for shutdown signal
            await self.shutdown_event.wait()

            # Cancel running tasks
            flask_task.cancel()
            bot_task.cancel()

            try:
                await asyncio.gather(flask_task, bot_task, return_exceptions=True)
            except asyncio.CancelledError:
                pass

        except Exception as e:
            logger.error(f"Error running services: {e}")
            raise

async def main():
    """Main entry point"""
    try:
        # Set up environment
        env = os.getenv('FLASK_ENV', 'development')
        os.environ['FLASK_APP'] = 'runner.py'
        
        # Initialize configuration
        app_config = config[env]
        
        # Create runner instance
        runner = Runner()
        
        # Set up signal handlers
        await runner.setup_signal_handlers()
        
        # Initialize and start services
        if await runner.initialize_services():
            await runner.run_services()
        else:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        sys.exit(1)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application crashed: {e}")
        sys.exit(1)