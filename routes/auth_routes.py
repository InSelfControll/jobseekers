
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import Employer
from extensions import db
from requests_oauthlib import OAuth2Session
import os

GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET')
GITHUB_AUTHORIZE_URL = 'https://github.com/login/oauth/authorize'
GITHUB_TOKEN_URL = 'https://github.com/login/oauth/access_token'
GITHUB_USER_INFO_URL = 'https://api.github.com/user'
GITHUB_USER_EMAIL_URL = 'https://api.github.com/user/emails'
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.utils import OneLogin_Saml2_Utils
from config.saml import SAML_SETTINGS

def init_saml_auth(req):
    auth = OneLogin_Saml2_Auth(req, SAML_SETTINGS)
    return auth

def prepare_flask_request(request):
    url_data = request.url.split('?')[0].split('/')
    return {
        'https': 'on' if request.scheme == 'https' else 'off',
        'http_host': request.host,
        'server_port': url_data[2:3][0] if len(url_data) > 2 else '',
        'script_name': request.path,
        'get_data': request.args.copy(),
        'post_data': request.form.copy()
    }

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        employer = Employer.query.filter_by(email=email).first()
        if employer and check_password_hash(employer.password_hash, password):
            login_user(employer)
            return redirect(url_for('employer.dashboard'))
        
        flash('Invalid email or password', 'error')
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        company_name = request.form.get('company_name')
        password = request.form.get('password')
        
        if Employer.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('auth.register'))
        
        employer = Employer(
            email=email,
            company_name=company_name,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(employer)
        db.session.commit()
        
        flash('Registration successful!', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html')

@auth_bp.route('/github/login')
def github_login():
    github = OAuth2Session(GITHUB_CLIENT_ID)
    authorization_url, state = github.authorization_url(GITHUB_AUTHORIZE_URL)
    session['oauth_state'] = state
    return redirect(authorization_url)

@auth_bp.route('/github/callback')
def github_callback():
    github = OAuth2Session(GITHUB_CLIENT_ID, state=session.get('oauth_state'))
    token = github.fetch_token(
        GITHUB_TOKEN_URL,
        client_secret=GITHUB_CLIENT_SECRET,
        authorization_response=request.url
    )
    
    resp = github.get(GITHUB_USER_INFO_URL)
    user_info = resp.json()
    
    resp = github.get(GITHUB_USER_EMAIL_URL)
    emails = resp.json()
    email = next((e['email'] for e in emails if e['primary']), emails[0]['email'])
    
    employer = Employer.query.filter_by(email=email).first()
    if not employer:
        employer = Employer(
            email=email,
            company_name=user_info.get('company') or user_info.get('login'),
            password_hash=generate_password_hash(os.urandom(24).hex())
        )
        db.session.add(employer)
        db.session.commit()
    
    login_user(employer)
    return redirect(url_for('employer.dashboard'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/saml/login')
def saml_login():
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    return redirect(auth.login())

@auth_bp.route('/saml/callback', methods=['POST'])
def saml_callback():
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    auth.process_response()
    errors = auth.get_errors()
    
    if not errors:
        if auth.is_authenticated():
            attributes = auth.get_attributes()
            email = attributes.get('email', [None])[0]
            
            if email:
                employer = Employer.query.filter_by(email=email).first()
                if employer:
                    login_user(employer)
                    return redirect(url_for('employer.dashboard'))
                    
    flash('SAML Authentication failed', 'error')
    return redirect(url_for('auth.login'))

@auth_bp.route('/saml/logout')
@login_required
def saml_logout():
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    return redirect(auth.logout())
