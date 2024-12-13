from extensions import db
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON

class Employer(UserMixin, db.Model):
    __tablename__ = 'employer'
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    jobs = db.relationship('Job', backref='employer', lazy='select')

class Job(db.Model):
    __tablename__ = 'job'
    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey('employer.id'), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(128), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')
    has_test = db.Column(db.Boolean, default=False)
    test_content = db.Column(db.Text)
    test_duration = db.Column(db.Integer) # in minutes
    applications = db.relationship('Application', backref='job', lazy='select')

class JobSeeker(db.Model):
    __tablename__ = 'job_seeker'
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(128), unique=True, nullable=False)
    whatsapp_number = db.Column(db.String(20))
    telegram_username = db.Column(db.String(128))
    full_name = db.Column(db.String(128), nullable=False)
    resume_path = db.Column(db.String(256))
    skills = db.Column(JSON)
    location = db.Column(db.String(128))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    applications = db.relationship('Application', backref='job_seeker', lazy='select')

class Application(db.Model):
    __tablename__ = 'application'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    job_seeker_id = db.Column(db.Integer, db.ForeignKey('job_seeker.id'), nullable=False)
    cover_letter = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('Message', backref='application', lazy='select')

class Message(db.Model):
    __tablename__ = 'message'
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False)
    sender_type = db.Column(db.String(20))  # 'employer' or 'job_seeker'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
