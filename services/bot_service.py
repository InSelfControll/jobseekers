import logging
import asyncio
from typing import Optional, Any
from core.bot_factory import BotFactory
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from services.base import BaseServiceManager
from services.logging_service import logging_service
from bot.handlers import (
    start, register, handle_full_name, handle_phone_number, 
    handle_location, handle_resume, handle_job_search,
    handle_application, cancel, unknown_command, error_handler
)

# Define conversation states
FULL_NAME, PHONE_NUMBER, LOCATION, RESUME = range(4)

class BotService(BaseServiceManager):
    """Service manager for Telegram bot operations"""
    
    def __init__(self):
        super().__init__()
        self.structured_logger = logging_service.get_structured_logger(__name__)
        self._instance: Optional[Application] = None
        self._lock = asyncio.Lock()
        self.register_required_service('telegram_bot', True)
        
    async def start_bot(self) -> bool:
        """Start the Telegram bot service using BotFactory"""
        try:
            async with self._lock:
                if self._instance and self._instance.running:
                    return True

                factory = await BotFactory.get_instance()
                self._instance = await factory.create_bot()

                if self._instance:
                    await self._instance.initialize()
                    await self._instance.start()
                    self._running = True
                    self.status.set_service_ready('telegram_bot', True)
                    self.structured_logger.info(
                        "Telegram bot started successfully",
                        {"service": "telegram_bot", "status": "running"}
                    )
                    return True
                return False

        except Exception as e:
            self.structured_logger.error(
                f"Error starting Telegram bot: {e}",
                {"service": "telegram_bot", "error_type": "startup_error", "error": str(e)}
            )
            self.status.set_service_ready('telegram_bot', False, str(e))
            return False

    async def stop_bot(self) -> bool:
        """Stop the Telegram bot service"""
        try:
            async with self._lock:
                if not self._instance:
                    return True

                factory = await BotFactory.get_instance()
                await factory.cleanup(cleanup_only=False)
                self._instance = None
                self._running = False
                self.status.set_cleanup_status('telegram_bot', True)
                
                self.structured_logger.info(
                    "Telegram bot stopped successfully",
                    {"service": "telegram_bot", "status": "stopped"}
                )
                return True

        except Exception as e:
            error_msg = f"Failed to stop Telegram bot: {e}"
            self.structured_logger.error(
                error_msg,
                {"service": "telegram_bot", "error_type": "shutdown_error", "error": str(e)}
            )
            self.status.set_cleanup_status('telegram_bot', False, error_msg)
            return False