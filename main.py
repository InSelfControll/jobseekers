import asyncio
import logging
import os
import signal
from app import create_app, db  # Added db import
from bot.telegram_bot import start_bot
from hypercorn.config import Config


def install_missing_modules():
    """Install any missing Python modules using poetry"""
    import os
    
    required_modules = [
        "flask", "flask-login", "flask-sqlalchemy", "openai", "sqlalchemy",
        "flask-wtf", "psycopg2-binary", "email-validator", "geopy",
        "nest-asyncio", "quart", "hypercorn", "asyncpg", "aiohttp",
        "sqlalchemy-utils", "python-telegram-bot==20.7", "python3-saml",
        "requests-oauthlib"
    ]

    for module in required_modules:
        try:
            __import__(module.replace('-', '_').split('==')[0])
        except ImportError:
            os.system(f"poetry add {module}")
            logger.info(f"Installed {module}")


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
    try:
        application = await start_bot()
        if application:
            await application.initialize()
            await application.start()
            await application.updater.start_polling(drop_pending_updates=True, allowed_updates=['message'])
            await application.updater.stop()
            
            while True:
                await asyncio.sleep(1)
                
    except asyncio.CancelledError:
        logger.info("Telegram bot gracefully shutting down.")
    except Exception as e:
        logger.error(f"Telegram bot error: {e}")
    finally:
        if 'application' in locals() and application:
            await application.stop()
            await application.shutdown()


async def main():
    """Main entry point for the application"""
    try:
        install_missing_modules()
        with app.app_context():
            db.drop_all()  # This will delete all data - make sure this is okay
            db.create_all()
            logger.info("Database tables recreated successfully")

        logger.info("Starting application...")
        telegram_task = asyncio.create_task(run_telegram_bot())
        web_task = asyncio.create_task(run_web_server())

        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}. Shutting down gracefully.")
            telegram_task.cancel()
            web_task.cancel()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


        await asyncio.gather(telegram_task, web_task)
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise


if __name__ == '__main__':
    asyncio.run(main())