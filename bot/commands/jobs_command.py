from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from models import Job, JobSeeker
from app.services.cv_matcher import calculate_job_match
from .base_command import BaseCommand


class JobsCommand(BaseCommand):
    """Command handler for showing available jobs matching user's profile"""

    @BaseCommand.handle_command
    async def execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show available jobs that match the user's profile with 75% or higher match rate"""
        self.log_command_execution("jobs")

        # Get the JobSeeker profile
        job_seeker = JobSeeker.query.filter_by(telegram_id=str(update.effective_user.id)).first()
        
        if not job_seeker:
            await update.message.reply_text(
                "Please set up your profile first with /profile command"
            )
            return
        
        if not job_seeker.resume_path:
            await update.message.reply_text(
                "Please upload your CV first using /profile command"
            )
            return

        # Get active jobs and calculate match score for each
        active_jobs = Job.query.filter_by(status='active').all()
        matched_jobs = []
        
        for job in active_jobs:
            match_score = calculate_job_match(job_seeker, job)
            if match_score >= 75:  # Only include jobs with 75% or higher match
                matched_jobs.append((job, match_score))
        
        # Sort by match score descending
        matched_jobs.sort(key=lambda x: x[1], reverse=True)
        
        if not matched_jobs:
            await update.message.reply_text(
                "No highly matching jobs found at the moment.\n"
                "Try updating your profile or checking back later."
            )
            return
            
        for job, match_score in matched_jobs[:5]:  # Show top 5 matching jobs
            keyboard = [[
                InlineKeyboardButton("Apply", callback_data=f"apply_{job.id}"),
                InlineKeyboardButton("More Info", callback_data=f"info_{job.id}")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = (
                f"Match Score: {match_score}%\n"
                f"🏢 {job.employer.company_name}\n"
                f"📋 {job.title}\n"
                f"📍 {job.location}\n\n"
                f"{job.description[:200]}..."
            )
            
            await update.message.reply_text(message, reply_markup=reply_markup)