import asyncio
import logging
from app import create_app, db # Added db import
from bot.telegram_bot import start_bot
from hypercorn.config import Config
from hypercorn.asyncio import serve
from telegram import Update

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
    application = await start_bot()
    if application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
async def main():
    """Main entry point for the application"""
    try:
        with app.app_context():
            db.drop_all()  # This will delete all data - make sure this is okay
            db.create_all()
            logger.info("Database tables recreated successfully")

        logger.info("Starting application...")
        telegram_task = asyncio.create_task(run_telegram_bot())
        web_task = asyncio.create_task(run_web_server())
        await asyncio.gather(telegram_task, web_task)
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise

if __name__ == '__main__':
    asyncio.run(main())