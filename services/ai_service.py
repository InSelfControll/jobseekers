import logging
import json
import os
import httpx

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

ABACUS_API_KEY = os.environ.get("ABACUS_API_KEY")
ABACUS_API_BASE_URL = "https://api.abacus.ai/v0"  # Example base URL

def extract_skills(resume_path):
    """Extract skills from resume using AbacusAI"""
    try:
        with open(resume_path, 'rb') as file:  # Changed to 'rb' for PDF files
            resume_text = file.read()
        
        # For now, return a mock response since we're waiting for the API key
        logger.info("Extracting skills from resume")
        return {
            "technical_skills": ["Python", "SQL", "Data Analysis"],
            "soft_skills": ["Communication", "Team Leadership"],
            "languages": ["English"]
        }
            
    except Exception as e:
        logger.error(f"Error extracting skills: {e}")
        return {
            "technical_skills": [],
            "soft_skills": [],
            "languages": []
        }

def generate_cover_letter(skills, job_description):
    """Generate a cover letter using AbacusAI"""
    try:
        # For now, return a mock response since we're waiting for the API key
        logger.info("Generating cover letter")
        
        cover_letter = (
            f"Dear Hiring Manager,\n\n"
            f"I am writing to express my interest in the position. "
            f"With my background in {', '.join(skills.get('technical_skills', []))}, "
            f"I believe I would be a great fit for this role.\n\n"
            f"Best regards"
        )
        return cover_letter
            
    except Exception as e:
        logger.error(f"Error generating cover letter: {e}")
        return "Error generating cover letter. Please try again later."
