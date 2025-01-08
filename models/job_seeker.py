from extensions import db
from datetime import datetime
from sqlalchemy import JSON, Text
from .base import Base

class JobSeeker(Base):
    """Model representing job seekers using the Telegram bot"""
    __tablename__ = 'job_seeker'

    id = db.Column(db.Integer, primary_key=True)
    telegram_user_id = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    resume_path = db.Column(db.String(512))
    preferred_location = db.Column(db.String(128))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    skills = db.Column(JSON)
    job_preferences = db.Column(JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    applications = db.relationship('Application',
                                 primaryjoin="and_(JobSeeker.telegram_user_id==foreign(Application.telegram_user_id))",
                                 backref='job_seeker',
                                 lazy='select',
                                 viewonly=True)

    def __init__(self, telegram_user_id, **kwargs):
        super(JobSeeker, self).__init__(**kwargs)
        self.telegram_user_id = telegram_user_id
        self.job_preferences = kwargs.get('job_preferences', {
            'max_distance': 50,  # km
            'job_types': [],
            'salary_min': None,
            'remote_only': False
        })
        self.skills = kwargs.get('skills', [])

    def update_location(self, latitude: float, longitude: float, location_name: str = None):
        """Update job seeker's preferred location"""
        self.latitude = latitude
        self.longitude = longitude
        if location_name:
            self.preferred_location = location_name
        self.updated_at = datetime.utcnow()

    def update_preferences(self, preferences: dict):
        """Update job preferences"""
        self.job_preferences.update(preferences)
        self.updated_at = datetime.utcnow()

    def update_skills(self, skills: list):
        """Update job seeker's skills"""
        self.skills = skills
        self.updated_at = datetime.utcnow()

    def log_activity(self):
        """Update last active timestamp"""
        self.last_active = datetime.utcnow()

    def get_matching_jobs(self, limit: int = 10):
        """Get matching jobs based on seeker's preferences and location"""
        from .job import Job
        from sqlalchemy import and_
        
        query = Job.query.filter(Job.status == Job.STATUS_ACTIVE)

        # Apply location filter if coordinates are available
        if self.latitude and self.longitude and self.job_preferences.get('max_distance'):
            max_distance = self.job_preferences['max_distance']
            query = query.filter(Job.calculate_distance(
                self.latitude,
                self.longitude
            ) <= max_distance)

        # Apply remote filter
        if self.job_preferences.get('remote_only'):
            query = query.filter(Job.is_remote == True)

        # Apply job type filter
        if self.job_preferences.get('job_types'):
            query = query.filter(Job.job_type.in_(self.job_preferences['job_types']))

        # Apply salary filter
        if self.job_preferences.get('salary_min'):
            query = query.filter(Job.salary_min >= self.job_preferences['salary_min'])

        return query.limit(limit).all()

    def __repr__(self):
        return f'<JobSeeker {self.telegram_user_id}>'
