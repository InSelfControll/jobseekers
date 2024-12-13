
from extensions import db
from models import Job, JobSeeker
from sqlalchemy import Boolean, Text, Integer, String

def add_test_columns():
    # Add new columns to Job table
    with db.engine.connect() as connection:
        connection.execute('''
            ALTER TABLE job 
            ADD COLUMN IF NOT EXISTS has_test BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS test_content TEXT,
            ADD COLUMN IF NOT EXISTS test_duration INTEGER;
            
            ALTER TABLE job_seeker
            ADD COLUMN IF NOT EXISTS whatsapp_number VARCHAR(20),
            ADD COLUMN IF NOT EXISTS telegram_username VARCHAR(128);
        ''')
        connection.commit()

if __name__ == '__main__':
    add_test_columns()
