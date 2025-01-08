import logging
from typing import Optional, List, Type, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app
from extensions import db, get_tenant_db_session

logger = logging.getLogger(__name__)

class DatabaseService:
    """Centralized service for handling database operations"""
    
    def __init__(self):
        self.db = db
        
    def get_session(self) -> Session:
        """Get the current database session"""
        return self.db.session
        
    def get_tenant_session(self, tenant_id: int) -> Session:
        """Get a database session for a specific tenant"""
        return get_tenant_db_session(tenant_id)
        
    def add(self, model: db.Model) -> None:
        """Add a new record to the database"""
        try:
            self.db.session.add(model)
            self.db.session.commit()
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"Error adding record: {str(e)}")
            raise
            
    def update(self, model: db.Model) -> None:
        """Update an existing record in the database"""
        try:
            self.db.session.commit()
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"Error updating record: {str(e)}")
            raise
            
    def delete(self, model: db.Model) -> None:
        """Delete a record from the database"""
        try:
            self.db.session.delete(model)
            self.db.session.commit()
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"Error deleting record: {str(e)}")
            raise
            
    def get_by_id(self, model_class: Type[db.Model], record_id: int) -> Optional[db.Model]:
        """Get a record by its ID"""
        try:
            return model_class.query.get(record_id)
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving record: {str(e)}")
            raise
            
    def get_all(self, model_class: Type[db.Model]) -> List[db.Model]:
        """Get all records of a specific model"""
        try:
            return model_class.query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving records: {str(e)}")
            raise
            
    def query(self, model_class: Type[db.Model]) -> Any:
        """Get a query object for a specific model"""
        return model_class.query
        
    def begin_transaction(self) -> None:
        """Begin a new database transaction"""
        self.db.session.begin()
        
    def commit_transaction(self) -> None:
        """Commit the current transaction"""
        try:
            self.db.session.commit()
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"Error committing transaction: {str(e)}")
            raise
            
    def rollback_transaction(self) -> None:
        """Rollback the current transaction"""
        self.db.session.rollback()
        
    def execute_in_transaction(self, callback) -> Any:
        """Execute operations within a transaction"""
        try:
            result = callback()
            self.db.session.commit()
            return result
        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Transaction failed: {str(e)}")
            raise
            
    def bulk_save(self, models: List[db.Model]) -> None:
        """Save multiple records in a single transaction"""
        try:
            self.db.session.bulk_save_objects(models)
            self.db.session.commit()
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"Error in bulk save: {str(e)}")
            raise
            
    def create_tables(self) -> None:
        """Create all database tables"""
        try:
            self.db.create_all()
        except SQLAlchemyError as e:
            logger.error(f"Error creating tables: {str(e)}")
            raise