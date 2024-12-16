import time
import logging
import functools
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
            result = await func(update, context, *args, **kwargs)
            execution_time = time.time() - start_time
            bot_monitor.record_message(execution_time)
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Error in {func.__name__}: {str(e)}"
            logger.error(error_msg)
            bot_monitor.record_error(error_msg)
            raise
    return wrapper
