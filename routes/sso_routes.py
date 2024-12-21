from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app, jsonify
from secops.sec import csrf_protected, exempt_csrf
from flask_login import login_user
from werkzeug.security import generate_password_hash
from models import Employer
from extensions import db
from requests_oauthlib import OAuth2Session
import os

sso_bp = Blueprint('sso', __name__, url_prefix='/sso')

def get_sso_config(domain):
    employer = Employer.query.filter_by(sso_domain=domain).first()
    if not employer or not employer.sso_config:
        return None
    return employer.sso_config
GITHUB_AUTHORIZE_URL = 'https://github.com/login/oauth/authorize'
GITHUB_TOKEN_URL = 'https://github.com/login/oauth/access_token'
GITHUB_USER_INFO_URL = 'https://api.github.com/user'
GITHUB_USER_EMAIL_URL = 'https://api.github.com/user/emails'

@sso_bp.route('/github/login')
@exempt_csrf
def github_login():
    domain = request.headers.get('Host')
    employer = Employer.query.filter_by(sso_domain=domain).first()
    if employer and employer.sso_provider == 'GITHUB':
        config = get_sso_config(domain)
        if not config:
            flash('SSO configuration not found', 'error')
            return redirect(url_for('auth.login'))
            
        github = OAuth2Session(config['client_id'])
        authorization_url, state = github.authorization_url(GITHUB_AUTHORIZE_URL)
        session['oauth_state'] = state
        return redirect(authorization_url)
    flash('Invalid SSO configuration', 'error')
    return redirect(url_for('auth.login'))

@sso_bp.route('/github/callback')
@exempt_csrf
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
            password_hash=generate_password_hash(os.urandom(24).hex()),
            sso_provider="GITHUB"
        )
        db.session.add(employer)
        db.session.commit()
        
    login_user(employer)
    return redirect(url_for('employer.dashboard'))
