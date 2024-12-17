import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, error as telegram_error
from telegram.ext import (
    ContextTypes, 
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext
)
from models import JobSeeker, Job, Application
from services.ai_service import extract_skills, generate_cover_letter
from services.geo_service import get_nearby_jobs
from services.file_service import save_resume
from extensions import db
from .middleware import monitor_handler, async_error_handler

logger = logging.getLogger(__name__)

FULL_NAME, PHONE_NUMBER, LOCATION, RESUME = range(4)

@monitor_handler
@async_error_handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message when /start command is issued"""
    try:
        await update.message.reply_text(
            "Welcome to the Job Application Bot! 🎯\n"
            "Use /register to create your profile and start applying for jobs."
        )
        logger.info(f"Start command used by user {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text("Sorry, something went wrong. Please try again.")

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the registration process"""
    await update.message.reply_text(
        "Let's create your profile! First, please send me your full name."
    )
    return FULL_NAME

async def handle_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the full name input"""
    context.user_data['full_name'] = update.message.text
    await update.message.reply_text(
        "Please share your phone number in the format +1234567890 📱"
    )
    return PHONE_NUMBER

async def handle_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the phone number input"""
    phone = update.message.text
    if not phone.startswith('+') or not phone[1:].isdigit():
        await update.message.reply_text(
            "Please enter a valid phone number starting with + (e.g., +1234567890)"
        )
        return PHONE_NUMBER
    
    context.user_data['phone_number'] = phone
    location_keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton('Share Location 📍', request_location=True)]],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    await update.message.reply_text(
        "Please share your location to help find jobs near you.\n"
        "Click the 'Share Location' button below 👇",
        reply_markup=location_keyboard
    )
    return LOCATION

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the location input"""
    try:
        location = update.message.location
        if not location:
            await update.message.reply_text("Please share your location using the button below.")
            return LOCATION
            
        context.user_data['latitude'] = location.latitude
        context.user_data['longitude'] = location.longitude
        
        await update.message.reply_text(
            "Perfect! Finally, please send your resume as a PDF file."
        )
        return RESUME
    except Exception as e:
        logging.error(f"Error handling location: {str(e)}")
        await update.message.reply_text(
            "There was an error processing your location. Please try again."
        )
        return LOCATION

async def handle_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the resume upload with proper database operations"""
    from app import create_app
    from extensions import db
    logger = logging.getLogger(__name__)
    
    app = create_app()
    if not app:
        logger.error("Failed to create application context")
        await update.message.reply_text("An error occurred. Please try again later.")
        return ConversationHandler.END
    
    try:
        # Initial validation
        if not update.message.document:
            logger.warning(f"No document provided by user {update.effective_user.id}")
            await update.message.reply_text("Please send your resume as a PDF file.")
            return ConversationHandler.END

        if not update.message.document.file_name.lower().endswith('.pdf'):
            logger.warning(f"Non-PDF file uploaded by user {update.effective_user.id}")
            await update.message.reply_text("Please upload your resume in PDF format only.")
            return ConversationHandler.END

        logger.info(f"Starting resume processing for user {update.effective_user.id}")
        
        # Verify user data exists
        required_fields = ['full_name', 'phone_number', 'latitude', 'longitude']
        missing_fields = [field for field in required_fields if field not in context.user_data]
        if missing_fields:
            logger.error(f"Missing required fields for user {update.effective_user.id}: {missing_fields}")
            await update.message.reply_text(
                "Some information is missing. Please start registration again with /register"
            )
            return ConversationHandler.END

        # Save resume file
        file = await update.message.document.get_file()
        logger.info(f"Got file object for user {update.effective_user.id}")
        resume_path = await save_resume(file, update.effective_user.id)
        logger.info(f"Resume saved at {resume_path}")
        
        # Extract skills with better error handling
        skills = {"default_skills": ["general"]}  # Default skills
        try:
            extracted_skills = await extract_skills(resume_path)
            if extracted_skills:
                if isinstance(extracted_skills, str):
                    skills = {"extracted_skills": [extracted_skills]}
                elif isinstance(extracted_skills, (list, dict)):
                    skills = extracted_skills
                logger.info(f"Skills extracted successfully: {skills}")
        except Exception as skill_error:
            logger.error(f"Error extracting skills: {str(skill_error)}")
            # Continue with default skills

        # Database operations
        with app.app_context():
            try:
                # Check for existing profile
                existing_profile = JobSeeker.query.filter_by(
                    telegram_id=str(update.effective_user.id)
                ).first()
                
                if existing_profile:
                    logger.info(f"Updating existing profile for user {update.effective_user.id}")
                    existing_profile.full_name = context.user_data['full_name']
                    existing_profile.phone_number = context.user_data['phone_number']
                    existing_profile.resume_path = resume_path
                    existing_profile.skills = skills
                    existing_profile.latitude = context.user_data['latitude']
                    existing_profile.longitude = context.user_data['longitude']
                else:
                    logger.info(f"Creating new profile for user {update.effective_user.id}")
                    new_job_seeker = JobSeeker(
                        telegram_id=str(update.effective_user.id),
                        full_name=context.user_data['full_name'],
                        phone_number=context.user_data['phone_number'],
                        resume_path=resume_path,
                        skills=skills,
                        latitude=context.user_data['latitude'],
                        longitude=context.user_data['longitude']
                    )
                    db.session.add(new_job_seeker)
                
                db.session.commit()
                logger.info(f"Successfully saved profile for user {update.effective_user.id}")
                
                await update.message.reply_text(
                    "Registration complete! 🎉\n"
                    "Use /search to find jobs in your area."
                )
                return ConversationHandler.END
                
            except Exception as db_error:
                logger.error(f"Database error: {str(db_error)}")
                db.session.rollback()
                raise
                    
    except Exception as e:
        logger.error(f"Error in handle_resume for user {update.effective_user.id}: {str(e)}")
        await update.message.reply_text(
            "Sorry, there was an error processing your registration. "
            "Please try again with /register"
        )
        return ConversationHandler.END

@monitor_handler
@async_error_handler
async def handle_job_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle job search command with proper monitoring and error handling"""
    from app import create_app
    app = create_app()
    
    try:
        radius = float(context.args[0]) if context.args else 15
    except (ValueError, IndexError):
        radius = 15
    
    try:
        with app.app_context():
            job_seeker = JobSeeker.query.filter_by(
                telegram_id=str(update.effective_user.id)
            ).first()
            
            if not job_seeker:
                await update.message.reply_text(
                    "⚠️ Please register first using /register command.\n"
                    "This will help us find jobs near you!"
                )
                return
            
            if not job_seeker.latitude or not job_seeker.longitude:
                await update.message.reply_text(
                    "📍 Please share your location to find nearby jobs.\n"
                    "Use /register to update your location."
                )
                return
            
            await update.message.reply_text("🔍 Searching for jobs in your area...")
            
            nearby_jobs = get_nearby_jobs(job_seeker.latitude, job_seeker.longitude, int(radius))
            
            if not nearby_jobs:
                await update.message.reply_text(
                    f"😔 No jobs found within {radius}km of your location.\n"
                    "We'll notify you when new positions become available!\n\n"
                    "💡 Tip: Try expanding your search radius using /search <radius>\n"
                    "Example: /search 25 to search within 25km"
                )
                return

            await update.message.reply_text(
                f"🎉 Found {len(nearby_jobs)} jobs near you!"
            )
            
            for job in nearby_jobs[:5]:  # Limit to 5 jobs per search
                employer_name = db.session.merge(job).employer.company_name
                await update.message.reply_text(
                    f"🏢 *{job.title}*\n"
                    f"🏗 _{employer_name}_\n"
                    f"📍 {job.location} ({job.distance:.1f}km away)\n"
                    f"💼 Description:\n{job.description}\n\n"
                    f"📝 To apply, use /apply {job.id}",
                    parse_mode='Markdown'
                )

            if len(nearby_jobs) > 5:
                await update.message.reply_text(
                    f"🔍 {len(nearby_jobs) - 5} more jobs available.\n"
                    "Use /search again to see more results!"
                )
                
    except Exception as e:
        logging.error(f"Error in handle_job_search: {e}")
        await update.message.reply_text(
            "😓 Sorry, something went wrong while searching for jobs.\n"
            "Please try again later."
        )

@monitor_handler
@async_error_handler
async def handle_application(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle job application with monitoring and error handling"""
    from app import create_app
    app = create_app()
    
    try:
        if not context.args:
            await update.message.reply_text(
                "⚠️ Please specify a job ID.\n"
                "Example: /apply 123"
            )
            return
            
        with app.app_context():
            job_id = int(context.args[0])
            job_seeker = JobSeeker.query.filter_by(
                telegram_id=str(update.effective_user.id)
            ).first()
            
            if not job_seeker:
                await update.message.reply_text(
                    "⚠️ Please register first using /register command.\n"
                    "This will help us create your profile!"
                )
                return
            
            job = Job.query.get(job_id)
            if not job:
                await update.message.reply_text(
                    "❌ Job not found. Please check the job ID and try again.\n"
                    "Use /search to see available jobs."
                )
                return
                
            # Check if already applied
            existing_application = Application.query.filter_by(
                job_id=job.id,
                job_seeker_id=job_seeker.id
            ).first()
            
            if existing_application:
                await update.message.reply_text(
                    "📝 You have already applied for this position!\n"
                    f"Current status: {existing_application.status}"
                )
                return
            
            await update.message.reply_text(
                "🤖 Generating your personalized cover letter..."
            )
            
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
                f"✅ Application submitted successfully for:\n"
                f"🏢 {job.title} at {job.employer.company_name}\n\n"
                f"Your cover letter has been generated based on your skills.\n"
                "We'll notify you of any updates from the employer!"
            )
            
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid job ID. Please use a number.\n"
            "Example: /apply 123"
        )
    except Exception as e:
        logging.error(f"Error in handle_application: {e}")
        await update.message.reply_text(
            "😓 Sorry, there was an error submitting your application.\n"
            "Please try again later."
        )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the conversation"""
    await update.message.reply_text(
        "Registration cancelled. Use /register to start again."
    )
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Centralized error handler for bot updates"""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.message:
        await update.message.reply_text(
            "Sorry, something went wrong. Please try again later."
        )
