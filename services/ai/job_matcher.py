# Standard library imports
import logging
from typing import Dict, List, Union, Optional

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Type definitions
CandidateSkills = Dict[str, Union[List[str], int]]
JobRequirements = Dict[str, Union[List[str], int]]

def calculate_job_match(
    candidate_skills: CandidateSkills,
    job_requirements: JobRequirements
) -> int:
    """
    Calculate the match percentage between a candidate's skills and job requirements.
    
    Args:
        candidate_skills: Dictionary containing candidate's skills and experience
            {
                'technical_skills': List[str],
                'soft_skills': List[str],
                'total_years': int
            }
        job_requirements: Dictionary containing job requirements
            {
                'required_skills': List[str],
                'required_years': int
            }
    
    Returns:
        int: Match percentage between 0 and 100
        
    Raises:
        KeyError: If required keys are missing from input dictionaries
        ValueError: If input data types are invalid
        Exception: For other unexpected errors
    """
    try:
        # Validate input types
        if not isinstance(candidate_skills, dict) or not isinstance(job_requirements, dict):
            raise ValueError("Both candidate_skills and job_requirements must be dictionaries")

        # Calculate technical skills match
        candidate_tech_skills = set(candidate_skills.get('technical_skills', []))
        required_skills = set(job_requirements.get('required_skills', []))
        
        if not required_skills:
            logger.warning("No required skills specified in job requirements")
            tech_match = 1.0
        else:
            matching_skills = candidate_tech_skills & required_skills
            tech_match = len(matching_skills) / len(required_skills)
        
        # Calculate experience match
        exp_years = candidate_skills.get('total_years', 0)
        required_years = job_requirements.get('required_years', 0)
        
        if not isinstance(exp_years, (int, float)) or not isinstance(required_years, (int, float)):
            raise ValueError("Years of experience must be numeric")
            
        exp_match = min(exp_years / max(required_years, 1), 1.0) if required_years > 0 else 1.0
        
        # Weight the scores (60% skills, 40% experience)
        total_score = (tech_match * 0.6) + (exp_match * 0.4)
        
        # Convert to percentage and ensure it's between 0 and 100
        match_percentage = max(0, min(100, int(total_score * 100)))
        
        logger.debug(f"Match calculation - Tech: {tech_match:.2f}, Exp: {exp_match:.2f}, Total: {match_percentage}%")
        return match_percentage
        
    except KeyError as e:
        logger.error(f"Missing required key in input data: {e}")
        raise
    except ValueError as e:
        logger.error(f"Invalid input data: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error calculating job match: {e}")
        return 50  # Return default match percentage on unexpected errors