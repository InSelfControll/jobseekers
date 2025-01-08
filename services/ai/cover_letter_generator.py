# Standard library imports
import logging
import os
from typing import Dict, List, Optional, Union

# Third-party imports
import httpx

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Constants
ABACUS_API_KEY = os.environ.get("ABACUS_API_KEY")
ABACUS_API_BASE_URL = "https://api.abacus.ai/v0"

async def generate_cover_letter(
    candidate_info: Dict[str, Union[List[str], int, str]], 
    job_info: Dict[str, str]
) -> str:
    """
    Generate a personalized cover letter using AI based on candidate and job information.
    
    Args:
        candidate_info: Dictionary containing candidate details with the following structure:
            - technical_skills (List[str]): List of technical skills
            - soft_skills (List[str]): List of soft skills
            - experience (List[str]): List of work experiences
            - education (List[str]): List of educational qualifications
            - name (Optional[str]): Candidate's name
            - total_years (Optional[int]): Total years of experience
            
        job_info: Dictionary containing job details with the following structure:
            - title (str): Job title
            - company (str): Company name
            - description (str): Job description/requirements
            
    Returns:
        str: Generated cover letter text
        
    Raises:
        httpx.HTTPError: If there's an error in the API request
        KeyError: If required fields are missing in the input dictionaries
        Exception: For any other unexpected errors
    """
    try:
        # Validate required fields
        required_job_fields = ['title', 'company', 'description']
        if not all(field in job_info for field in required_job_fields):
            raise KeyError("Missing required job information fields")

        # Prepare skills list safely
        technical_skills = candidate_info.get('technical_skills', [])
        soft_skills = candidate_info.get('soft_skills', [])
        all_skills = ', '.join(technical_skills + soft_skills)
        
        # Prepare experience and education safely
        experience = '; '.join(candidate_info.get('experience', []))
        education = '; '.join(candidate_info.get('education', []))

        prompt = f"""
        Generate a professional cover letter based on:

        Candidate Background:
        - Skills: {all_skills}
        - Experience: {experience}
        - Education: {education}

        Job Details:
        - Title: {job_info['title']}
        - Company: {job_info['company']}
        - Requirements: {job_info['description']}
        """

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ABACUS_API_BASE_URL}/generate",
                headers={"Authorization": f"Bearer {ABACUS_API_KEY}"},
                json={"prompt": prompt},
                timeout=30.0
            )
            
            response.raise_for_status()
            result = response.json()
            
            if 'text' in result:
                return result['text']

        logger.warning("API response missing 'text' field, falling back to template")
        return _generate_fallback_cover_letter(candidate_info, job_info)

    except httpx.HTTPError as e:
        logger.error(f"HTTP error occurred while generating cover letter: {e}")
        return _generate_fallback_cover_letter(candidate_info, job_info)
    except KeyError as e:
        logger.error(f"Missing required field in input data: {e}")
        return "Error: Missing required information for cover letter generation."
    except Exception as e:
        logger.error(f"Unexpected error generating cover letter: {e}")
        return "Error generating cover letter. Please try again later."

def _generate_fallback_cover_letter(
    candidate_info: Dict[str, Union[List[str], int, str]], 
    job_info: Dict[str, str]
) -> str:
    """
    Generate a fallback cover letter template when the AI service is unavailable.
    
    Args:
        candidate_info: Dictionary containing candidate details
        job_info: Dictionary containing job details
        
    Returns:
        str: Basic cover letter template
    """
    return f"""
    Dear Hiring Manager,

    I am writing to express my strong interest in the {job_info.get('title', '[Position]')} position at {job_info.get('company', '[Company]')}. 
    With {candidate_info.get('total_years', 0)} years of experience and expertise in {', '.join(candidate_info.get('technical_skills', []))}, 
    I believe I would be an excellent fit for this role.

    Best regards,
    {candidate_info.get('name', '[Candidate Name]')}
    """