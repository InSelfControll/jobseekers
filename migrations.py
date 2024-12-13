
from extensions import db
from models import Job, JobSeeker
import sqlalchemy as sa
from sqlalchemy import inspect

def add_test_columns():
    inspector = inspect(db.engine)
    connection = db.engine.connect()
    
    with connection.begin():
        # Add columns to Job table if they don't exist
        existing_columns = [col['name'] for col in inspector.get_columns('job')]
        
        if 'has_test' not in existing_columns:
            connection.execute(sa.text('ALTER TABLE job ADD COLUMN has_test BOOLEAN DEFAULT FALSE'))
        
        if 'test_content' not in existing_columns:
            connection.execute(sa.text('ALTER TABLE job ADD COLUMN test_content TEXT'))
            
        if 'test_duration' not in existing_columns:
            connection.execute(sa.text('ALTER TABLE job ADD COLUMN test_duration INTEGER'))

if __name__ == '__main__':
    add_test_columns()
