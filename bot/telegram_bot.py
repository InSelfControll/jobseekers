
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
from services.monitoring_service import bot_monitor

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Global variables
_instance = None
_lock = asyncio.Lock()

async def init_bot():
    """Initialize bot instance with proper error handling and monitoring"""
    try:
        logger.info("Starting bot initialization...")
        
        # Check for token
        token = os.environ.get('TELEGRAM_BOT_TOKEN')
        if not token:
            logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
            return None

        # Build application
        logger.info("Building Telegram application...")
        application = ApplicationBuilder().token(token).build()
        
        # Import handlers here to avoid circular imports
        logger.info("Importing handlers...")
        from .handlers import (
            start, register, handle_full_name, handle_phone_number,
            handle_location, handle_resume, handle_job_search,
            handle_application, cancel, error_handler,
            FULL_NAME, PHONE_NUMBER, LOCATION, RESUME
        )
        
        try:
            logger.info("Registering command handlers...")
            # Register conversation handlers
            conv_handler = ConversationHandler(
                entry_points=[CommandHandler("register", register)],
                states={
                    FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_full_name)],
                    PHONE_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone_number)],
                    LOCATION: [MessageHandler(filters.LOCATION, handle_location)],
                    RESUME: [MessageHandler(filters.Document.PDF, handle_resume)]
                },
                fallbacks=[CommandHandler("cancel", cancel)]
            )
            
            # Register all command handlers with proper order
            application.add_handler(CommandHandler("start", start))
            application.add_handler(conv_handler)
            application.add_handler(CommandHandler("search", handle_job_search))
            application.add_handler(CommandHandler("apply", handle_application))
            application.add_error_handler(error_handler)
            
            logger.info("All bot handlers registered successfully")
            
            # Initialize bot monitor
            bot_monitor.set_status("initializing")
            logger.info("Bot monitor initialized")
            
            return application
            
        except Exception as e:
            logger.error(f"Error registering handlers: {e}")
            bot_monitor.set_status("error")
            bot_monitor.record_error(f"Handler registration failed: {e}")
            return None
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
