from datetime import datetime
from sqlalchemy import Text
from extensions import db
from .base import Base

VALID_SENDER_TYPES = ['employer', 'job_seeker']

class Message(Base):
    """Model representing messages in job applications"""
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id', name='fk_message_application'), nullable=False)
    sender_type = db.Column(db.String(20))  # 'employer' or 'job_seeker'
    content = db.Column(Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, application_id, sender_type, content):
        if sender_type not in VALID_SENDER_TYPES:
            raise ValueError(f"Invalid sender type. Must be one of: {', '.join(VALID_SENDER_TYPES)}")
        self.application_id = application_id
        self.sender_type = sender_type
        self.content = content