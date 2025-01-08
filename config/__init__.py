from builtins import bool, int, set, str
from dataclasses import dataclass, field

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
    WTF_CSRF_METHODS: set = field(default_factory=lambda: {'POST', 'PUT', 'PATCH', 'DELETE'})
    
    # Added SSO config
    GITHUB_CLIENT_ID: str = None
    GITHUB_CLIENT_SECRET: str = None
    AUTH0_DOMAIN: str = None
    AUTH0_CLIENT_ID: str = None
    AUTH0_CLIENT_SECRET: str = None
    
    # Added AI integration
    ABACUS_API_KEY: str = None
    ABACUS_ORG_ID: str = None
    
    # Added SSL config
    SSL_CERT_PATH: str = None
    SSL_KEY_PATH: str = None
    
    # Added core secrets
    FLASK_SECRET_KEY: str = None
    DATABASE_URL: str = None
