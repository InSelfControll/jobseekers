from geopy.distance import geodesic
from models import Job

def get_nearby_jobs(latitude, longitude, radius_km=15):
    """Get jobs within specified radius"""
    all_jobs = Job.query.filter_by(status='active').all()
    nearby_jobs = []
    
    for job in all_jobs:
        distance = geodesic(
            (latitude, longitude),
            (job.latitude, job.longitude)
        ).kilometers
        
        if distance <= radius_km:
            job.distance = round(distance, 1)
            nearby_jobs.append(job)
    
    return sorted(nearby_jobs, key=lambda x: x.distance)
