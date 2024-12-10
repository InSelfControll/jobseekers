import asyncio
import logging
from hypercorn.config import Config
from hypercorn.asyncio import serve
from bot.telegram_bot import start_bot
from app import create_app, get_app_context

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Quart app
app = create_app()

async def run_web_and_bot():
    """Run both web application and Telegram bot"""
    try:
        # Configure Hypercorn
        config = Config()
        config.bind = ["0.0.0.0:5000"]
        
        # Start web application in its own context
        web_server = serve(app, config)
        
        # Start Telegram bot
        telegram_bot = start_bot()
        
        # Run both concurrently
        async with get_app_context():
            await asyncio.gather(web_server, telegram_bot)
            
    except Exception as e:
        logger.error(f"Error running application: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_web_and_bot())
