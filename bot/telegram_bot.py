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
        
        # Create application with better error handling
        application = (
            ApplicationBuilder()
            .token(token)
            .read_timeout(30)
            .write_timeout(30)
            .pool_timeout(30)
            .connect_timeout(30)
            .build()
        )
        
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
        
        # Error handler
        async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            logger.error(f"Update {update} caused error {context.error}")
            if update and update.message:
                await update.message.reply_text(
                    "Sorry, something went wrong. Please try again later."
                )
        
        application.add_error_handler(error_handler)
        
        # Initialize the application
        await application.initialize()
        
        # Start the bot with proper shutdown handling
        await application.start()
        await application.run_polling(drop_pending_updates=True)
        
        logger.info("Telegram bot started successfully")
        
        # Keep the bot running
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Error in Telegram bot: {e}")
        raise
    finally:
        # Ensure proper cleanup
        await application.stop()
