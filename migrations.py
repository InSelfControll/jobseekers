
from extensions import db
from models import Job, JobSeeker, Employer, Application, Message
from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://runner:runner@localhost:5432/db'
    db.init_app(app)
    return app

def run_migrations():
    app = create_app()
    with app.app_context():
        # Drop all tables and recreate
        db.drop_all()
        db.create_all()
        print("All database tables created successfully!")
        
if __name__ == '__main__':
    run_migrations()
