
import asyncio
import logging
from app import create_app
from bot.telegram_bot import start_bot
from hypercorn.config import Config
from hypercorn.asyncio import serve

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
        try:
            await application.run_polling(allowed_updates=Update.ALL_TYPES)
        finally:
            await application.stop()

async def main():
    """Main entry point for the application"""
    try:
        logger.info("Starting application...")
        await asyncio.gather(
            run_web_server(),
            run_telegram_bot()
        )
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise

if __name__ == '__main__':
    asyncio.run(main())
