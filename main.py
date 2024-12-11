
import asyncio
import logging
import nest_asyncio
from app import create_app
from bot.telegram_bot import start_bot
from hypercorn.config import Config
from hypercorn.asyncio import serve

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Enable nested event loops
nest_asyncio.apply()

# Create Flask app
app = create_app()

async def run_web_server():
    """Run the web server"""
    config = Config()
    config.bind = ["0.0.0.0:5000"]
    config.use_reloader = False
    await serve(app, config)

async def run_telegram_bot():
    """Run the Telegram bot"""
    await start_bot()

async def main():
    """Main entry point for the application"""
    tasks = []
    try:
        logger.info("Starting application...")
        
        # Create tasks for both services
        web_server_task = asyncio.create_task(run_web_server())
        telegram_bot_task = asyncio.create_task(run_telegram_bot())
        tasks = [web_server_task, telegram_bot_task]
        
        # Wait for both tasks to complete or interrupt
        await asyncio.gather(*tasks, return_exceptions=True)
        
    except Exception as e:
        logger.error(f"Application error: {e}")
    finally:
        logger.info("Shutting down...")
        for task in tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        logger.info("Application shutdown complete")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
