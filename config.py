import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'dev_key'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_NAME = os.environ.get('DB_NAME', 'jobsearch')
    
    # Session
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(days=14)
    
    # Security
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or 'csrf-key'
    
    # SSL/TLS
    # SSL/TLS Configuration
    SSL_REQUIRED = os.environ.get('SSL_REQUIRED', 'False').lower() == 'true'
    SSL_CERT_DIR = os.environ.get('SSL_CERT_DIR', 'certs')
    SSL_KEY_FILE = os.environ.get('SSL_KEY_FILE', 'server.key')
    SSL_CERT_FILE = os.environ.get('SSL_CERT_FILE', 'server.crt')
    SSL_VERIFY_CLIENT = os.environ.get('SSL_VERIFY_CLIENT', 'False').lower() == 'true'
    # Bot Service Configuration
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    TELEGRAM_BOT_REQUIRED = os.environ.get('TELEGRAM_BOT_REQUIRED', 'False').lower() == 'true'
    TELEGRAM_BOT_WEBHOOK_URL = os.environ.get('TELEGRAM_BOT_WEBHOOK_URL')
    TELEGRAM_BOT_POLLING_TIMEOUT = int(os.environ.get('TELEGRAM_BOT_POLLING_TIMEOUT', '30'))
    TELEGRAM_BOT_MAX_CONNECTIONS = int(os.environ.get('TELEGRAM_BOT_MAX_CONNECTIONS', '40'))

    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.environ.get('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    LOG_DIR = os.environ.get('LOG_DIR', 'logs')
    LOG_FILE_MAX_BYTES = int(os.environ.get('LOG_FILE_MAX_BYTES', 10 * 1024 * 1024))  # 10MB
    LOG_FILE_BACKUP_COUNT = int(os.environ.get('LOG_FILE_BACKUP_COUNT', '5'))
    LOG_STRUCTURED_FORMAT = os.environ.get('LOG_STRUCTURED_FORMAT',
                                         '%(asctime)s - %(name)s - %(levelname)s - %(structured_data)s - %(message)s')

    # Service Management Configuration
    SERVICE_STARTUP_TIMEOUT = int(os.environ.get('SERVICE_STARTUP_TIMEOUT', '60'))  # seconds
    REQUIRED_SERVICES = os.environ.get('REQUIRED_SERVICES', '').split(',')
    SERVICE_RETRY_ATTEMPTS = int(os.environ.get('SERVICE_RETRY_ATTEMPTS', '3'))
    SERVICE_RETRY_DELAY = int(os.environ.get('SERVICE_RETRY_DELAY', '5'))  # seconds

    # Service Status Persistence
    STATUS_PERSISTENCE_ENABLED = os.environ.get('STATUS_PERSISTENCE_ENABLED', 'True').lower() == 'true'
    STATUS_FILE_PATH = os.environ.get('STATUS_FILE_PATH', 'service_status.json')
    STATUS_UPDATE_INTERVAL = int(os.environ.get('STATUS_UPDATE_INTERVAL', '300'))  # seconds
    STATUS_BACKUP_COUNT = int(os.environ.get('STATUS_BACKUP_COUNT', '3'))
    # SSO Configuration
    SSO_ENABLED = os.environ.get('SSO_ENABLED', 'False').lower() == 'true'
    SAML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'saml')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    # Production security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
