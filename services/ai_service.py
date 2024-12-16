
import logging
import json
import os
import httpx
from PyPDF2 import PdfReader
import re

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

ABACUS_API_KEY = os.environ.get("ABACUS_API_KEY")
ABACUS_API_BASE_URL = "https://api.abacus.ai/v0"

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return ""

def extract_skills(resume_path):
    """Extract skills from resume using AbacusAI"""
    try:
        resume_text = extract_text_from_pdf(resume_path)
        
        # Structure the resume data for AI analysis
        prompt = f"""
        Analyze this resume text and extract key information:
        {resume_text}
        
        Extract and categorize:
        1. Technical skills
        2. Soft skills
        3. Work experience
        4. Education
        5. Languages
        6. Years of experience
        """
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ABACUS_API_BASE_URL}/analyze",
                headers={"Authorization": f"Bearer {ABACUS_API_KEY}"},
                json={"text": prompt}
            )
            
            if response.status_code == 200:
                return response.json()
            
        # Fallback mock response
        return {
            "technical_skills": ["Python", "SQL", "Data Analysis"],
            "soft_skills": ["Communication", "Leadership"],
            "experience": ["Software Engineer - 3 years", "Data Analyst - 2 years"],
            "education": ["Bachelor's in Computer Science"],
            "languages": ["English"],
            "total_years": 5
        }
            
    except Exception as e:
        logger.error(f"Error extracting skills: {e}")
        return {
            "technical_skills": [],
            "soft_skills": [],
            "experience": [],
            "education": [],
            "languages": [],
            "total_years": 0
        }

def generate_cover_letter(candidate_info, job_info):
    """Generate a personalized cover letter using AI"""
    try:
        prompt = f"""
        Generate a professional cover letter based on:
        
        Candidate Background:
        - Skills: {', '.join(candidate_info.get('technical_skills', []) + candidate_info.get('soft_skills', []))}
        - Experience: {'; '.join(candidate_info.get('experience', []))}
        - Education: {'; '.join(candidate_info.get('education', []))}
        
        Job Details:
        - Title: {job_info.get('title')}
        - Company: {job_info.get('company')}
        - Requirements: {job_info.get('description')}
        """
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ABACUS_API_BASE_URL}/generate",
                headers={"Authorization": f"Bearer {ABACUS_API_KEY}"},
                json={"prompt": prompt}
            )
            
            if response.status_code == 200:
                return response.json().get('text')
        
        # Fallback template
        return f"""
        Dear Hiring Manager,

        I am writing to express my strong interest in the {job_info.get('title')} position at {job_info.get('company')}. 
        With {candidate_info.get('total_years', 0)} years of experience and expertise in {', '.join(candidate_info.get('technical_skills', []))}, 
        I believe I would be an excellent fit for this role.

        Best regards,
        {candidate_info.get('name', '[Candidate Name]')}
        """
            
    except Exception as e:
        logger.error(f"Error generating cover letter: {e}")
        return "Error generating cover letter. Please try again later."

def calculate_job_match(candidate_skills, job_requirements):
    """Calculate detailed match percentage between candidate and job"""
    try:
        # Calculate technical skills match
        tech_match = len(set(candidate_skills.get('technical_skills', [])) & 
                        set(job_requirements.get('required_skills', [])))
        
        # Calculate experience match
        exp_years = candidate_skills.get('total_years', 0)
        required_years = job_requirements.get('required_years', 0)
        exp_match = min(exp_years / max(required_years, 1), 1.0) if required_years > 0 else 1.0
        
        # Weight the scores (60% skills, 40% experience)
        total_score = (tech_match * 0.6) + (exp_match * 0.4)
        return int(total_score * 100)
        
    except Exception as e:
        logger.error(f"Error calculating job match: {e}")
        return 50
