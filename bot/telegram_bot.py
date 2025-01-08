import os
import asyncio
import logging
from telegram.ext import Application

logger = logging.getLogger(__name__)
_instance = None
_lock = asyncio.Lock()
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

async def create_application():
    """Create and configure the bot application"""
    if not TOKEN:
        logger.error("No telegram bot token provided")
        return None
        
    try:
        # Import handlers at the start to avoid circular imports
        from telegram.ext import (
            CommandHandler,
            MessageHandler, 
            ConversationHandler,
            CallbackContext,
            filters
        )
        from telegram.ext.filters import TEXT, COMMAND
        from .handlers import (
            start,
            register,
            handle_full_name,
            handle_phone_number,
            handle_location,
            handle_resume,
            handle_job_search,
            handle_application,
            cancel,
            unknown_command,
            error_handler,
            FULL_NAME, 
            PHONE_NUMBER, 
            LOCATION, 
            RESUME
        )

        application = Application.builder().token(TOKEN).build()

        # Set up conversation handler for registration
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('register', register)],
            states={
                FULL_NAME: [MessageHandler(TEXT & ~COMMAND, handle_full_name)],
                PHONE_NUMBER: [MessageHandler(TEXT & ~COMMAND, handle_phone_number)],
                LOCATION: [MessageHandler(filters.LOCATION, handle_location)],
                RESUME: [MessageHandler(filters.Document.ALL, handle_resume)]
            },
            fallbacks=[CommandHandler('cancel', cancel)]
        )

        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(conv_handler)
        application.add_handler(CommandHandler("search", handle_job_search))
        application.add_handler(CommandHandler("apply", handle_application))
        # Add error handler
        application.add_error_handler(error_handler)
        # Add unknown command handler last
        application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
        
        logger.info("Telegram bot application created successfully")
        return application
        
    except Exception as e:
        logger.error(f"Failed to create bot application: {e}")
        return None


async def start_bot():
    """Start the Telegram bot.

    Returns:
        The bot instance if successfully started, None otherwise.
    """
    try:
        global _instance
        async with _lock:
            if _instance:
                logger.info("Bot instance already exists")
                return _instance

            logger.info("Starting Telegram bot...")
            if not TOKEN:
                logger.error("No telegram bot token provided")
                return None

            _instance = await create_application()
            if _instance:
                await _instance.initialize()
                await _instance.start()
                # Start polling for updates
                await _instance.updater.start_polling()
                logger.info("Telegram bot started successfully and polling for updates")
                return _instance
            else:
                logger.error("Failed to create bot application")
                return None

    except Exception as e:
        logger.error(f"Failed to start Telegram bot: {e}")
        return None

async def stop_bot(cleanup_only: bool = False):
    """Stop the Telegram bot gracefully with optional cleanup.

    Args:
        cleanup_only (bool, optional): If True, only perform resource cleanup
            without full shutdown. Defaults to False.
    """
    try:
        global _instance
        async with _lock:
            if not _instance:
                logger.info("No active bot instance to stop")
                return

            logger.info(f"{'Cleaning up' if cleanup_only else 'Stopping'} Telegram bot...")

            try:
                if not cleanup_only:
                    # Full shutdown - stop polling first
                    if hasattr(_instance, 'updater') and _instance.updater:
                        await _instance.updater.stop()
                    # Then stop the application
                    await _instance.shutdown()
                    _instance = None
                    logger.info("Telegram bot stopped successfully")
                else:
                    # Just cleanup resources
                    if hasattr(_instance, 'updater') and _instance.updater:
                        await _instance.updater.drop_pending_updates()
                    logger.info("Resource cleanup completed successfully")

            except Exception as inner_e:
                logger.error(f"Error during {'cleanup' if cleanup_only else 'shutdown'}: {inner_e}")
                # Don't re-raise, allow graceful degradation

    except Exception as e:
        logger.error(f"Failed to {'cleanup' if cleanup_only else 'stop'} Telegram bot: {e}")
        raise
