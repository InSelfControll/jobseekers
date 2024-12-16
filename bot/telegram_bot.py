
import os
import logging
import asyncio
import time
from telegram import Update, Bot
from telegram.ext import (Application, CommandHandler, MessageHandler,
                        ConversationHandler, CallbackContext,
                        ApplicationBuilder, ContextTypes, filters)
from bot.handlers import (start, register, handle_full_name,
                        handle_phone_number, handle_location, handle_resume,
                        handle_job_search, handle_application, cancel)
from services.monitoring_service import bot_monitor

logger = logging.getLogger(__name__)
FULL_NAME, PHONE_NUMBER, LOCATION, RESUME = range(4)

async def send_status_notification(telegram_id: str, job_title: str, status: str):
    """Send application status notification to user"""
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        logger.error("TELEGRAM_TOKEN not found")
        return

    status_messages = {
        'accepted': f'🎉 Congratulations! Your application for "{job_title}" has been accepted!',
        'rejected': f'📝 Update on your application for "{job_title}": Unfortunately, the employer has decided not to proceed.',
        'pending': f'⏳ Your application for "{job_title}" is now under review.'
    }

    message = status_messages.get(status)
    if message:
        try:
            bot = Bot(token)
            await bot.send_message(chat_id=telegram_id, text=message)
        except Exception as e:
            logger.error(f"Error sending notification: {e}")

_instance = None

async def start_bot():
    """Initialize and start the Telegram bot"""
    global _instance
    token = os.environ.get("TELEGRAM_TOKEN")
    
    if not token:
        logger.error("TELEGRAM_TOKEN not found in environment variables")
        return None

    try:
        if _instance is None:
            builder = ApplicationBuilder().token(token)
            builder.read_timeout(30)
            builder.write_timeout(30)
            builder.connect_timeout(30)
            builder.pool_timeout(30)
            
            application = builder.build()
            
            # Add conversation handler for registration
            conv_handler = ConversationHandler(
                entry_points=[CommandHandler("register", register)],
                states={
                    FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_full_name)],
                    PHONE_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone_number)],
                    LOCATION: [MessageHandler(filters.LOCATION, handle_location)],
                    RESUME: [MessageHandler(filters.Document.PDF, handle_resume)],
                },
                fallbacks=[CommandHandler("cancel", cancel)]
            )

            # Add handlers
            application.add_handler(conv_handler)
            application.add_handler(CommandHandler("start", start))
            application.add_handler(CommandHandler("search", handle_job_search))
            application.add_handler(CommandHandler("apply", handle_application))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
            
            # Error handler
            async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
                logger.error(f"Exception while handling an update: {context.error}")
                if update and isinstance(update, Update) and update.effective_message:
                    await update.effective_message.reply_text(
                        "Sorry, an error occurred while processing your request."
                    )
            
            application.add_error_handler(error_handler)
            _instance = application
            
            # Initialize monitoring
            bot_monitor.set_status("running")
            
            # Start the bot
            await application.initialize()
            await application.start()
            
            # Start polling in non-blocking mode
            await application.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                close_loop=False
            )
            
            logger.info("Telegram bot successfully started")
            
            # Keep the bot running
            while True:
                await asyncio.sleep(1)
                
    except Exception as e:
        logger.error(f"Error initializing bot: {e}")
        return None

    return _instance
