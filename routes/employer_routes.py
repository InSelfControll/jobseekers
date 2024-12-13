
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import Job, Application, Message
from extensions import db
from services.geo_service import get_nearby_jobs

employer_bp = Blueprint('employer', __name__)

@employer_bp.route('/dashboard')
@login_required
def dashboard():
    jobs = Job.query.filter_by(employer_id=current_user.id).all()
    active_jobs = len([j for j in jobs if j.status == 'active'])
    total_applications = Application.query.join(Job).filter(
        Job.employer_id == current_user.id
    ).count()
    
    return render_template('employer/dashboard.html',
                         jobs=jobs,
                         active_jobs=active_jobs,
                         total_applications=total_applications)

@employer_bp.route('/jobs')
@login_required
def jobs():
    jobs = Job.query.filter_by(employer_id=current_user.id).all()
    return render_template('employer/jobs.html', jobs=jobs)

@employer_bp.route('/jobs/new', methods=['GET', 'POST'])
@login_required
def new_job():
    if request.method == 'POST':
        job = Job(
            employer_id=current_user.id,
            title=request.form['title'],
            description=request.form['description'],
            location=request.form['location'],
            latitude=float(request.form['latitude']),
            longitude=float(request.form['longitude'])
        )
        db.session.add(job)
        db.session.commit()
        flash('Job posted successfully!', 'success')
        return redirect(url_for('employer.jobs'))
    
    return render_template('employer/jobs.html', new_job=True)

@employer_bp.route('/applications')
@login_required
def applications():
    applications = Application.query.join(Job).filter(
        Job.employer_id == current_user.id
    ).all()
    return render_template('employer/applications.html', applications=applications)

@employer_bp.route('/application/<int:app_id>', methods=['POST'])
@login_required
def update_application(app_id):
    application = Application.query.get_or_404(app_id)
    if application.job.employer_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('employer.applications'))
    
    status = request.form.get('status')
    if status in ['accepted', 'rejected', 'pending']:
        application.status = status
        db.session.commit()
        
        # Get job seeker and send notification asynchronously
        job_seeker = application.job_seeker
        if job_seeker and job_seeker.telegram_id:
            from bot.telegram_bot import send_status_notification
            import asyncio
            try:
                asyncio.create_task(send_status_notification(
                    job_seeker.telegram_id,
                    application.job.title,
                    status
                ))
            except Exception as e:
                print(f"Failed to send notification: {e}")
        
        flash('Application status updated', 'success')
    
    return redirect(url_for('employer.applications'))

@employer_bp.route('/jobs/<int:job_id>/edit', methods=['POST'])
@login_required
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.employer_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('employer.jobs'))
    
    job.title = request.form['title']
    job.description = request.form['description']
    job.location = request.form['location']
    job.latitude = float(request.form['latitude'])
    job.longitude = float(request.form['longitude'])
    
    db.session.commit()
    flash('Job updated successfully!', 'success')
    return redirect(url_for('employer.jobs'))

@employer_bp.route('/jobs/<int:job_id>/delete', methods=['POST'])
@login_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.employer_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('employer.jobs'))
    
    db.session.delete(job)
    db.session.commit()
    flash('Job deleted successfully!', 'success')
    return redirect(url_for('employer.jobs'))

@employer_bp.route('/message/<int:app_id>', methods=['POST'])
@login_required
def send_message(app_id):
    application = Application.query.get_or_404(app_id)
    if application.job.employer_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('employer.applications'))
    
    message = Message(
        application_id=app_id,
        sender_type='employer',
        content=request.form['message']
    )
    db.session.add(message)
    db.session.commit()
    flash('Message sent', 'success')
    
    return redirect(url_for('employer.applications'))
