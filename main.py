
import asyncio
import logging
import os
import signal
from app import create_app, db
from bot.telegram_bot import start_bot
from hypercorn.config import Config
from hypercorn.asyncio import serve

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
    try:
        with app.app_context():
            db.create_all()
        
        tasks = [
            asyncio.create_task(run_web_server()),
            asyncio.create_task(run_telegram_bot())
        ]
        
        def cleanup():
            for task in tasks:
                task.cancel()
            
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda s, f: cleanup())
            
        await asyncio.gather(*tasks)
        
    except asyncio.CancelledError:
        logger.info("Application shutdown requested")
    except Exception as e:
        logger.error(f"Application error: {e}")
    finally:
        cleanup()

if __name__ == '__main__':
    asyncio.run(main())
