
import asyncio
import logging
from app import create_app, db
from bot.telegram_bot import start_bot
from hypercorn.config import Config
from hypercorn.asyncio import serve

logging.basicConfig(level=logging.INFO)
logging.getLogger('httpx').setLevel(logging.ERROR)
logging.getLogger('httpcore').setLevel(logging.ERROR) 
logging.getLogger('telegram').setLevel(logging.ERROR)
logging.getLogger('telegram.ext').setLevel(logging.ERROR)
logging.getLogger('bot.telegram_bot').setLevel(logging.INFO)
logger = logging.getLogger(__name__)

async def run_web_server():
    """Run the Flask web server using Hypercorn"""
    app = create_app()
    config = Config()
    config.bind = ["0.0.0.0:3000"]
    config.worker_class = "asyncio"
    return await serve(app, config)

async def main():
    """Main entry point for the application"""
    try:
        # Initialize Flask app and database
        app = create_app()
        with app.app_context():
            db.create_all()
            logger.info("Database initialized")
        
        # Start both web server and bot concurrently
        logger.info("Starting web server and bot...")
        await asyncio.gather(
            run_web_server(),
            start_bot()
        )
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise

if __name__ == '__main__':
    asyncio.run(main())
