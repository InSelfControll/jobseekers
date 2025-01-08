"""
Bot package initialization.
This file makes the bot directory a Python package.
"""

# Export the main bot functions and decorators
from .telegram_bot import start_bot, stop_bot
from .decorators import monitor_handler, async_error_handler

__all__ = ['start_bot', 'stop_bot', 'monitor_handler', 'async_error_handler']
