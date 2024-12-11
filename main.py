import asyncio
import logging
import signal
from quart import Quart
from bot.telegram_bot import start_bot
from app import create_app

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Quart app from Flask app
flask_app = create_app()
app = Quart(__name__)

# Copy Flask app configurations to Quart app
app.config.update(**flask_app.config)

# Register Flask blueprints with Quart
for name, blueprint in flask_app.blueprints.items():
    app.register_blueprint(blueprint)

@app.route('/')
async def index():
    return 'Job Application Platform - Please <a href="/login">login</a> to continue'

async def shutdown(signal, loop):
    """Cleanup tasks tied to the service's shutdown."""
    logger.info(f"Received exit signal {signal.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    logger.info(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

def handle_exception(loop, context):
    msg = context.get("exception", context["message"])
    logger.error(f"Caught exception: {msg}")
    logger.info("Shutting down...")
    asyncio.create_task(shutdown(signal.SIGTERM, loop))

async def main():
    # Get or create event loop
    loop = asyncio.get_event_loop()
    
    # Handle exceptions
    loop.set_exception_handler(handle_exception)
    
    # Start the bot
    bot_task = asyncio.create_task(start_bot())
    
    # Start Quart app
    server = await app.run_task(
        host='0.0.0.0',
        port=5000,
        debug=False  # Set to False to avoid duplicate bot instances
    )
    
    try:
        await asyncio.gather(bot_task, server)
    except asyncio.CancelledError:
        logger.info("Tasks cancelled")
    finally:
        await shutdown(signal.SIGTERM, loop)

if __name__ == '__main__':
    asyncio.run(main())
