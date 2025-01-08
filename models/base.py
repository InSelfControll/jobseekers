from typing import ClassVar, Optional
from extensions import db

class Base(db.Model):
    """
    Base model class that serves as the foundation for all database entities.
    
    This abstract class provides common functionality and attributes that all models should inherit.
    It includes support for tenant-specific table names and SQLAlchemy configurations.
    
    Attributes:
        __abstract__ (bool): SQLAlchemy flag to mark this as an abstract base class
    """
    __abstract__: ClassVar[bool] = True

    @classmethod
    def __declare_last__(cls) -> None:
        """
        Hook called by SQLAlchemy after mappings are configured.
        
        This method is automatically invoked by SQLAlchemy after all 
        table configurations and relationships are set up.
        """
        pass
    
    @classmethod
    def get_tenant_specific_table_name(cls, tenant_id: str) -> str:
        """
        Generate a tenant-specific table name by prefixing the tenant ID.
        
        Args:
            tenant_id (str): The unique identifier for the tenant
            
        Returns:
            str: The tenant-specific table name in format '{tenant_id}_{table_name}'
        """
        return f"{tenant_id}_{cls.__tablename__}"