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

# Configure logging
logger = logging.getLogger(__name__)
FULL_NAME, PHONE_NUMBER, LOCATION, RESUME = range(4)


async def send_status_notification(telegram_id: str, job_title: str,
                                   status: str):
    """Send application status notification to user"""
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        return

    status_messages = {
        'accepted':
        f'🎉 Congratulations! Your application for "{job_title}" has been accepted!',
        'rejected':
        f'📝 Update on your application for "{job_title}": Unfortunately, the employer has decided not to proceed.',
        'pending': f'⏳ Your application for "{job_title}" is now under review.'
    }

    message = status_messages.get(status)
    if message:
        bot = Bot(token)
        await bot.send_message(chat_id=telegram_id, text=message)


_instance = None
_lock = asyncio.Lock()


async def start_bot():
    """Initialize and start the Telegram bot"""
    token = os.environ.get("TELEGRAM_TOKEN")
    global _instance
    lock_file = None
    logger.info("Starting Telegram bot initialization")

    if not token:
        logger.error("TELEGRAM_TOKEN not found in environment variables")
        return None

    try:
        import tempfile
        import atexit
        import psutil

        lock_file = os.path.join(tempfile.gettempdir(), "telegram_bot.lock")
        logger.debug(f"Using lock file: {lock_file}")

        def cleanup_lock():
            try:
                if lock_file and os.path.exists(lock_file):
                    os.remove(lock_file)
                    logger.info("Cleaned up bot lock file")
            except Exception as e:
                logger.error(f"Error cleaning up lock file: {e}")

        # Register cleanup function
        atexit.register(cleanup_lock)

        # Check for existing bot process
        if os.path.exists(lock_file):
            try:
                with open(lock_file, "r") as f:
                    pid = int(f.read().strip())
                    if psutil.pid_exists(pid):
                        proc = psutil.Process(pid)
                        if proc.name().startswith('python'):
                            logger.info(f"Bot already running with PID {pid}")
                            return None
            except Exception as e:
                logger.warning(f"Error checking existing bot process: {e}")

            try:
                os.remove(lock_file)
                logger.info("Removed stale lock file")
            except Exception as e:
                logger.error(f"Error removing stale lock file: {e}")
                return None

        # Create new lock file
        try:
            with open(lock_file, "w") as f:
                f.write(str(os.getpid()))
            logger.info(f"Created lock file with PID {os.getpid()}")
        except Exception as e:
            logger.error(f"Error creating lock file: {e}")
            return None

        if _instance is None:
            application = ApplicationBuilder().token(token).build()

            # Add conversation handler for registration
            conv_handler = ConversationHandler(
                entry_points=[CommandHandler("register", register)],
                states={
                    FULL_NAME: [
                        MessageHandler(filters.TEXT & ~filters.COMMAND,
                                       handle_full_name)
                    ],
                    PHONE_NUMBER: [
                        MessageHandler(filters.TEXT & ~filters.COMMAND,
                                       handle_phone_number)
                    ],
                    LOCATION:
                    [MessageHandler(filters.LOCATION, handle_location)],
                    RESUME:
                    [MessageHandler(filters.Document.PDF, handle_resume)],
                },
                fallbacks=[CommandHandler("cancel", cancel)])

            # Add handlers
            application.add_handler(CommandHandler("start", start))
            application.add_handler(conv_handler)
            application.add_handler(CommandHandler("search", handle_job_search))
            application.add_handler(CommandHandler("apply", handle_application))

            # Add error handler before starting polling
            application.add_error_handler(error_handler)

            async def error_handler(update: Update,
                                    context: ContextTypes.DEFAULT_TYPE):
                error = context.error
                logger.error(f"Update {update} caused error: {error}",
                             exc_info=context.error)

                if isinstance(error, Exception):
                    error_message = "An unexpected error occurred. Please try again later."
                    if update and update.message:
                        try:
                            await update.message.reply_text(error_message)
                        except Exception as e:
                            logger.error(f"Failed to send error message: {e}")

                # Prevent the error from propagating
                return True

            application.add_error_handler(error_handler)
            _instance = application
            # Initialize bot monitoring
            bot_monitor.set_status("running")
            # Add message handler wrapper
            original_process_update = _instance.process_update

            async def monitored_process_update(update: Update,
                                               context: CallbackContext):
                start_time = time.time()
                try:
                    result = await original_process_update(update, context)
                    execution_time = time.time() - start_time
                    bot_monitor.record_message(execution_time)
                    return result
                except Exception as e:
                    bot_monitor.record_error(str(e))
                    raise

            _instance.process_update = monitored_process_update
            
            # Initialize and start polling
            await _instance.initialize()
            await _instance.start()
            await _instance.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            logger.info("Bot successfully started and polling for updates")
            # Keep the polling running
            try:
                while True:
                    await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error in polling: {e}")
                raise

        return _instance

    except Exception as e:
        logger.error(f"Error initializing bot: {e}")
        if os.path.exists(lock_file):
            os.remove(lock_file)
        return None
