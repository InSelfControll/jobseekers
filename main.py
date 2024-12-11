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
    try:
        logger.info("Starting application...")
        
        # Create tasks for both services
        web_server_task = asyncio.create_task(run_web_server())
        telegram_bot_task = asyncio.create_task(run_telegram_bot())
        
        # Wait for both tasks to complete
        await asyncio.gather(
            web_server_task,
            telegram_bot_task,
            return_exceptions=True
        )
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise
    finally:
        logger.info("Application shutdown complete")

if __name__ == '__main__':
    try:
        # Set up asyncio policy for better Windows compatibility
        if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        # Run the main async function
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
