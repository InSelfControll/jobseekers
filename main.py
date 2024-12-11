import asyncio
import logging
from hypercorn.config import Config
from hypercorn.asyncio import serve
from bot.telegram_bot import start_bot
from app import create_app

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
        
        # Create tasks
        web_server = serve(app, config)
        telegram_bot = None
        
        async with app.app_context():
            # Start bot only after app context is established
            telegram_bot = asyncio.create_task(start_bot())
            
            # Run both concurrently
            await asyncio.gather(web_server, telegram_bot)
            
    except Exception as e:
        logger.error(f"Error running application: {e}")
        if telegram_bot:
            telegram_bot.cancel()
        raise

if __name__ == "__main__":
    asyncio.run(run_web_and_bot())
