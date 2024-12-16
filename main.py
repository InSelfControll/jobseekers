import asyncio
import logging
import os
import signal
from app import create_app, db  # Added db import
from bot.telegram_bot import start_bot
from hypercorn.config import Config
from hypercorn.asyncio import serve
from telegram import Update
from telegram.ext import Updater


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


# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = create_app()


async def run_web_server():
    """Run the web server"""
    config = Config()
    config.bind = ["0.0.0.0:443", "0.0.0.0:80"]
    config.use_reloader = False

    # Query all employers with SSL enabled
    with app.app_context():
        from models import Employer
        ssl_employers = Employer.query.filter_by(ssl_enabled=True).all()

        if ssl_employers:
            certs = []
            for employer in ssl_employers:
                if employer.ssl_cert_path and employer.ssl_key_path and os.path.exists(
                        employer.ssl_cert_path) and os.path.exists(
                            employer.ssl_key_path):
                    certs.append({
                        'cert': employer.ssl_cert_path,
                        'key': employer.ssl_key_path,
                        'domains': [employer.sso_domain]
                    })
                    logging.info(
                        f"Using SSL for domain: {employer.sso_domain}")

            if certs:
                # Configure the primary certificate
                config.certfile = certs[0]['cert']
                config.keyfile = certs[0]['key']
                # Add all certificates to the additional certs list
                #config.additional_certs = [(cert['cert'], cert['key']) for cert in certs]
                ssl_employers = Employer.query.filter_by(
                    ssl_enabled=True).all()
                logging.info("Configured SSL certificates")
                # config.additional_certs = [(cert['cert'], cert['key'])  # This line is incorrect due to the error

    await serve(app, config)


async def run_telegram_bot():
    """Run the Telegram bot"""
    try:
        application = await start_bot()
        if application:  # Check if application is not None
            await application.initialize()
            await application.start()
            await application.updater.start_polling(
                allowed_updates=[Update.MESSAGE])
            #await application.updater.start_polling(
            #    drop_pending_updates=True,
            #    allowed_updates=[Update.MESSAGE],
            #    read_timeout=30,
            #    write_timeout=30)

            try:
                while True:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                logger.info("Telegram bot gracefully shutting down")
                await application.updater.stop()
                await application.stop()
                await application.shutdown()

    except Exception as e:
        logger.error(f"Telegram bot error: {e}")
    finally:
        if os.path.exists("bot.lock"):
            os.remove("bot.lock")


async def main():
    """Main entry point for the application"""
    try:
        install_missing_modules()
        with app.app_context():
            db.drop_all()  # This will delete all data - make sure this is okay
            db.create_all()
            logger.info("Database tables recreated successfully")

        logger.info("Starting application...")
        # Start web server first
        web_task = asyncio.create_task(run_web_server())
        # Wait a moment before starting bot
        await asyncio.sleep(2)
        telegram_task = asyncio.create_task(run_telegram_bot())

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
