
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required
from services.email_service import send_verification_email
from flask_wtf.csrf import CSRFProtect
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
    domain = request.headers.get('Host')
    employer = Employer.query.filter_by(sso_domain=domain).first()
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        employer = Employer.query.filter_by(email=email).first()
        if employer and check_password_hash(employer.password_hash, password):
            employer.login_count += 1
            db.session.commit()
            login_user(employer)
            
            if employer.is_admin and employer.login_count > 1 and not employer.sso_domain:
                return redirect(url_for('admin.sso_config'))
            return redirect(url_for('employer.dashboard'))
        
        flash('Invalid email or password', 'error')
    return render_template('auth/login.html', employer=employer)

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email

class RegistrationForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if request.method == 'POST':
        email = request.form.get('email')
        company_name = request.form.get('company_name')
        password = request.form.get('password')
        domain = email.split('@')[1]
        
        existing_domain = Employer.query.filter_by(company_domain=domain).first()
        if existing_domain:
            flash('Another user from your company is already registered', 'error')
            return redirect(url_for('auth.register'))
            
        if Employer.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('auth.register'))
        
        domain = email.split('@')[1]
        existing_company = Employer.query.filter_by(company_domain=domain).first()
        
        employer = Employer(
            email=email,
            company_name=company_name,
            company_domain=domain,
            password_hash=generate_password_hash(password),
            is_admin=not existing_company,  # First user is admin
            is_owner=not existing_company   # First user is owner
        )
        
        db.session.add(employer)
        db.session.commit()
        
        send_verification_email(email)
        login_user(employer)
        
        flash('Registration successful! Please check your email to verify your account.', 'success')
        return redirect(url_for('admin.sso_config'))
    return render_template('auth/register.html', form=form)

@auth_bp.route('/github/login')
def github_login():
    domain = request.headers.get('Host')
    employer = Employer.query.filter_by(sso_domain=domain).first()
    if employer and employer.sso_provider == 'GITHUB':
        github = OAuth2Session(GITHUB_CLIENT_ID)
        authorization_url, state = github.authorization_url(GITHUB_AUTHORIZE_URL)
        session['oauth_state'] = state
        return redirect(authorization_url)
    flash('Invalid SSO configuration', 'error')
    return redirect(url_for('auth.login'))

def generate_sso_domain(employer, provider):
    import uuid
    domain_prefix = str(uuid.uuid4())[:8]
    domain = f"{domain_prefix}-{provider.lower()}.{request.host}"
    cname_record = f"CNAME {domain} {request.host}"
    txt_record = f"TXT {domain} \"v=sso1 provider={provider}\""
    return domain, cname_record, txt_record

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
    domain = request.form.get('domain') or f"{user_info.get('login').lower()}.{request.host}"
    if not employer:
        cname_record = f"CNAME {domain} login.{request.host}"
        txt_record = f"TXT {domain} \"v=sso1 provider=GITHUB user={user_info.get('login')}\""
        employer = Employer(
            email=email,
            company_name=user_info.get('company') or user_info.get('login'),
            password_hash=generate_password_hash(os.urandom(24).hex()),
            sso_domain=domain,
            sso_provider="GITHUB"
        )
        db.session.add(employer)
        db.session.commit()
        flash(f"Configure your DNS with:\nCNAME Record: {cname_record}\nTXT Record: {txt_record}", "success")
        session['sso_domain'] = domain
        session['sso_records'] = {'cname': cname_record, 'txt': txt_record}
    elif not employer.sso_domain:
        domain, cname_record, txt_record = generate_sso_domain(None, "GITHUB")
        employer.sso_domain = domain
        employer.sso_provider = "GITHUB"
        db.session.commit()
        flash(f"Configure your DNS with:\nCNAME Record: {cname_record}\nTXT Record: {txt_record}", "success")
    login_user(employer)
    
    login_user(employer)
    return redirect(url_for('employer.dashboard'))

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    try:
        email = current_app.ts.loads(token, salt='email-verify-key', max_age=86400)
        employer = Employer.query.filter_by(email=email).first()
        if employer:
            employer.email_verified = True
            db.session.commit()
            flash('Email verified successfully!', 'success')
        else:
            flash('Invalid verification link', 'error')
    except:
        flash('Invalid or expired verification link', 'error')
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/saml/login')
def saml_login():
    domain = request.headers.get('Host')
    employer = Employer.query.filter_by(sso_domain=domain).first()
    if employer and employer.sso_provider == 'SAML':
        req = prepare_flask_request(request)
        auth = init_saml_auth(req)
        return redirect(auth.login())
    flash('Invalid SSO configuration', 'error')
    return redirect(url_for('auth.login'))

@auth_bp.route('/saml/callback', methods=['POST'])
def saml_callback():
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    auth.process_response()
    errors = auth.get_errors()
    
    if not errors and auth.is_authenticated():
        # Generate SSO domain after successful authentication
        domain, cname, txt = generate_sso_domain(employer, "SAML")
        flash(f"Configure your DNS with:\n{cname}\n{txt}", "info")
    
    if not errors:
        if auth.is_authenticated():
            attributes = auth.get_attributes()
            email = attributes.get('email', [None])[0]
            
            if email:
                employer = Employer.query.filter_by(email=email).first()
                admin_groups = os.environ.get('SAML_ADMIN_GROUPS', '').split(',')
                user_groups = attributes.get('groups', [])
                
                is_admin = any(group in admin_groups for group in user_groups)
                
                if employer:
                    if is_admin:
                        employer.is_admin = True
                        db.session.commit()
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
