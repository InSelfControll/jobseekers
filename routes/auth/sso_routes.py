import os
import logging
from flask import Blueprint, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from core.db_utils import session_scope
from models import Employer
from services.domain_service import DomainService
from services.github_service import GitHubOAuth
from services.saml_service import SAMLProvider
from werkzeug.security import generate_password_hash

logger = logging.getLogger(__name__)
sso_bp = Blueprint('sso', __name__, url_prefix='/auth')

# GitHub OAuth Configuration
github_oauth = GitHubOAuth(
    client_id=os.getenv('GITHUB_CLIENT_ID'),
    client_secret=os.getenv('GITHUB_CLIENT_SECRET')
)

# SAML Provider Configuration
saml_provider = SAMLProvider()

@sso_bp.route('/github/login')
def github_login():
    return github_oauth.get_authorization_url()

@sso_bp.route('/github/callback')
def github_callback():
    code = request.args.get('code')
    return handle_github_callback(code)

@sso_bp.route('/github/configure', methods=['GET', 'POST'])
@login_required
def github_configure():
    """Configure GitHub SSO domain"""
    if request.method == 'POST':
        domain = request.form.get('domain')
        if not domain:
            return jsonify({'error': 'Domain is required'}), 400

        try:
            current_user.sso_domain = domain
            current_user.sso_provider = 'github'
            current_user.domain_verified = False
            db.session.commit()

            domain_service = DomainService()
            success, message = domain_service.setup_custom_domain(current_user.id)
            
            if not success:
                logger.error(f"Domain setup failed: {message}")
                return jsonify({'error': message}), 400

            session['sso_domain'] = domain
            return render_template('auth/github_domain.html')

        except Exception as e:
            logger.error(f"GitHub domain configuration error: {e}")
            return jsonify({'error': str(e)}), 500

    return render_template('auth/github_domain.html')

@sso_bp.route('/auth0/login')
def auth0_login():
    return auth0_service.authorize_redirect(
        redirect_uri=url_for('sso.auth0_callback', _external=True),
        audience=f'https://{auth0_service.domain}/api/v2/'
    )

@sso_bp.route('/auth0/callback')
def auth0_callback():
    token = auth0_service.authorize_access_token()
    payload = auth0_service.verify_token(token['access_token'])
    
    with session_scope() as session:
        employer = Employer.query.filter_by(
            email=payload['email'],
            sso_provider='auth0'
        ).first()
        
        if not employer:
            employer = Employer(
                email=payload['email'],
                sso_provider='auth0',
                sso_id=payload['sub']
            )
            session.add(employer)
            
    return redirect(url_for('employer.dashboard'))
@sso_bp.route('/verify-domain/<domain>')
@login_required
def verify_domain(domain):
    """Verify custom domain configuration"""
    try:
        domain_service = DomainService()
        success, message = domain_service.verify_domain(domain)
        
        if success:
            current_user.domain_verified = True
            db.session.commit()
            return jsonify({'message': 'Domain verified successfully'})
        
        return jsonify({'error': message}), 400

    except Exception as e:
        logger.error(f"Domain verification error: {e}")
        return jsonify({'error': str(e)}), 500