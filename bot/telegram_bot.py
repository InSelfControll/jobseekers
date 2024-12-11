import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes
)
from bot.handlers import (
    start, register, handle_full_name, handle_location, handle_resume,
    handle_job_search, handle_application, cancel
)

# Configure logging
logger = logging.getLogger(__name__)
FULL_NAME, LOCATION, RESUME = range(3)

async def start_bot():
    """Initialize and start the Telegram bot"""
    try:
        # Verify token exists
        token = os.environ.get("TELEGRAM_TOKEN")
        if not token:
            logger.error("TELEGRAM_TOKEN not found in environment variables")
            return
        
        # Create application
        application = ApplicationBuilder().token(token).build()
        
        # Add conversation handler for registration
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("register", register)],
            states={
                FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_full_name)],
                LOCATION: [MessageHandler(filters.LOCATION, handle_location)],
                RESUME: [MessageHandler(filters.Document.PDF, handle_resume)],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        )
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(conv_handler)
        application.add_handler(CommandHandler("search", handle_job_search))
        application.add_handler(CommandHandler("apply", handle_application))
        
        # Initialize and start the bot
        await application.initialize()
        await application.start()
        
        # Start polling
        await application.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"Error in Telegram bot: {e}")
        raise
    
    return application
