import asyncio
import logging
import os
import signal
import nest_asyncio
from telegram import Update
from telegram.ext import Application
from .telegram_bot import start_bot, stop_bot

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Enable nested event loops
nest_asyncio.apply()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signal.Signals(signum).name}")
    asyncio.create_task(shutdown())

async def shutdown():
    """Cleanup tasks tied to the service's shutdown."""
    logger.info("Starting graceful shutdown...")
    try:
        await stop_bot()
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("Shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

async def main():
    """Main entry point for the Telegram bot"""
    try:
        # Register signal handlers
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, signal_handler)
        
        # Start bot
        application = await start_bot()
        if not application:
            logger.error("Failed to start bot")
            return
            
        logger.info("Bot started successfully")
        await application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
            
    except Exception as e:
        logger.error(f"Error in main: {e}")
        await shutdown()
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        logger.info("Bot shutdown complete")
