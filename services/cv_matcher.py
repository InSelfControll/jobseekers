import logging
from typing import Tuple
import json
from pathlib import Path

logger = logging.getLogger(__name__)

def calculate_job_match(job_seeker, job) -> float:
    """
    Calculate match percentage between a job seeker and a job posting.
    Returns a score between 0 and 100.
    """
    try:
        # Get job seeker skills
        seeker_skills = set(job_seeker.skills or [])
        if not seeker_skills:
            logger.warning(f"No skills found for job seeker {job_seeker.id}")
            return 0
            
        # Extract required skills from job description
        job_skills = _extract_skills_from_job(job)
        if not job_skills:
            logger.warning(f"No skills extracted from job {job.id}")
            return 0
            
        # Calculate match score
        total_required = len(job_skills)
        if total_required == 0:
            return 0
            
        matches = len(seeker_skills.intersection(job_skills))
        match_percentage = (matches / total_required) * 100
        
        # Apply location bonus if locations match
        if job_seeker.location and job.location:
            if _locations_match(job_seeker.location, job.location):
                match_percentage += 10
                
        # Cap at 100%
        match_percentage = min(match_percentage, 100)
        
        return round(match_percentage, 1)
        
    except Exception as e:
        logger.error(f"Error calculating job match: {e}")
        return 0

def _extract_skills_from_job(job) -> set:
    """Extract required skills from job description"""
    try:
        # First check if job has structured skills data
        if hasattr(job, 'required_skills') and job.required_skills:
            return set(job.required_skills)
            
        # Otherwise extract from description
        description = job.description.lower()
        
        # Load skills dictionary from JSON file
        skills_file = Path(__file__).parent / 'data' / 'skills.json'
        with open(skills_file) as f:
            skills_dict = json.load(f)
            
        # Look for skills mentions in description
        found_skills = set()
        for category in skills_dict.values():
            for skill in category:
                if skill.lower() in description:
                    found_skills.add(skill)
                    
        return found_skills
        
    except Exception as e:
        logger.error(f"Error extracting skills from job: {e}")
        return set()

def _locations_match(seeker_location: str, job_location: str) -> bool:
    """Check if job seeker location matches job location"""
    try:
        # Simple substring matching for now
        # Could be enhanced with geocoding and distance calculation
        seeker_location = seeker_location.lower()
        job_location = job_location.lower()
        
        return (
            seeker_location in job_location or
            job_location in seeker_location
        )
    except Exception as e:
        logger.error(f"Error matching locations: {e}")
        return False
