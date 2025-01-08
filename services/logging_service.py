import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
import json

class LoggingService:
    def __init__(self):
        self.logger = logging.getLogger()
        self.log_level = self._get_log_level()
        self.log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        self.structured_format = '%(asctime)s - %(name)s - %(levelname)s - %(structured_data)s - %(message)s'
        self.log_dir = 'logs'
        self.max_bytes = 10 * 1024 * 1024  # 10MB
        self.backup_count = 5

    def _get_log_level(self):
        """Get log level based on environment"""
        env = os.getenv('FLASK_ENV', 'development').lower()
        log_levels = {
            'development': logging.DEBUG,
            'testing': logging.INFO,
            'staging': logging.INFO,
            'production': logging.WARNING
        }
        return log_levels.get(env, logging.INFO)

    def setup_logging(self):
        """Configure logging with both console and file handlers"""
        self.logger.setLevel(self.log_level)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # Setup console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(self.log_format))
        self.logger.addHandler(console_handler)

        # Setup file handler
        self._setup_file_handler()

        return self.logger

    def _setup_file_handler(self):
        """Setup rotating file handler"""
        try:
            if not os.path.exists(self.log_dir):
                os.makedirs(self.log_dir)

            log_file = os.path.join(self.log_dir, 'app.log')
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count
            )
            file_handler.setFormatter(logging.Formatter(self.structured_format))
            self.logger.addHandler(file_handler)
        except Exception as e:
            self.logger.error(f"Failed to setup file handler: {e}")

    def get_structured_logger(self, name):
        """Get a logger instance with structured logging support"""
        logger = logging.getLogger(name)
        logger.setLevel(self.log_level)
        return StructuredLogger(logger)

class StructuredLogger:
    def __init__(self, logger):
        self.logger = logger

    def _format_structured_data(self, data):
        """Format structured data as JSON string"""
        try:
            return json.dumps(data) if data else '{}'
        except Exception:
            return str(data)

    def _log(self, level, msg, structured_data=None, *args, **kwargs):
        """Generic logging method with structured data support"""
        extra = kwargs.get('extra', {})
        extra['structured_data'] = self._format_structured_data(structured_data)
        kwargs['extra'] = extra
        getattr(self.logger, level)(msg, *args, **kwargs)

    def debug(self, msg, structured_data=None, *args, **kwargs):
        self._log('debug', msg, structured_data, *args, **kwargs)

    def info(self, msg, structured_data=None, *args, **kwargs):
        self._log('info', msg, structured_data, *args, **kwargs)

    def warning(self, msg, structured_data=None, *args, **kwargs):
        self._log('warning', msg, structured_data, *args, **kwargs)

    def error(self, msg, structured_data=None, *args, **kwargs):
        self._log('error', msg, structured_data, *args, **kwargs)

    def critical(self, msg, structured_data=None, *args, **kwargs):
        self._log('critical', msg, structured_data, *args, **kwargs)

# Initialize logging service
logging_service = LoggingService()