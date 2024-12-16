
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from models import JobSeeker, Job, Application
from services.ai_service import extract_skills, generate_cover_letter
from services.geo_service import get_nearby_jobs
from services.file_service import save_resume
from extensions import db
import logging

FULL_NAME, PHONE_NUMBER, LOCATION, RESUME = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message when /start command is issued"""
    try:
        await update.message.reply_text(
            "Welcome to the Job Application Bot! 🎯\n"
            "Use /register to create your profile and start applying for jobs."
        )
    except Exception as e:
        logger.error(f"Error in start handler: {e}")
        await update.message.reply_text("An error occurred. Please try again.")

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the registration process"""
    try:
        await update.message.reply_text(
            "Let's create your profile! First, please send me your full name."
        )
        return FULL_NAME
    except Exception as e:
        logger.error(f"Error in register handler: {e}")
        await update.message.reply_text("An error occurred. Please try again.")
        return ConversationHandler.END

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
    """Handle the resume upload"""
    from app import create_app
    app = create_app()
    
    try:
        if not update.message.document:
            await update.message.reply_text("Please send your resume as a PDF file.")
            return ConversationHandler.END

        with app.app_context():
            file = await update.message.document.get_file()
            resume_path = await save_resume(file, update.effective_user.id)
            
            # Extract skills using AI
            skills = extract_skills(resume_path)
            
            # Create job seeker profile
            job_seeker = JobSeeker(
                telegram_id=str(update.effective_user.id),
                full_name=context.user_data['full_name'],
                phone_number=context.user_data['phone_number'],
                resume_path=resume_path,
                skills=skills,
                latitude=context.user_data['latitude'],
                longitude=context.user_data['longitude']
            )
            
            db.session.add(job_seeker)
            db.session.commit()
            logging.info(f"Successfully registered job seeker: {job_seeker.telegram_id}")
            
            await update.message.reply_text(
                "Registration complete! 🎉\n"
                "Use /search to find jobs in your area."
            )
            return ConversationHandler.END
    except Exception as db_error:
        if 'db' in locals():
            db.session.rollback()
        logging.error(f"Database error in handle_resume: {db_error}")
        await update.message.reply_text(
            "Error saving your profile. Please try registering again with /register"
        )
        return ConversationHandler.END

async def handle_job_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle job search command"""
    from app import create_app
    app = create_app()
    
    # Get search radius from command arguments
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
            
            nearby_jobs = get_nearby_jobs(job_seeker.latitude, job_seeker.longitude, radius)
            
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
                # Load employer relationship within context
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
            return
            
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
            await update.message.reply_text(
                f"🏢 *{job.title}*\n"
                f"🏗 _{job.employer.company_name}_\n"
                f"📍 {job.location} ({job.distance:.1f}km away)\n"
                f"💼 {job.description[:150]}...\n\n"
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

async def handle_application(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle job application"""
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
            return
        
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
