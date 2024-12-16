
import asyncio
import logging
import os
from app import create_app, db
from bot.telegram_bot import start_bot
from hypercorn.config import Config
from hypercorn.asyncio import serve

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.INFO)
logger = logging.getLogger(__name__)

async def run_web_server():
    """Run the Flask web server using Hypercorn"""
    app = create_app()
    config = Config()
    config.bind = ["0.0.0.0:5000"]
    return await serve(app, config)

async def run_telegram_bot():
    """Run the Telegram bot"""
    try:
        bot = await start_bot()
        if not bot:
            logger.error("Failed to initialize bot")
            return
    except Exception as e:
        logger.error(f"Telegram bot error: {e}")
        if os.path.exists("bot.lock"):
            os.remove("bot.lock")

async def main():
    """Main entry point for the application"""
    try:
        app = create_app()
        with app.app_context():
            db.create_all()
            logger.info("Database tables created successfully")
        
        await asyncio.gather(
            run_web_server(),
            run_telegram_bot()
        )
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise

if __name__ == '__main__':
    asyncio.run(main())
