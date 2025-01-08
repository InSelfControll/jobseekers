import logging
from typing import Optional, Any
from functools import wraps
from extensions import db, get_tenant_db_session

logger = logging.getLogger(__name__)

class BaseCommand:
    def __init__(self):
        self.db = db
        self._tenant_session = None
        self.logger = logger

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.handle_error(exc_val)
        if self._tenant_session:
            self._tenant_session.close()

    @staticmethod
    def handle_command(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            try:
                return await func(self, *args, **kwargs)
            except Exception as e:
                await self.handle_error(e)
                return None
        return wrapper

    async def handle_error(self, error: Exception) -> None:
        """Handle errors in a consistent way across all commands"""
        error_type = type(error).__name__
        error_message = str(error)
        
        self.logger.error(f"Command error occurred: {error_type} - {error_message}")
        
        if isinstance(error, (ValueError, TypeError)):
            self.logger.warning(f"Validation error: {error_message}")
        elif isinstance(error, db.SQLAlchemyError):
            self.logger.error(f"Database error: {error_message}")
            await self.rollback_transaction()
        else:
            self.logger.error(f"Unexpected error: {error_message}", exc_info=True)

    async def get_db_session(self, tenant_id: Optional[str] = None):
        """Get database session based on tenant ID"""
        try:
            if tenant_id:
                self._tenant_session = get_tenant_db_session(tenant_id)
                return self._tenant_session
            return self.db.session
        except Exception as e:
            await self.handle_error(e)
            return None

    async def commit_transaction(self) -> bool:
        """Commit the current transaction"""
        try:
            if self._tenant_session:
                self._tenant_session.commit()
            else:
                self.db.session.commit()
            return True
        except Exception as e:
            await self.handle_error(e)
            return False

    async def rollback_transaction(self) -> None:
        """Rollback the current transaction"""
        try:
            if self._tenant_session:
                self._tenant_session.rollback()
            else:
                self.db.session.rollback()
        except Exception as e:
            self.logger.error(f"Error during rollback: {e}")

    def log_command_execution(self, command_name: str, args: Any = None) -> None:
        """Log command execution with relevant details"""
        self.logger.info(f"Executing command: {command_name}")
        if args:
            self.logger.debug(f"Command arguments: {args}")

    async def validate_input(self, data: Any, required_fields: list = None) -> bool:
        """Validate input data against required fields"""
        try:
            if required_fields:
                if not all(field in data for field in required_fields):
                    missing_fields = [field for field in required_fields if field not in data]
                    raise ValueError(f"Missing required fields: {missing_fields}")
            return True
        except Exception as e:
            await self.handle_error(e)
            return False