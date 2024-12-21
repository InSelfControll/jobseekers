from extensions import db
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import JSON, Text

class Base(db.Model):
    """Base model class for all entities"""
    __abstract__ = True

    @classmethod
    def __declare_last__(cls):
        """Called after mappings are configured"""
        pass
    
    @classmethod
    def get_tenant_specific_table_name(cls, tenant_id):
        """Get table name specific to a tenant"""
        return f"{tenant_id}_{cls.__tablename__}"

class Employer(UserMixin, Base):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    company_name = db.Column(db.String(120), nullable=False)
    sso_domain = db.Column(db.String(255), unique=True)
    sso_provider = db.Column(db.String(50))
    sso_config = db.Column(JSON)
    company_domain = db.Column(db.String(120))
    tenant_id = db.Column(db.String(50), unique=True)  # Unique identifier for company's database
    db_name = db.Column(db.String(120))  # Name of company's database
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    is_owner = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    email_footer = db.Column(db.Text)
    notify_new_applications = db.Column(db.Boolean, default=True)
    notify_status_changes = db.Column(db.Boolean, default=True)
    ssl_enabled = db.Column(db.Boolean, default=False)
    ssl_cert_path = db.Column(db.String(512))
    ssl_key_path = db.Column(db.String(512))
    ssl_expiry = db.Column(db.DateTime)
    domain_verification_date = db.Column(db.DateTime)
    domain_verified = db.Column(db.Boolean, default=False)
    jobs = db.relationship('Job', backref='employer', lazy='select')

class Job(Base):
    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey('employer.id', name='fk_job_employer'), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(128), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')
    applications = db.relationship('Application', backref='job', lazy='select')

class JobSeeker(Base):
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(128), unique=True, nullable=False)
    full_name = db.Column(db.String(128), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    resume_path = db.Column(db.String(256))
    skills = db.Column(JSON)
    location = db.Column(db.String(128))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    applications = db.relationship('Application', 
                               backref=db.backref('job_seeker', lazy='select'),
                               lazy='select')

class Application(Base):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id', name='fk_application_job'), nullable=False)
    job_seeker_id = db.Column(db.Integer, db.ForeignKey('job_seeker.id', name='fk_application_job_seeker'), nullable=False)
    cover_letter = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('Message', backref='application', lazy='select')

class Message(Base):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id', name='fk_message_application'), nullable=False)
    sender_type = db.Column(db.String(20))  # 'employer' or 'job_seeker'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
