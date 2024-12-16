
import logging
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes
)
from bot.handlers import handle_job_search, handle_application

logger = logging.getLogger(__name__)
_instance = None

async def start_bot():
    try:
        global _instance
        if _instance:
            return _instance
            
        if not os.environ.get('TELEGRAM_BOT_TOKEN'):
            logger.error("No bot token provided")
            return None
            
        token = os.environ['TELEGRAM_BOT_TOKEN']
        
        if os.path.exists("bot.lock"):
            logger.warning("Bot is already running")
            return None
            
        with open("bot.lock", "w") as f:
            f.write("1")
            
        application = ApplicationBuilder().token(token).build()
        
        application.add_handler(CommandHandler("search", handle_job_search))
        application.add_handler(CommandHandler("apply", handle_application))
        
        from bot.handlers import error_handler
        application.add_error_handler(error_handler)
        _instance = application
        
        return _instance
                
    except Exception as e:
        logger.error(f"Error initializing bot: {e}")
        if os.path.exists("bot.lock"):
            os.remove("bot.lock")
        return None
