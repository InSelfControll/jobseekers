
import os
import logging
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
from bot.handlers import (
    start, register, handle_full_name, handle_phone_number, handle_location, 
    handle_resume, handle_job_search, handle_application, cancel
)

# Configure logging
logger = logging.getLogger(__name__)
FULL_NAME, PHONE_NUMBER, LOCATION, RESUME = range(4)

async def send_status_notification(telegram_id: str, job_title: str, status: str):
    """Send application status notification to user"""
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        return
        
    status_messages = {
        'accepted': f'🎉 Congratulations! Your application for "{job_title}" has been accepted!',
        'rejected': f'📝 Update on your application for "{job_title}": Unfortunately, the employer has decided not to proceed.',
        'pending': f'⏳ Your application for "{job_title}" is now under review.'
    }
    
    message = status_messages.get(status)
    if message:
        from telegram import Bot
        bot = Bot(token)
        await bot.send_message(chat_id=telegram_id, text=message)

_instance = None
_lock = asyncio.Lock()

async def start_bot():
    """Initialize and start the Telegram bot"""
    token = os.environ.get("TELEGRAM_TOKEN")
    global _instance
    
    if not token:
        logger.error("TELEGRAM_TOKEN not found in environment variables")
        return None

    try:
        if os.path.exists("bot.lock"):
            with open("bot.lock", "r") as f:
                pid = int(f.read().strip())
                if os.path.exists(f"/proc/{pid}"):
                    logger.info(f"Bot already running with PID {pid}")
                    return None
            os.remove("bot.lock")
        
        with open("bot.lock", "w") as f:
            f.write(str(os.getpid()))
        
        async with _lock:
            if _instance is None:
                application = ApplicationBuilder().token(token).build()
                
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
                application.add_handler(CommandHandler("start", start))
                application.add_handler(conv_handler)
                application.add_handler(CommandHandler("search", handle_job_search))
                application.add_handler(CommandHandler("apply", handle_application))
                
                async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
                    logger.error(f"Update {update} caused error {context.error}")
                    if update and update.message:
                        await update.message.reply_text(
                            "Sorry, something went wrong. Please try again later."
                        )
                
                application.add_error_handler(error_handler)
                _instance = application
                
        return _instance
                
    except Exception as e:
        logger.error(f"Error initializing bot: {e}")
        if os.path.exists("bot.lock"):
            os.remove("bot.lock")
        return None
