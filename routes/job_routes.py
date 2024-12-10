from flask import Blueprint, jsonify
from models import Job
from services.geo_service import get_nearby_jobs

job_bp = Blueprint('job', __name__)

@job_bp.route('/api/jobs/nearby')
def nearby_jobs():
    """API endpoint for nearby jobs search"""
    try:
        latitude = float(request.args.get('lat'))
        longitude = float(request.args.get('lng'))
        radius = float(request.args.get('radius', 15))
        
        jobs = get_nearby_jobs(latitude, longitude, radius)
        return jsonify([{
            'id': job.id,
            'title': job.title,
            'description': job.description,
            'location': job.location,
            'distance': job.distance,
            'company': job.employer.company_name
        } for job in jobs])
    
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid parameters'}), 400
