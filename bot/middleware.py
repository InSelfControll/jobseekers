import time
import logging
import functools
import asyncio
from datetime import datetime
from services.monitoring_service import bot_monitor
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

def monitor_handler(func):
    """Decorator to monitor handler execution time and errors"""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        start_time = time.time()
        try:
            # Record incoming message
            bot_monitor.message_count += 1
            bot_monitor.last_message_time = datetime.now()
            
            # Execute handler
            result = await func(update, context, *args, **kwargs)
            
            # Record execution time
            execution_time = time.time() - start_time
            bot_monitor.record_message(execution_time)
            
            # Log success
            logger.debug(f"Handler {func.__name__} completed in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            # Record error and execution time
            execution_time = time.time() - start_time
            error_msg = f"Error in {func.__name__}: {str(e)}"
            logger.error(error_msg)
            bot_monitor.record_error(error_msg)
            
            # Try to send error message to user
            try:
                error_text = "Sorry, an error occurred processing your request. Please try again later."
                await update.message.reply_text(error_text)
            except Exception as reply_error:
                logger.error(f"Failed to send error message: {reply_error}")
                
            raise
    return wrapper

def async_error_handler(func):
    """Decorator to handle async errors in bot handlers"""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            return await func(update, context, *args, **kwargs)
        except asyncio.CancelledError:
            logger.warning(f"Handler {func.__name__} was cancelled")
            bot_monitor.record_error(f"Handler {func.__name__} cancelled")
            raise
        except Exception as e:
            logger.exception(f"Unhandled error in {func.__name__}")
            bot_monitor.record_error(f"Unhandled error in {func.__name__}: {str(e)}")
            raise
    return wrapper