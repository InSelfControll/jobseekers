from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from models import JobSeeker, Job, Application
from services.ai_service import extract_skills, generate_cover_letter
from services.geo_service import get_nearby_jobs
from services.file_service import save_resume
from extensions import db
import logging

FULL_NAME, LOCATION, RESUME = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when /start command is issued"""
    await update.message.reply_text(
        "Welcome to the Job Application Bot! 🎯\n"
        "Use /register to create your profile and start applying for jobs."
    )

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the registration process"""
    await update.message.reply_text(
        "Let's create your profile! First, please send me your full name."
    )
    return FULL_NAME

async def handle_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the full name input"""
    context.user_data['full_name'] = update.message.text
    await update.message.reply_text(
        "Great! Now please share your location to help us find jobs near you."
    )
    return LOCATION

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the location input"""
    location = update.message.location
    context.user_data['latitude'] = location.latitude
    context.user_data['longitude'] = location.longitude
    
    await update.message.reply_text(
        "Perfect! Finally, please send your resume as a PDF file."
    )
    return RESUME

async def handle_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the resume upload"""
    try:
        file = await update.message.document.get_file()
        resume_path = await save_resume(file)
        
        # Extract skills using AI
        skills = extract_skills(resume_path)
        
        # Create job seeker profile
        job_seeker = JobSeeker(
            telegram_id=str(update.effective_user.id),
            full_name=context.user_data['full_name'],
            resume_path=resume_path,
            skills=skills,
            latitude=context.user_data['latitude'],
            longitude=context.user_data['longitude']
        )
        
        db.session.add(job_seeker)
        db.session.commit()
        
        await update.message.reply_text(
            "Registration complete! 🎉\n"
            "Use /search to find jobs in your area."
        )
        return ConversationHandler.END
        
    except Exception as e:
        logging.error(f"Error in handle_resume: {e}")
        await update.message.reply_text(
            "Sorry, there was an error processing your resume. Please try again."
        )
        return ConversationHandler.END

async def handle_job_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle job search command"""
    job_seeker = JobSeeker.query.filter_by(
        telegram_id=str(update.effective_user.id)
    ).first()
    
    if not job_seeker:
        await update.message.reply_text(
            "Please register first using /register command."
        )
        return
    
    nearby_jobs = get_nearby_jobs(job_seeker.latitude, job_seeker.longitude)
    
    if not nearby_jobs:
        await update.message.reply_text(
            "No jobs found in your area. We'll notify you when new positions become available!"
        )
        return
    
    for job in nearby_jobs:
        await update.message.reply_text(
            f"🏢 {job.title}\n"
            f"📍 {job.location}\n"
            f"📝 {job.description[:200]}...\n\n"
            f"To apply, use /apply {job.id}"
        )

async def handle_application(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle job application"""
    try:
        job_id = int(context.args[0])
        job_seeker = JobSeeker.query.filter_by(
            telegram_id=str(update.effective_user.id)
        ).first()
        
        if not job_seeker:
            await update.message.reply_text("Please register first using /register command.")
            return
        
        job = Job.query.get(job_id)
        if not job:
            await update.message.reply_text("Job not found.")
            return
        
        # Generate cover letter using AI
        cover_letter = generate_cover_letter(job_seeker.skills, job.description)
        
        # Create application
        application = Application(
            job_id=job.id,
            job_seeker_id=job_seeker.id,
            cover_letter=cover_letter
        )
        
        db.session.add(application)
        db.session.commit()
        
        await update.message.reply_text(
            "Application submitted successfully! 🎉\n"
            "We'll notify you of any updates."
        )
        
    except Exception as e:
        logging.error(f"Error in handle_application: {e}")
        await update.message.reply_text(
            "Sorry, there was an error submitting your application. Please try again."
        )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the conversation"""
    await update.message.reply_text(
        "Registration cancelled. Use /register to start again."
    )
    return ConversationHandler.END
