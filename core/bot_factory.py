import logging
import asyncio
from typing import Optional
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ConversationHandler
)
from services.logging_service import logging_service
from bot.handlers import (
    start, register, handle_full_name, handle_phone_number, 
    handle_location, handle_resume, handle_job_search,
    handle_application, cancel, unknown_command, error_handler
)

# Define conversation states
FULL_NAME, PHONE_NUMBER, LOCATION, RESUME = range(4)

class BotFactory:
    """Factory class for creating and managing Telegram bot instances"""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __init__(self):
        self.structured_logger = logging_service.get_structured_logger(__name__)
        self._application: Optional[Application] = None
        
    @classmethod
    async def get_instance(cls):
        """Get singleton instance of BotFactory"""
        async with cls._lock:
            if not cls._instance:
                cls._instance = BotFactory()
            return cls._instance
            
    def _create_conversation_handler(self) -> ConversationHandler:
        """Create and configure the conversation handler"""
        return ConversationHandler(
            entry_points=[CommandHandler('register', register)],
            states={
                FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_full_name)],
                PHONE_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone_number)],
                LOCATION: [MessageHandler(filters.LOCATION, handle_location)],
                RESUME: [MessageHandler(filters.DOCUMENT, handle_resume)]
            },
            fallbacks=[CommandHandler('cancel', cancel)]
        )
        
    def _setup_command_handlers(self, application: Application):
        """Set up command handlers for the bot"""
        application.add_handler(CommandHandler('start', start))
        application.add_handler(self._create_conversation_handler())
        application.add_handler(CommandHandler('search', handle_job_search))
        application.add_handler(CommandHandler('apply', handle_application))
        
        # Add handler for unknown commands
        application.add_handler(MessageHandler(
            filters.COMMAND & ~filters.Regex('^/(start|register|search|apply|cancel)$'),
            unknown_command
        ))
        
        # Add handler for non-command messages
        application.add_handler(MessageHandler(~filters.COMMAND, unknown_command))
        
        # Add error handler
        application.add_error_handler(error_handler)
        
    async def create_bot(self) -> Optional[Application]:
        """Create and initialize a new Telegram bot instance"""
        try:
            from os import getenv
            token = getenv('TELEGRAM_BOT_TOKEN')
            
            self.structured_logger.info("Attempting to create Telegram bot...")
            
            if not token:
                self.structured_logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
                return None
                
            if not isinstance(token, str) or not token.split(':')[0].isdigit():
                self.structured_logger.error("Invalid TELEGRAM_BOT_TOKEN format")
                return None
                
            # Create application
            application = Application.builder().token(token).build()
            
            # Setup handlers
            self._setup_command_handlers(application)
            
            self._application = application
            self.structured_logger.info("Telegram bot created successfully")
            return application
            
        except Exception as e:
            self.structured_logger.error(f"Failed to create Telegram bot: {e}")
            return None
            
    async def cleanup(self, cleanup_only: bool = False):
        """Clean up bot resources with optional full shutdown"""
        try:
            if not self._application:
                return
                
            self.structured_logger.info(
                f"{'Cleaning up' if cleanup_only else 'Stopping'} Telegram bot..."
            )
            
            await self._application.drop_pending_updates()
            
            if not cleanup_only:
                await self._application.stop()
                self._application = None
                
            self.structured_logger.info(
                f"Telegram bot {'cleanup' if cleanup_only else 'shutdown'} completed"
            )
            
        except Exception as e:
            self.structured_logger.error(
                f"Failed to {'cleanup' if cleanup_only else 'stop'} Telegram bot: {e}"
            )
            raise