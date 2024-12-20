
import asyncio
import os
from app import create_app
from extensions import socketio, db
from bot.telegram_bot import start_bot
from hypercorn.config import Config
from hypercorn.asyncio import serve

async def run_web_server():
    app = create_app()
    config = Config()
    config.bind = ["0.0.0.0:3000"]
    config.use_reloader = True
    config.debug = True
    config.worker_class = "asyncio"
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Database initialization error: {e}")
    await serve(app, config)

async def run_telegram_bot():
    try:
        if os.path.exists("bot.lock"):
            os.remove("bot.lock")
        application = await start_bot()
        if application:
            await application.initialize()
            await application.start()
            await application.updater.start_polling()
    except Exception as e:
        print(f"Telegram bot error: {e}")
    finally:
        if os.path.exists("bot.lock"):
            os.remove("bot.lock")

async def main():
    tasks = [run_web_server(), run_telegram_bot()]
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("Shutting down gracefully...")
    except Exception as e:
        print(f"Error in main: {e}")
    finally:
        print("Application shutdown complete")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Received keyboard interrupt")
    except Exception as e:
        print(f"Fatal error: {e}")
