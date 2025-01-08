import contextlib
from typing import Generator, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from services.logging_service import logging_service

logger = logging_service.get_structured_logger(__name__)

@contextlib.contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    session = db.session
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        logger.error(f"Database error occurred: {str(e)}")
        session.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

def safe_commit() -> bool:
    """Safely commit the current transaction."""
    try:
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        logger.error(f"Failed to commit transaction: {str(e)}")
        db.session.rollback()
        return False

def safe_add(obj: Any) -> bool:
    """Safely add an object to the session."""
    try:
        db.session.add(obj)
        return True
    except SQLAlchemyError as e:
        logger.error(f"Failed to add object to session: {str(e)}")
        db.session.rollback()
        return False

def safe_delete(obj: Any) -> bool:
    """Safely delete an object from the session."""
    try:
        db.session.delete(obj)
        return True
    except SQLAlchemyError as e:
        logger.error(f"Failed to delete object from session: {str(e)}")
        db.session.rollback()
        return False

def safe_get(model: Any, id: int) -> Optional[Any]:
    """Safely get an object by ID."""
    try:
        return db.session.get(model, id)
    except SQLAlchemyError as e:
        logger.error(f"Failed to get object: {str(e)}")
        return None

def cleanup_session() -> None:
    """Clean up the current session."""
    try:
        db.session.remove()
    except SQLAlchemyError as e:
        logger.error(f"Failed to cleanup session: {str(e)}")

def rollback_session() -> None:
    """Rollback the current session."""
    try:
        db.session.rollback()
    except SQLAlchemyError as e:
        logger.error(f"Failed to rollback session: {str(e)}")

def refresh_object(obj: Any) -> bool:
    """Refresh an object from the database."""
    try:
        db.session.refresh(obj)
        return True
    except SQLAlchemyError as e:
        logger.error(f"Failed to refresh object: {str(e)}")
        return False

def flush_session() -> bool:
    """Flush the current session."""
    try:
        db.session.flush()
        return True
    except SQLAlchemyError as e:
        logger.error(f"Failed to flush session: {str(e)}")
        return False