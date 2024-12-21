from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from secops.sec import csrf_protected
import json
from extensions import db
from models import Job

job_bp = Blueprint('job', __name__)

@job_bp.route('/api/jobs')
@login_required
def list_jobs():
    """API endpoint for jobs search"""
    try:
        jobs = Job.query.all()
        return jsonify([{
        'id': job.id,
        'title': job.title,
        'description': job.description,
        'location': job.location,
        'company': job.employer.company_name
    } for job in jobs]), 200
    except Exception as e:
        current_app.logger.error(f"Error in list_jobs: {str(e)}")
        return jsonify({'error': 'Failed to fetch jobs'}), 500
from secops.sec import csrf_protected

@job_bp.route('/api/jobs/import', methods=['POST'])
@csrf_protected
def import_jobs():
    """Import jobs from Atlassian or JSON file"""
    try:
        if request.files and 'job_file' in request.files:
            # Handle JSON file import
            file = request.files['job_file']
            if file.filename.endswith('.json'):
                jobs_data = json.loads(file.read())
                for job_data in jobs_data:
                    job = Job(
                        employer_id=current_user.id,
                        title=job_data['title'],
                        description=job_data['description'],
                        location=job_data['location']
                    )
                    db.session.add(job)
                db.session.commit()
                return jsonify({'success': True, 'message': 'Jobs imported successfully'})
            
        elif request.json and request.json.get('atlassian_token'):
            # Handle Atlassian API import
            token = request.json['atlassian_token']
            domain = request.json['atlassian_domain']
            headers = {'Authorization': f'Bearer {token}'}
            url = f'https://{domain}.atlassian.net/rest/api/3/search'
            
            response = requests.get(url, headers=headers)
            if response.ok:
                jobs_data = response.json()
                for issue in jobs_data['issues']:
                    if issue['fields'].get('issuetype', {}).get('name') == 'Job Posting':
                        job = Job(
                            employer_id=current_user.id,
                            title=issue['fields']['summary'],
                            description=issue['fields']['description'],
                            location=issue['fields'].get('customfield_location', 'Remote')
                        )
                        db.session.add(job)
                db.session.commit()
                return jsonify({'success': True, 'message': 'Jobs imported from Atlassian'})
                
        return jsonify({'error': 'Invalid import format'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
