# main.py
import asyncio
import threading
import logging.config
from core.application_manager import ApplicationManager

# Configure logging
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': True
        }
    }
})

logger = logging.getLogger(__name__)

async def amain():
    """Async main function"""
    manager = ApplicationManager()
    
    try:
        # Create Flask app first
        from app import create_app
        from bot.telegram_bot import start_bot
        
        manager.app = await create_app()
        if not manager.app:
            raise RuntimeError("Failed to create Flask application")

        # Initialize manager before running app
        if not await manager.initialize():
            raise RuntimeError("Failed to initialize services")
        
        # Start Telegram bot
        bot = await start_bot()
        if not bot:
            logger.warning("Failed to start Telegram bot - continuing without bot functionality")
        else:
            logger.info("Telegram bot started successfully")
            
        # Run Flask app in a separate thread
        flask_thread = threading.Thread(target=lambda: asyncio.run(manager.run_flask_app()))
        flask_thread.daemon = True
        flask_thread.start()
        
        # Keep the main thread running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        from bot.telegram_bot import stop_bot
        await stop_bot()
        await manager.cleanup()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        from bot.telegram_bot import stop_bot
        await stop_bot()
        await manager.cleanup()
        raise

def main():
    """Synchronous entry point"""
    try:
        asyncio.run(amain())
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        raise

if __name__ == '__main__':
    main()
