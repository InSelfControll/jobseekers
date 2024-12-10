import os
import uuid
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'

async def save_resume(file):
    """Save resume file with UUID-based name"""
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    # Generate UUID for filename
    filename = str(uuid.uuid4()) + '_' + secure_filename(file.file_path)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    # Download and save file
    await file.download_to_drive(file_path)
    
    return file_path
