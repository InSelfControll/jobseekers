import os
import uuid
import logging
import pytesseract
import fitz  # PyMuPDF
import docx2txt
from PIL import Image
import io
from pathlib import Path
from typing import Optional, Dict, List, Union
from werkzeug.utils import secure_filename
from telegram import File
from models.employer import Employer

# Get absolute path to upload folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

logger = logging.getLogger(__name__)

import PyPDF2
from pdf2image import convert_from_path
from typing import Dict, List, Any
import os
import requests
import json

async def extract_resume_data(resume_path: str) -> Dict[str, Any]:
    """Extract data from resume using AI, including text from images"""
    try:
        # Convert resume_path to absolute path if not already
        abs_resume_path = os.path.join(UPLOAD_FOLDER, resume_path)
        
        # Verify file exists
        if not os.path.isfile(abs_resume_path):
            logger.error(f"Resume file not found: {abs_resume_path}")
            return get_default_resume_data()
            
        file_ext = os.path.splitext(abs_resume_path)[1].lower()[1:]
        text_content = ""
        
        if file_ext == 'pdf':
            # Extract text from PDF (both regular text and images)
            text_content = extract_from_pdf(abs_resume_path)
        elif file_ext in ['doc', 'docx']:
            # Extract text from Word documents
            text_content = docx2txt.process(resume_path)
        else:
            logger.error(f"Unsupported file format: {file_ext}")
            return get_default_resume_data()

        # Check for Abacus API key
        api_key = os.getenv('ABACUS_API_KEY')
        if not api_key:
            logger.error("ABACUS_API_KEY is not set in environment variables")
            return get_default_resume_data()

        # Prepare the API request
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        # Construct the prompt
        prompt = f"""Extract the following information from this resume text:
1. All skills (technical and soft skills)
2. Work experience with company names, dates, and responsibilities
3. Education details
4. Certifications
5. Languages

Resume text:
{text_content}

Format the response as a JSON object with these keys:
skills, experience, education, certifications, languages"""

        # Make request to Abacus AI GPT4 endpoint
        response = requests.post(
            "https://api.abacus.ai/v0/gpt4",
            headers=headers,
            json={
                "messages": [
                    {"role": "system", "content": "You are a professional resume parser. Extract and organize resume information accurately."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 1500
            }
        )

        if response.status_code != 200:
            logger.error(f"Abacus AI API error: {response.text}")
            return get_default_resume_data()

        # Parse API response
        api_response = response.json()
        extracted_data = json.loads(api_response['choices'][0]['message']['content'])
        logger.info(f"Successfully extracted resume data using AI for {resume_path}")
        return extracted_data

    except Exception as e:
        logger.error(f"Error extracting resume data: {str(e)}")
        return get_default_resume_data()

def extract_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF including images"""
    text_content = ""
    
    # Extract regular text using PyMuPDF (more reliable than PyPDF2)
    doc = fitz.open(pdf_path)
    for page in doc:
        text_content += page.get_text()
        
        # Extract images and process them with OCR
        images = page.get_images()
        for img_index, img in enumerate(images):
            try:
                # Get image data
                xref = img[0]
                base_img = doc.extract_image(xref)
                image_bytes = base_img["image"]
                
                # Convert image bytes to PIL Image
                image = Image.open(io.BytesIO(image_bytes))
                
                # Perform OCR
                image_text = pytesseract.image_to_string(image)
                text_content += "\n" + image_text
            except Exception as e:
                logger.error(f"Error extracting image {img_index}: {str(e)}")
                continue
    
    doc.close()
    return text_content

def get_default_resume_data() -> Dict[str, Any]:
    """Return default resume data structure"""
    return {
        "skills": ["communication", "teamwork"],
        "experience": [],
        "education": [],
        "certifications": [],
        "languages": ["English"]
    }

async def extract_skills(resume_path: str) -> Dict[str, List[str]]:
    """Extract skills from resume using AI"""
    try:
        full_data = await extract_resume_data(resume_path)
        return {"extracted_skills": full_data["skills"]}
    except Exception as e:
        logger.error(f"Error extracting skills: {str(e)}")
        return {"extracted_skills": ["communication", "teamwork"]}  # Default fallback

# Already defined at top of file
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

async def save_resume(file: File, user_id: int) -> Optional[str]:
    """Save resume file with UUID-based name in user-specific folder"""
    try:
        # Create user folder if it doesn't exist
        user_folder = Path(UPLOAD_FOLDER) / str(user_id)
        user_folder.mkdir(parents=True, exist_ok=True)
        
        # Get original filename and check extension
        original_filename = file.file_path.split('/')[-1]
        if not allowed_file(original_filename):
            logger.warning(f"Invalid file type for user {user_id}: {original_filename}")
            return None
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}_{secure_filename(original_filename)}"
        file_path = user_folder / unique_filename
        
        # Ensure file_path is absolute
        abs_file_path = file_path.absolute()
        
        # Download and save file
        await file.download_to_drive(str(abs_file_path))
        logger.info(f"Resume saved for user {user_id}: {abs_file_path}")
        
        # Return path relative to UPLOAD_FOLDER
        try:
            return str(abs_file_path.relative_to(Path(UPLOAD_FOLDER)))
        except ValueError:
            logger.error(f"Could not make path relative: {abs_file_path}")
            return str(abs_file_path)
        
    except Exception as e:
        logger.error(f"Error saving resume for user {user_id}: {str(e)}")
        return None
