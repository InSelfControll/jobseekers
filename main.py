
import asyncio
import logging
import os
import signal
from app import create_app, db
from bot.telegram_bot import start_bot
from hypercorn.config import Config
from hypercorn.asyncio import serve

from bot.telegram_bot import logger

app = create_app()

async def run_web_server():
    config = Config()
    config.bind = ["0.0.0.0:3000"]
    config.use_reloader = False
    await serve(app, config)

async def run_telegram_bot():
    try:
        if os.path.exists("bot.lock"):
            os.remove("bot.lock")
            
        application = await start_bot()
        if application:
            await application.initialize()
            await application.start()
            await application.updater.start_polling(
                drop_pending_updates=True,
                allowed_updates=["message"],
                read_timeout=30,
                write_timeout=30
            )
            while True:
                await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"Telegram bot error: {e}")
    finally:
        if os.path.exists("bot.lock"):
            os.remove("bot.lock")

async def main():
    with app.app_context():
        db.create_all()
    
    tasks = [run_web_server(), run_telegram_bot()]
    
    try:
        await asyncio.gather(*tasks)
    except (asyncio.CancelledError, KeyboardInterrupt):
        logger.info("Application shutdown requested")
    except Exception as e:
        logger.error(f"Application error: {e}")

if __name__ == '__main__':
    asyncio.run(main())
