from telegram import Update
from telegram.ext import ContextTypes
from commands.base_command import BaseCommand


class HelpCommand(BaseCommand):
    """Command handler for the /help command"""

    @BaseCommand.handle_command
    async def execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Execute the help command to display available bot commands.
        
        Args:
            update (Update): The update object from Telegram
            context (ContextTypes.DEFAULT_TYPE): The context object from Telegram
        """
        self.log_command_execution("help")
        
        help_text = (
            "Here are the available commands:\n\n"
            "/start - Start the bot\n"
            "/jobs - View available jobs\n"
            "/search - Search for specific jobs\n"
            "/profile - View and edit your profile\n"
            "/help - Show this help message"
        )
        
        await update.message.reply_text(help_text)