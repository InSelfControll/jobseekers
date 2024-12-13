
from extensions import db
from models import Job, JobSeeker
from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://runner:runner@localhost:5432/db'
    db.init_app(app)
    return app

def run_migrations():
    app = create_app()
    with app.app_context():
        # Drop existing tables
        db.drop_all()
        # Create all tables fresh
        db.create_all()
        
if __name__ == '__main__':
    run_migrations()
