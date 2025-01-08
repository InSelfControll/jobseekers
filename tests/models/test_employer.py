import pytest
from datetime import datetime
from models.employer import Employer, DomainValidator
from models.job import Job
from extensions import db
from werkzeug.security import generate_password_hash

class TestEmployer:
    @pytest.fixture(autouse=True)
    def setup(self, app, db):
        self.app = app
        self.db = db
        
        # Create test employer
        self.employer_data = {
            'email': 'test@company.com',
            'company_name': 'Test Company',
            'password_hash': generate_password_hash('password123'),
            'company_domain': 'company.com'
        }
        
        with self.app.app_context():
            self.employer = Employer(**self.employer_data)
            self.db.session.add(self.employer)
            self.db.session.commit()
            
    def teardown_method(self):
        with self.app.app_context():
            self.db.session.query(Job).delete()
            self.db.session.query(Employer).delete()
            self.db.session.commit()
            
    def test_employer_creation(self):
        """Test employer model instantiation"""
        with self.app.app_context():
            assert self.employer.email == self.employer_data['email']
            assert self.employer.company_name == self.employer_data['company_name']
            assert self.employer.company_domain == self.employer_data['company_domain']
            assert isinstance(self.employer.created_at, datetime)
            
    def test_required_fields(self):
        """Test required fields validation"""
        with self.app.app_context():
            invalid_employer = Employer(company_name='Invalid Company')
            with pytest.raises(Exception):
                self.db.session.add(invalid_employer)
                self.db.session.commit()
                
    def test_unique_constraints(self):
        """Test unique constraints on email and sso_domain"""
        with self.app.app_context():
            duplicate_employer = Employer(
                email=self.employer_data['email'],
                company_name='Another Company',
                password_hash=generate_password_hash('password456')
            )
            with pytest.raises(Exception):
                self.db.session.add(duplicate_employer)
                self.db.session.commit()
                
    def test_relationship_with_jobs(self):
        """Test relationship with Job model"""
        with self.app.app_context():
            job = Job(
                employer_id=self.employer.id,
                title='Test Job',
                description='Job Description',
                location='Remote'
            )
            self.db.session.add(job)
            self.db.session.commit()
            
            assert len(self.employer.jobs) == 1
            assert self.employer.jobs[0].title == 'Test Job'
            assert job.employer == self.employer
            
    def test_query_operations(self):
        """Test query operations including filter_by"""
        with self.app.app_context():
            # Test filter_by
            employer = Employer.query.filter_by(email=self.employer_data['email']).first()
            assert employer is not None
            assert employer.company_name == self.employer_data['company_name']
            
            # Test get
            employer = Employer.query.get(self.employer.id)
            assert employer is not None
            assert employer.email == self.employer_data['email']
            
    def test_user_mixin_functionality(self):
        """Test UserMixin functionality"""
        with self.app.app_context():
            assert self.employer.is_authenticated
            assert self.employer.is_active
            assert not self.employer.is_anonymous
            assert isinstance(self.employer.get_id(), str)
            
    def test_domain_validation(self):
        """Test domain validation functionality"""
        with self.app.app_context():
            validator = DomainValidator('example.com')
            success, message = validator.validate_domain()
            assert isinstance(success, bool)
            assert isinstance(message, str)
            
            # Test invalid domain
            validator = DomainValidator('invalid..domain')
            success, message = validator.validate_domain()
            assert not success
            assert 'failed' in message.lower()
            
    def test_ssl_config_validation(self):
        """Test SSL configuration validation"""
        with self.app.app_context():
            self.employer.ssl_enabled = True
            self.employer.ssl_cert_path = '/path/to/cert'
            self.employer.ssl_key_path = '/path/to/key'
            
            # Test missing certificate files
            success, message = DomainValidator(self.employer.company_domain).validate_ssl_config()
            assert not success
            assert 'failed' in message.lower()
            
    def test_boolean_flags(self):
        """Test boolean flags and defaults"""
        with self.app.app_context():
            assert self.employer.notify_new_applications is True
            assert self.employer.notify_status_changes is True
            assert self.employer.is_admin is False
            assert self.employer.is_owner is False
            assert self.employer.ssl_enabled is False
            assert self.employer.domain_verified is False
            
    def test_session_handling(self):
        """Test database session handling"""
        with self.app.app_context():
            # Test session rollback
            invalid_employer = Employer(email='test@test.com')  # Missing required fields
            self.db.session.add(invalid_employer)
            with pytest.raises(Exception):
                self.db.session.commit()
            self.db.session.rollback()
            
            # Verify session is still usable
            valid_employer = Employer(
                email='test2@company.com',
                company_name='Test Company 2',
                password_hash=generate_password_hash('password789')
            )
            self.db.session.add(valid_employer)
            self.db.session.commit()
            assert valid_employer.id is not None