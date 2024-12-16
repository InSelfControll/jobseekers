
from dataclasses import dataclass

@dataclass
class Config:
    TELEGRAM_TOKEN: str = None
    UPLOAD_FOLDER: str = 'uploads'
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB max file size
    SQLALCHEMY_DATABASE_URI: str = 'sqlite:///jobseekr.db'
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
