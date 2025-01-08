from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models.employer import Employer
from models.job import Job, JobApplication
from models.message import Message
from extensions import db
from datetime import datetime
from core.db_utils import session_scope, safe_get, cleanup_session
from services.logging_service import logging_service
from jinja2.exceptions import TemplateError

logger = logging_service.get_structured_logger(__name__)
employer = Blueprint('employer', __name__)

@employer.route('/dashboard')
@login_required
def dashboard():
    # Get active jobs count
    active_jobs = len([job for job in current_user.jobs if job.is_active])
    
    # Get total applications count
    total_applications = sum(len(job.applications) for job in current_user.jobs)
    
    # Get jobs with recent applications
    jobs = current_user.jobs
    
    return render_template('employer/dashboard.html',
                         active_jobs=active_jobs,
                         total_applications=total_applications,
                         jobs=jobs)

@employer.route('/jobs', methods=['GET'])
@login_required
def jobs():
    return render_template('employer/jobs.html', jobs=current_user.jobs)

@employer.route('/jobs/new', methods=['POST'])
@login_required
def new_job():
    try:
        title = request.form.get('title')
        description = request.form.get('description')
        location = request.form.get('location')
        
        if not all([title, description, location]):
            flash('Please fill in all required fields', 'error')
            return redirect(url_for('employer.jobs'))
        
        with session_scope() as session:
            job = Job(
                title=title,
                description=description,
                location=location,
                employer_id=current_user.id,
                created_at=datetime.utcnow()
            )
            session.add(job)
            logger.info(f'New job created by employer {current_user.id}')
            flash('Your job posting has been successfully created', 'success')
            
        return redirect(url_for('employer.jobs'))
    except Exception as e:
        logger.error(f'Error creating new job: {str(e)}')
        flash('An error occurred while creating the job posting. Please try again.', 'error')
        return render_template('errors/500.html'), 500

@employer.route('/jobs/<int:job_id>/edit', methods=['POST'])
@login_required
def edit_job(job_id):
    try:
        job = safe_get(Job, job_id)
        if not job:
            flash('Job posting not found', 'error')
            return redirect(url_for('employer.jobs'))
        
        if job.employer_id != current_user.id:
            logger.warning(f'Unauthorized job edit attempt by user {current_user.id}')
            flash('You do not have permission to edit this job posting', 'error')
            return redirect(url_for('employer.jobs'))
        
        with session_scope() as session:
            job.title = request.form.get('title')
            job.description = request.form.get('description')
            job.location = request.form.get('location')
            logger.info(f'Job {job_id} updated by employer {current_user.id}')
            flash('Your job posting has been successfully updated', 'success')
            
        return redirect(url_for('employer.jobs'))
    except Exception as e:
        logger.error(f'Error updating job {job_id}: {str(e)}')
        flash('An error occurred while updating the job posting. Please try again.', 'error')
        return render_template('errors/500.html'), 500
@employer.route('/jobs/<int:job_id>/delete', methods=['POST'])
@login_required
def delete_job(job_id):
    try:
        job = safe_get(Job, job_id)
        if not job:
            flash('Job posting not found', 'error')
            return redirect(url_for('employer.jobs'))
        
        if job.employer_id != current_user.id:
            logger.warning(f'Unauthorized job deletion attempt by user {current_user.id}')
            flash('You do not have permission to delete this job posting', 'error')
            return redirect(url_for('employer.jobs'))
        
        with session_scope() as session:
            session.delete(job)
            logger.info(f'Job {job_id} deleted by employer {current_user.id}')
            flash('Your job posting has been successfully deleted', 'success')
            
        return redirect(url_for('employer.jobs'))
    except Exception as e:
        logger.error(f'Error deleting job {job_id}: {str(e)}')
        flash('An error occurred while deleting the job posting. Please try again.', 'error')
        return render_template('errors/500.html'), 500

@bp.route('/applications')
@login_required
def applications():
    """View all applications across employer's jobs."""
    try:
        # Get all applications across all jobs
        all_applications = []
        for job in current_user.jobs:
            all_applications.extend(job.applications)
            
        # Sort applications by date, newest first
        all_applications.sort(key=lambda x: x.created_at, reverse=True)
        
        return render_template(
            'employer/applications.html',
            applications=all_applications
        )
    except Exception as e:
        logger.error(f"Error fetching applications: {str(e)}")
        return render_template('errors/500.html'), 500



@employer.route('/applications/<int:app_id>/update', methods=['POST'])
@login_required
def update_application(app_id):
    try:
        application = safe_get(JobApplication, app_id)
        if not application:
            flash('Application not found', 'error')
            return redirect(url_for('employer.applications'))
        
        if application.job.employer_id != current_user.id:
            logger.warning(f'Unauthorized application update attempt by user {current_user.id}')
            flash('You do not have permission to update this application', 'error')
            return redirect(url_for('employer.applications'))
        
        new_status = request.form.get('status')
        if new_status in ['pending', 'accepted', 'rejected']:
            with session_scope() as session:
                application.status = new_status
                logger.info(f'Application {app_id} status updated to {new_status}')
                flash('Application status has been successfully updated', 'success')
        else:
            flash('Invalid application status', 'error')
        
        return redirect(url_for('employer.applications'))
    except Exception as e:
        logger.error(f'Error updating application {app_id}: {str(e)}')
        flash('An error occurred while updating the application. Please try again.', 'error')
        return render_template('errors/500.html'), 500
@employer.route('/applications/<int:app_id>/message', methods=['POST'])
@login_required
def send_message(app_id):
    try:
        application = safe_get(JobApplication, app_id)
        if not application:
            flash('Application not found', 'error')
            return redirect(url_for('employer.applications'))
        
        if application.job.employer_id != current_user.id:
            logger.warning(f'Unauthorized message attempt by user {current_user.id}')
            flash('You do not have permission to send messages for this application', 'error')
            return redirect(url_for('employer.applications'))
        
        message_content = request.form.get('message')
        if not message_content:
            flash('Message content cannot be empty', 'error')
            return redirect(url_for('employer.applications'))
        
        with session_scope() as session:
            message = Message(
                content=message_content,
                sender_type='employer',
                application_id=app_id,
                created_at=datetime.utcnow()
            )
            session.add(message)
            logger.info(f'Message sent for application {app_id}')
            flash('Your message has been sent successfully', 'success')
        
        return redirect(url_for('employer.applications'))
    except Exception as e:
        logger.error(f'Error sending message for application {app_id}: {str(e)}')
        flash('An error occurred while sending the message. Please try again.', 'error')
        return render_template('errors/500.html'), 500

@employer.teardown_request
def cleanup(exception=None):
    if exception:
        logger.error(f'Request error: {str(exception)}')
        db.session.rollback()
    cleanup_session()