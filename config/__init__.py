
from dataclasses import dataclass

@dataclass
class Config:
    TELEGRAM_TOKEN: str = None
    UPLOAD_FOLDER: str = 'uploads'
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB max file size
    SQLALCHEMY_DATABASE_URI: str = 'sqlite:///jobseekr.db'
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    WTF_CSRF_ENABLED: bool = True
    WTF_CSRF_SECRET_KEY: str = "your-csrf-secret-key"  # Change in production
    WTF_CSRF_TIME_LIMIT: int = 3600
    WTF_CSRF_SSL_STRICT: bool = True
    WTF_CSRF_METHODS: set = {'POST', 'PUT', 'PATCH', 'DELETE'}
