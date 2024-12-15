from flask import Blueprint, jsonify, request
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
@job_bp.route('/api/jobs/import', methods=['POST'])
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
                        location=job_data['location'],
                        latitude=job_data.get('latitude', 0),
                        longitude=job_data.get('longitude', 0)
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
                            location=issue['fields'].get('customfield_location', 'Remote'),
                            latitude=0,
                            longitude=0
                        )
                        db.session.add(job)
                db.session.commit()
                return jsonify({'success': True, 'message': 'Jobs imported from Atlassian'})
                
        return jsonify({'error': 'Invalid import format'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
