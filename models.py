from extensions import Base
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON
import uuid

class Employer(UserMixin, Base):
    __tablename__ = 'employer'
    id = Column(Integer, primary_key=True)
    company_name = Column(String(128), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256))
    created_at = Column(DateTime, default=datetime.utcnow)
    jobs = relationship('Job', backref='employer', lazy='select')

class Job(Base):
    __tablename__ = 'job'
    id = Column(Integer, primary_key=True)
    employer_id = Column(Integer, ForeignKey('employer.id'), nullable=False)
    title = Column(String(128), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(128), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default='active')
    applications = relationship('Application', backref='job', lazy='select')

class JobSeeker(Base):
    __tablename__ = 'job_seeker'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(128), unique=True, nullable=False)
    full_name = Column(String(128), nullable=False)
    resume_path = Column(String(256))
    skills = Column(JSON)
    location = Column(String(128))
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    applications = relationship('Application', backref='job_seeker', lazy='select')

class Application(Base):
    __tablename__ = 'application'
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('job.id'), nullable=False)
    job_seeker_id = Column(Integer, ForeignKey('job_seeker.id'), nullable=False)
    cover_letter = Column(Text)
    status = Column(String(20), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    messages = relationship('Message', backref='application', lazy='select')

class Message(Base):
    __tablename__ = 'message'
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey('application.id'), nullable=False)
    sender_type = Column(String(20))  # 'employer' or 'job_seeker'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
