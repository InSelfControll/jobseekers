"""
Bot package initialization.
This file makes the bot directory a Python package.
"""

# Export the main bot functions and decorators
from .telegram_bot import start_bot, stop_bot
from .decorators import monitor_handler, async_error_handler

__all__ = ['start_bot', 'stop_bot', 'monitor_handler', 'async_error_handler']
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import logging
import os

# Configure logging
logger = logging.getLogger(__name__)

# Get bot token from environment
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

async def error_handler(update, context):
    """Log Errors caused by Updates."""
    logger.error(f'Update "{update}" caused error "{context.error}"')

def create_application():
    """Create and configure the bot application"""
    if not TOKEN:
        logger.error("No telegram bot token provided")
        return None
        
    try:
        application = Application.builder().token(TOKEN).build()
        
        # Add error handler
        application.add_error_handler(error_handler)
        
        # Import and add command handlers
        from .handlers.start import start_handler
        from .handlers.help import help_handler
        from .handlers.jobs import jobs_handler
        
        application.add_handler(start_handler)
        application.add_handler(help_handler)
        application.add_handler(jobs_handler)
        
        logger.info("Telegram bot application created successfully")
        return application
        
    except Exception as e:
        logger.error(f"Failed to create bot application: {e}")
        return None
