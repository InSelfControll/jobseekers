from extensions import db
from datetime import datetime
from sqlalchemy import Text
from .base import Base

class Application(Base):
    """Model representing a job application via Telegram bot"""
    __tablename__ = 'application'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id', name='fk_application_job'), nullable=False)
    telegram_user_id = db.Column(db.String(50), nullable=False)
    cover_letter = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resume_path = db.Column(db.String(512))
    
    # Relationships 
    messages = db.relationship('Message', backref='application', lazy='select')
    job = db.relationship('Job', back_populates='applications')

    # Status constants
    STATUS_PENDING = 'pending'
    STATUS_REVIEWING = 'reviewing'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_WITHDRAWN = 'withdrawn'
    
    VALID_STATUSES = [
        STATUS_PENDING,
        STATUS_REVIEWING,
        STATUS_ACCEPTED,
        STATUS_REJECTED,
        STATUS_WITHDRAWN
    ]

    def __init__(self, **kwargs):
        super(Application, self).__init__(**kwargs)
        if not self.status:
            self.status = self.STATUS_PENDING

    def update_status(self, new_status: str) -> None:
        """Update application status if valid"""
        if new_status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(self.VALID_STATUSES)}")
        self.status = new_status
        self.updated_at = datetime.utcnow()

    def add_message(self, content: str, sender_type: str) -> 'Message':
        """Add a new message to the application"""
        from .message import Message
        if sender_type not in ['employer', 'candidate']:
            raise ValueError("sender_type must be either 'employer' or 'candidate'")
        
        message = Message(
            application_id=self.id,
            content=content, 
            sender_type=sender_type
        )
        db.session.add(message)
        return message

    def get_messages(self, limit: int = None):
        """Retrieve messages for the application"""
        query = Message.query.filter_by(application_id=self.id).order_by(Message.created_at.desc())
        if limit:
            query = query.limit(limit)
        return query.all()

    def is_active(self) -> bool:
        """Check if the application is still active"""
        return self.status in [self.STATUS_PENDING, self.STATUS_REVIEWING]

    def can_withdraw(self) -> bool:
        """Check if the application can be withdrawn"""
        return self.status in [self.STATUS_PENDING, self.STATUS_REVIEWING]

    def withdraw(self) -> bool:
        """Withdraw the application if possible"""
        if self.can_withdraw():
            self.update_status(self.STATUS_WITHDRAWN)
            return True
        return False

    def __repr__(self):
        return f'<Application {self.id} - Job {self.job_id} - TelegramUser {self.telegram_user_id}>'
