
import asyncio
import logging
from app import create_app
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
        try:
            await application.initialize()
            await application.start()
            await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
            await application.updater.wait_closed()
        finally:
            await application.stop()
            await application.shutdown()

def main():
    """Main entry point for the application"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        logger.info("Starting application...")
        loop.create_task(run_web_server())
        loop.create_task(run_telegram_bot())
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise
    finally:
        loop.close()

if __name__ == '__main__':
    main()
