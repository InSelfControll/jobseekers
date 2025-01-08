from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from models.job import Job
from extensions import db
from http import HTTPStatus
from sqlalchemy.exc import SQLAlchemyError
from core.db_utils import session_scope, safe_get, safe_add, safe_delete
from services.logging_service import logging_service

logger = logging_service.get_structured_logger(__name__)
job_bp = Blueprint('job', __name__)

@job_bp.route('/jobs', methods=['GET'])
def list_jobs():
    try:
        status = request.args.get('status', 'active')
        if status not in Job.VALID_STATUSES:
            logger.warning(f'Invalid job status requested: {status}')
            return jsonify({'error': 'Please select a valid job status'}), HTTPStatus.BAD_REQUEST
            
        with session_scope() as session:
            jobs = session.query(Job).filter_by(status=status).all()
            return jsonify([{
                'id': job.id,
                'title': job.title,
                'description': job.description,
                'location': job.location,
                'latitude': job.latitude,
                'longitude': job.longitude,
                'status': job.status,
                'created_at': job.created_at.isoformat(),
                'employer_id': job.employer_id
            } for job in jobs]), HTTPStatus.OK
    except SQLAlchemyError as e:
        logger.error(f'Database error while listing jobs: {str(e)}')
        return render_template('errors/500.html'), HTTPStatus.INTERNAL_SERVER_ERROR
    except Exception as e:
        logger.error(f'Unexpected error while listing jobs: {str(e)}')
        return render_template('errors/500.html'), HTTPStatus.INTERNAL_SERVER_ERROR
@job_bp.route('/jobs', methods=['POST'])
@login_required
def create_job():
    try:
        if not current_user.is_employer:
            logger.warning(f'Non-employer user {current_user.id} attempted to create a job')
            return jsonify({'error': 'You must be registered as an employer to create job listings'}), HTTPStatus.FORBIDDEN

        data = request.get_json()
        required_fields = ['title', 'description', 'location']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            logger.warning(f'Missing fields in job creation: {missing_fields}')
            return jsonify({'error': 'Please provide all required information for the job listing'}), HTTPStatus.BAD_REQUEST

        with session_scope() as session:
            job = Job(
                employer_id=current_user.id,
                title=data['title'],
                description=data['description'],
                location=data['location'],
                latitude=data.get('latitude'),
                longitude=data.get('longitude'),
                status=data.get('status', Job.STATUS_DRAFT)
            )

            if not safe_add(job):
                logger.error('Failed to add new job to database')
                return render_template('errors/500.html'), HTTPStatus.INTERNAL_SERVER_ERROR

            return jsonify({
                'id': job.id,
                'title': job.title,
                'description': job.description,
                'location': job.location,
                'latitude': job.latitude,
                'longitude': job.longitude,
                'status': job.status,
                'created_at': job.created_at.isoformat(),
                'employer_id': job.employer_id
            }), HTTPStatus.CREATED
    except SQLAlchemyError as e:
        logger.error(f'Database error while creating job: {str(e)}')
        return render_template('errors/500.html'), HTTPStatus.INTERNAL_SERVER_ERROR
    except Exception as e:
        logger.error(f'Unexpected error while creating job: {str(e)}')
        return render_template('errors/500.html'), HTTPStatus.INTERNAL_SERVER_ERROR
@job_bp.route('/jobs/<int:job_id>', methods=['GET'])
def get_job(job_id):
    try:
        job = safe_get(Job, job_id)
        if not job:
            logger.warning(f'Job not found with ID: {job_id}')
            return jsonify({'error': 'The requested job listing could not be found'}), HTTPStatus.NOT_FOUND

        return jsonify({
            'id': job.id,
            'title': job.title,
            'description': job.description,
            'location': job.location,
            'latitude': job.latitude,
            'longitude': job.longitude,
            'status': job.status,
            'created_at': job.created_at.isoformat(),
            'employer_id': job.employer_id
        }), HTTPStatus.OK
    except SQLAlchemyError as e:
        logger.error(f'Database error while retrieving job {job_id}: {str(e)}')
        return render_template('errors/500.html'), HTTPStatus.INTERNAL_SERVER_ERROR
    except Exception as e:
        logger.error(f'Unexpected error while retrieving job {job_id}: {str(e)}')
        return render_template('errors/500.html'), HTTPStatus.INTERNAL_SERVER_ERROR
@job_bp.route('/jobs/<int:job_id>', methods=['PUT'])
@login_required
def update_job(job_id):
    try:
        with session_scope() as session:
            job = safe_get(Job, job_id)
            if not job:
                logger.warning(f'Job not found for update with ID: {job_id}')
                return jsonify({'error': 'The job listing you are trying to update could not be found'}), HTTPStatus.NOT_FOUND
            
            if current_user.id != job.employer_id:
                logger.warning(f'Unauthorized job update attempt by user {current_user.id} for job {job_id}')
                return jsonify({'error': 'You are not authorized to update this job listing'}), HTTPStatus.FORBIDDEN

            data = request.get_json()
            
            if 'title' in data:
                job.title = data['title']
            if 'description' in data:
                job.description = data['description']
            if 'location' in data:
                job.location = data['location']
            if 'latitude' in data:
                job.latitude = data['latitude']
            if 'longitude' in data:
                job.longitude = data['longitude']
            if 'status' in data:
                if data['status'] not in Job.VALID_STATUSES:
                    logger.warning(f'Invalid status update attempt: {data["status"]}')
                    return jsonify({'error': 'Please select a valid job status'}), HTTPStatus.BAD_REQUEST
                job.status = data['status']

            return jsonify({
                'id': job.id,
                'title': job.title,
                'description': job.description,
                'location': job.location,
                'latitude': job.latitude,
                'longitude': job.longitude,
                'status': job.status,
                'created_at': job.created_at.isoformat(),
                'employer_id': job.employer_id
            }), HTTPStatus.OK
    except SQLAlchemyError as e:
        logger.error(f'Database error while updating job {job_id}: {str(e)}')
        return render_template('errors/500.html'), HTTPStatus.INTERNAL_SERVER_ERROR
    except Exception as e:
        logger.error(f'Unexpected error while updating job {job_id}: {str(e)}')
        return render_template('errors/500.html'), HTTPStatus.INTERNAL_SERVER_ERROR
@job_bp.route('/jobs/<int:job_id>', methods=['DELETE'])
@login_required
def delete_job(job_id):
    try:
        with session_scope() as session:
            job = safe_get(Job, job_id)
            if not job:
                logger.warning(f'Job not found for deletion with ID: {job_id}')
                return jsonify({'error': 'The job listing you are trying to delete could not be found'}), HTTPStatus.NOT_FOUND
            
            if current_user.id != job.employer_id:
                logger.warning(f'Unauthorized job deletion attempt by user {current_user.id} for job {job_id}')
                return jsonify({'error': 'You are not authorized to delete this job listing'}), HTTPStatus.FORBIDDEN

            if not safe_delete(job):
                logger.error(f'Failed to delete job {job_id}')
                return render_template('errors/500.html'), HTTPStatus.INTERNAL_SERVER_ERROR

            return '', HTTPStatus.NO_CONTENT
    except SQLAlchemyError as e:
        logger.error(f'Database error while deleting job {job_id}: {str(e)}')
        return render_template('errors/500.html'), HTTPStatus.INTERNAL_SERVER_ERROR
    except Exception as e:
        logger.error(f'Unexpected error while deleting job {job_id}: {str(e)}')
        return render_template('errors/500.html'), HTTPStatus.INTERNAL_SERVER_ERROR