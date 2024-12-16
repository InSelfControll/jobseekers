
import asyncio
import logging
from app import create_app, db
from bot.telegram_bot import start_bot
from hypercorn.config import Config
from hypercorn.asyncio import serve

logging.basicConfig(level=logging.WARNING)
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
    return await serve(app, config)

async def main():
    """Main entry point for the application"""
    try:
        # Initialize Flask app and database
        app = create_app()
        with app.app_context():
            db.create_all()
        
        # Start web server only - bot will be started separately
        await run_web_server()
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise

if __name__ == '__main__':
    asyncio.run(main())
