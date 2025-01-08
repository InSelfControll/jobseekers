import logging
from typing import Dict, Any
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from bot.commands.base_command import BaseCommand
from models.job_seeker import JobSeeker

logger = logging.getLogger(__name__)

class RegisterCommand(BaseCommand):
    # Conversation states
    FULL_NAME = 0
    PHONE_NUMBER = 1
    LOCATION = 2
    RESUME = 3

    def __init__(self):
        super().__init__()
        self.user_data: Dict[str, Any] = {}

    @BaseCommand.handle_command
    async def register(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start the registration process"""
        self.log_command_execution("register")
        
        # Check if user is already registered
        session = await self.get_db_session()
        existing_user = session.query(JobSeeker).filter_by(
            telegram_id=str(update.effective_user.id)
        ).first()
        
        if existing_user:
            await update.message.reply_text(
                "You are already registered! Use /search to look for jobs or /apply to apply for positions."
            )
            return ConversationHandler.END
        
        await update.message.reply_text(
            "Let's get you registered! Please enter your full name:"
        )
        return self.FULL_NAME

    @BaseCommand.handle_command
    async def handle_full_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle full name input"""
        full_name = update.message.text.strip()
        if not full_name or len(full_name) < 2:
            await update.message.reply_text(
                "Please enter a valid full name (at least 2 characters):"
            )
            return self.FULL_NAME
        
        self.user_data['full_name'] = full_name
        await update.message.reply_text(
            "Great! Now please enter your phone number:"
        )
        return self.PHONE_NUMBER

    @BaseCommand.handle_command
    async def handle_phone_number(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle phone number input"""
        phone_number = update.message.text.strip()
        if not phone_number.replace('+', '').isdigit():
            await update.message.reply_text(
                "Please enter a valid phone number (only numbers and + allowed):"
            )
            return self.PHONE_NUMBER
        
        self.user_data['phone_number'] = phone_number
        await update.message.reply_text(
            "Please share your location to help us find jobs near you.",
            reply_markup=self._get_location_keyboard()
        )
        return self.LOCATION

    @BaseCommand.handle_command
    async def handle_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle location input"""
        location = update.message.location
        self.user_data.update({
            'latitude': location.latitude,
            'longitude': location.longitude,
            'location': f"{location.latitude},{location.longitude}"
        })
        
        await update.message.reply_text(
            "Almost done! Please upload your resume (PDF format):"
        )
        return self.RESUME

    @BaseCommand.handle_command
    async def handle_resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle resume upload"""
        document = update.message.document
        if not document.file_name.lower().endswith('.pdf'):
            await update.message.reply_text(
                "Please upload your resume in PDF format:"
            )
            return self.RESUME

        file = await context.bot.get_file(document.file_id)
        file_path = f"resumes/{update.effective_user.id}_{document.file_name}"
        await file.download_to_drive(file_path)
        
        self.user_data['resume_path'] = file_path
        
        # Save user data to database
        try:
            session = await self.get_db_session()
            job_seeker = JobSeeker(
                telegram_id=str(update.effective_user.id),
                full_name=self.user_data['full_name'],
                phone_number=self.user_data['phone_number'],
                resume_path=self.user_data['resume_path'],
                location=self.user_data['location'],
                latitude=self.user_data['latitude'],
                longitude=self.user_data['longitude']
            )
            session.add(job_seeker)
            await self.commit_transaction()
            
            await update.message.reply_text(
                "Registration complete! You can now use /search to look for jobs and /apply to submit applications."
            )
        except Exception as e:
            await self.handle_error(e)
            await update.message.reply_text(
                "An error occurred during registration. Please try again later."
            )
        
        return ConversationHandler.END

    @BaseCommand.handle_command
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel the registration process"""
        await update.message.reply_text(
            "Registration cancelled. You can start again with /register when you're ready."
        )
        return ConversationHandler.END

    def _get_location_keyboard(self):
        """Helper method to create location keyboard"""
        from telegram import KeyboardButton, ReplyKeyboardMarkup
        location_keyboard = KeyboardButton(text="Share Location", request_location=True)
        return ReplyKeyboardMarkup([[location_keyboard]], one_time_keyboard=True)