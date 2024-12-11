import os
import logging
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
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
        # Create application
        application = Application.builder().token(os.environ.get("TELEGRAM_TOKEN")).build()

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

        # Start the bot
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        # Keep the bot running until interrupted
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            await application.stop()
            
    except Exception as e:
        logger.error(f"Error in Telegram bot: {e}")
        raise
