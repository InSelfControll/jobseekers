import logging
import functools
import traceback
from typing import Callable, Any, Optional
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime

logger = logging.getLogger(__name__)

def monitor_handler(func: Callable) -> Callable:
    """Decorator to monitor and log handler execution with detailed metrics"""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any):
        start_time = datetime.now()
        user_id = update.effective_user.id if update and update.effective_user else "Unknown"
        command = update.message.text if update and update.message else "Unknown"
        
        try:
            logger.info(f"Handler {func.__name__} called by user {user_id} with command: {command}")
            result = await func(update, context, *args, **kwargs)
            
            # Log execution metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Handler {func.__name__} completed successfully for user {user_id} "
                f"in {execution_time:.2f} seconds"
            )
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(
                f"Error in {func.__name__} for user {user_id} after {execution_time:.2f} seconds: "
                f"{str(e)}\n{traceback.format_exc()}"
            )
            raise
            
    return wrapper

def async_error_handler(func: Callable) -> Callable:
    """Enhanced decorator to handle errors in async handlers with user feedback"""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any):
        try:
            return await func(update, context, *args, **kwargs)
            
        except ValueError as ve:
            # Handle validation errors with specific message
            logger.warning(f"Validation error in {func.__name__}: {str(ve)}")
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    f"⚠️ {str(ve)}\nPlease try again with valid input."
                )
                
        except Exception as e:
            # Log detailed error information
            logger.error(
                f"Unhandled error in {func.__name__}: {str(e)}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            
            if update and update.effective_message:
                error_message = get_user_friendly_error_message(e)
                await update.effective_message.reply_text(error_message)
                
def get_user_friendly_error_message(error: Exception) -> str:
    """Convert technical errors to user-friendly messages"""
    if isinstance(error, ValueError):
        return "⚠️ Invalid input provided. Please check your input and try again."
    elif isinstance(error, FileNotFoundError):
        return "❌ Required file not found. Please try uploading again."
    elif isinstance(error, PermissionError):
        return "🔒 Permission denied. Please contact support if this persists."
    else:
        return "😔 Sorry, something went wrong. Please try again later."
