
import logging
import os
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes
)
from bot.handlers import handle_job_search, handle_application, error_handler
from services.monitoring_service import bot_monitor

logger = logging.getLogger(__name__)
_instance = None
_lock = asyncio.Lock()

async def init_bot():
    """Initialize bot instance with proper error handling and monitoring"""
    try:
        token = os.environ.get('TELEGRAM_BOT_TOKEN')
        if not token:
            logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
            return None

        application = ApplicationBuilder().token(token).build()
        
        # Register command handlers
        application.add_handler(CommandHandler("search", handle_job_search))
        application.add_handler(CommandHandler("apply", handle_application))
        application.add_error_handler(error_handler)
        
        # Initialize bot monitor
        bot_monitor.set_status("initializing")
        
        return application
    except Exception as e:
        logger.error(f"Failed to initialize bot: {e}")
        bot_monitor.record_error(f"Bot initialization failed: {e}")
        return None

async def start_bot():
    """Start the bot with proper locking and monitoring"""
    try:
        global _instance
        async with _lock:
            if _instance:
                logger.info("Bot instance already exists")
                return _instance

            # Initialize new bot instance
            logger.info("Initializing new bot instance")
            _instance = await init_bot()
            
            if not _instance:
                bot_monitor.set_status("error")
                return None
            
            # Update monitor status
            bot_monitor.set_status("running")
            logger.info("Bot successfully started")
            return _instance

    except Exception as e:
        logger.error(f"Error in start_bot: {e}")
        bot_monitor.record_error(f"Bot startup failed: {e}")
        bot_monitor.set_status("error")
        return None

async def stop_bot():
    """Gracefully stop the bot"""
    try:
        global _instance
        async with _lock:
            if _instance:
                logger.info("Stopping bot")
                await _instance.stop()
                _instance = None
                bot_monitor.set_status("stopped")
                logger.info("Bot stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        bot_monitor.record_error(f"Bot shutdown failed: {e}")
