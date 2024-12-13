
from extensions import db
from models import Job

def add_test_columns():
    # Add new columns to Job table
    db.engine.execute('''
        ALTER TABLE job 
        ADD COLUMN has_test BOOLEAN DEFAULT FALSE,
        ADD COLUMN test_content TEXT,
        ADD COLUMN test_duration INTEGER
    ''')

if __name__ == '__main__':
    add_test_columns()
