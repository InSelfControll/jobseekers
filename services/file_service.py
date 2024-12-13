
import os
import uuid
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'

async def save_resume(file, user_id):
    """Save resume file with UUID-based name in user-specific folder"""
    user_folder = os.path.join(UPLOAD_FOLDER, str(user_id))
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    
    # Generate UUID for filename
    filename = str(uuid.uuid4()) + '_' + secure_filename(file.file_path)
    file_path = os.path.join(user_folder, filename)
    
    # Download and save file
    await file.download_to_drive(file_path)
    
    return os.path.join(str(user_id), filename)
