import pytest
from flask import url_for
from models import Employer
from extensions import db
from werkzeug.security import generate_password_hash

class TestAuthRoutes:
    @pytest.fixture(autouse=True)
    def setup(self, client, app):
        self.client = client
        self.app = app
        with self.app.app_context():
            db.create_all()
            yield
            db.session.remove()
            db.drop_all()

    def test_login_page_loads(self, client):
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_successful_login(self, client):
        with self.app.app_context():
            employer = Employer(
                email='test@example.com',
                company_name='Test Company'
            )
            employer.set_password('password123')
            db.session.add(employer)
            db.session.commit()

        response = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123',
            'submit': True
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Dashboard' in response.data

    def test_invalid_login_credentials(self, client):
        response = client.post('/login', data={
            'email': 'wrong@example.com',
            'password': 'wrongpassword',
            'submit': True
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Invalid email or password' in response.data

    def test_register_page_loads(self, client):
        response = client.get('/register')
        assert response.status_code == 200
        assert b'Register' in response.data

    def test_successful_registration(self, client):
        response = client.post('/register', data={
            'email': 'newuser@example.com',
            'password': 'password123',
            'company_name': 'New Company',
            'submit': True
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Dashboard' in response.data

        with self.app.app_context():
            employer = Employer.query.filter_by(email='newuser@example.com').first()
            assert employer is not None
            assert employer.company_name == 'New Company'

    def test_register_existing_email(self, client):
        with self.app.app_context():
            existing_employer = Employer(
                email='existing@example.com',
                company_name='Existing Company'
            )
            existing_employer.set_password('password123')
            db.session.add(existing_employer)
            db.session.commit()

        response = client.post('/register', data={
            'email': 'existing@example.com',
            'password': 'password123',
            'company_name': 'New Company',
            'submit': True
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Email already registered' in response.data

    def test_logout(self, client):
        with self.app.app_context():
            employer = Employer(
                email='test@example.com',
                company_name='Test Company'
            )
            employer.set_password('password123')
            db.session.add(employer)
            db.session.commit()

        # Login first
        client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123',
            'submit': True
        })

        # Then test logout
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_login_invalid_form_data(self, client):
        response = client.post('/login', data={
            'email': 'invalid-email',
            'password': '',
            'submit': True
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Invalid email or password' in response.data

    def test_register_invalid_form_data(self, client):
        response = client.post('/register', data={
            'email': 'invalid-email',
            'password': '',
            'company_name': '',
            'submit': True
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Register' in response.data

    def test_authenticated_user_redirect(self, client):
        with self.app.app_context():
            employer = Employer(
                email='test@example.com',
                company_name='Test Company'
            )
            employer.set_password('password123')
            db.session.add(employer)
            db.session.commit()

        # Login
        client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123',
            'submit': True
        })

        # Try accessing login page while authenticated
        response = client.get('/login', follow_redirects=True)
        assert response.status_code == 200
        assert b'Dashboard' in response.data

        # Try accessing register page while authenticated
        response = client.get('/register', follow_redirects=True)
        assert response.status_code == 200
        assert b'Dashboard' in response.data