import asyncio
import logging
from hypercorn.config import Config
from hypercorn.asyncio import serve
from quart import Quart
from bot.telegram_bot import start_bot
from app import app as flask_app

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Quart app from Flask app
app = Quart(__name__)
app.config.from_mapping(flask_app.config)

# Copy routes and handlers from Flask app
for endpoint, view_function in flask_app.view_functions.items():
    app.view_functions[endpoint] = view_function

# Copy blueprints
for blueprint in flask_app.blueprints.values():
    app.register_blueprint(blueprint)

async def run_web_and_bot():
    """Run both web application and Telegram bot"""
    try:
        # Start Telegram bot
        bot_task = asyncio.create_task(start_bot())
        
        # Configure Hypercorn
        config = Config()
        config.bind = ["0.0.0.0:5000"]
        config.debug = True
        
        # Start web application
        web_task = asyncio.create_task(serve(app, config))
        
        # Run both tasks concurrently
        await asyncio.gather(bot_task, web_task)
    except Exception as e:
        logger.error(f"Error running application: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_web_and_bot())
