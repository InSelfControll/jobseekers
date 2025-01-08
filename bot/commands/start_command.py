from telegram import Update
from telegram.ext import ContextTypes
from commands.base_command import BaseCommand


class StartCommand(BaseCommand):
    """Command handler for the /start command"""

    @BaseCommand.handle_command
    async def execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle the /start command.
        
        Args:
            update (Update): The update object containing message data
            context (ContextTypes.DEFAULT_TYPE): The context object for the command
        """
        self.log_command_execution("start")
        
        user = update.effective_user
        await update.message.reply_html(
            f"Hi {user.mention_html()}!\n\n"
            "I'm your job search assistant. Here's what I can help you with:\n\n"
            "/jobs - View available jobs\n"
            "/help - Show available commands"
        )