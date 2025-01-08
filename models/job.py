from extensions import db
from datetime import datetime
from sqlalchemy import JSON, Text, func
from .base import Base
from math import radians, cos, sin, asin, sqrt

class Job(Base):
    __tablename__ = 'job'

    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey('employer.id', name='fk_job_employer'), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(128), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')
    job_type = db.Column(db.String(50))  # full-time, part-time, contract, etc
    is_remote = db.Column(db.Boolean, default=False)
    salary_min = db.Column(db.Integer)
    salary_max = db.Column(db.Integer)
    required_skills = db.Column(JSON)
    preferred_skills = db.Column(JSON)
    experience_level = db.Column(db.String(50))  # entry, mid, senior
    
    # Relationships
    employer = db.relationship('Employer', back_populates='jobs')
    applications = db.relationship('Application', back_populates='job', lazy='select', cascade='all, delete-orphan')

    # Status constants
    STATUS_ACTIVE = 'active'
    STATUS_CLOSED = 'closed'
    STATUS_DRAFT = 'draft'
    STATUS_ARCHIVED = 'archived'
    
    VALID_STATUSES = [STATUS_ACTIVE, STATUS_CLOSED, STATUS_DRAFT, STATUS_ARCHIVED]

    def __init__(self, **kwargs):
        super(Job, self).__init__(**kwargs)
        if not self.status:
            self.status = self.STATUS_DRAFT

    @property
    def is_active(self):
        return self.status == self.STATUS_ACTIVE

    @property
    def is_closed(self):
        return self.status == self.STATUS_CLOSED

    @property
    def is_draft(self):
        return self.status == self.STATUS_DRAFT

    @property
    def is_archived(self):
        return self.status == self.STATUS_ARCHIVED

    def activate(self) -> None:
        """Activate the job posting"""
        self.update_status(self.STATUS_ACTIVE)

    def close(self) -> None:
        """Close the job posting"""
        self.update_status(self.STATUS_CLOSED)

    def archive(self) -> None:
        """Archive the job posting"""
        self.update_status(self.STATUS_ARCHIVED)

    def set_draft(self) -> None:
        """Set job posting as draft"""
        self.update_status(self.STATUS_DRAFT)
    def update_status(self, new_status: str) -> None:
        """Update job status if valid"""
        if new_status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(self.VALID_STATUSES)}")
        self.status = new_status

    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float = None, lon2: float = None):
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees)
        """
        if lat2 is None:
            # If lat2/lon2 not provided, reference to job's location
            return func.ST_Distance_Sphere(
                func.ST_MakePoint(Job.longitude, Job.latitude),
                func.ST_MakePoint(lon1, lat1)
            ) / 1000  # Convert meters to kilometers
        
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers
        return c * r

    @classmethod
    def search(cls, filters: dict = None, location: tuple = None, radius_km: float = None, 
              limit: int = 10, skills: list = None):
        """
        Search for jobs based on various criteria
        
        Args:
            filters (dict): Filtering criteria (status, job_type, etc)
            location (tuple): (latitude, longitude) pair
            radius_km (float): Search radius in kilometers
            limit (int): Maximum number of results
            skills (list): Required skills to match
            
        Returns:
            list: Matching Job objects
        """
        query = cls.query.filter_by(status=cls.STATUS_ACTIVE)

        if filters:
            for key, value in filters.items():
                if hasattr(cls, key) and value is not None:
                    query = query.filter(getattr(cls, key) == value)

        if location and radius_km:
            lat, lon = location
            distance = cls.calculate_distance(lat, lon)
            query = query.having(distance <= radius_km)
            query = query.order_by(distance)

        if skills:
            # Match any of the provided skills
            query = query.filter(cls.required_skills.contains(skills))

        return query.limit(limit).all()

    def matches_job_seeker(self, job_seeker) -> bool:
        """Check if job matches a job seeker's preferences"""
        # Check location preference if set
        if job_seeker.latitude and job_seeker.longitude:
            distance = self.calculate_distance(
                job_seeker.latitude,
                job_seeker.longitude,
                self.latitude,
                self.longitude
            )
            if distance > job_seeker.job_preferences.get('max_distance', float('inf')):
                return False

        # Check remote preference
        if job_seeker.job_preferences.get('remote_only') and not self.is_remote:
            return False

        # Check salary preference
        min_salary_pref = job_seeker.job_preferences.get('salary_min')
        if min_salary_pref and (not self.salary_min or self.salary_min < min_salary_pref):
            return False

        # Check skills match
        if job_seeker.skills and self.required_skills:
            seeker_skills = set(job_seeker.skills)
            required_skills = set(self.required_skills)
            if not required_skills.intersection(seeker_skills):
                return False

        return True

    def __repr__(self):
        return f'<Job {self.title}>'
