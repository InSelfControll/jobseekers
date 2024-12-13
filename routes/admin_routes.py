
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from extensions import db
from functools import wraps
import os
import hashlib
import dns.resolver
from models import Employer

def verify_domain_records(domain, provider):
    try:
        # Verify CNAME
        answers = dns.resolver.resolve(domain, 'CNAME')
        cname_valid = any(str(rdata.target).rstrip('.') == f"auth.{request.host}" for rdata in answers)
        
        # Verify TXT
        domain_hash = hashlib.sha256(f"{domain}:{provider}".encode()).hexdigest()[:16]
        expected_txt = f"v=sso provider={provider} verify={domain_hash}"
        answers = dns.resolver.resolve(domain, 'TXT')
        txt_valid = any(str(rdata).strip('"') == expected_txt for rdata in answers)
        
        return cname_valid and txt_valid
    except:
        return False

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not getattr(current_user, 'is_admin', False):
            flash('Admin access required', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/sso-config', methods=['GET'])
@login_required
@admin_required
def sso_config():
    users = Employer.query.all()
    return render_template('admin/sso_config.html',
                         users=users,
                         github_client_id=os.environ.get('GITHUB_CLIENT_ID', ''),
                         github_client_secret=os.environ.get('GITHUB_CLIENT_SECRET', ''),
                         saml_entity_id=os.environ.get('SAML_IDP_ENTITY_ID', ''),
                         saml_sso_url=os.environ.get('SAML_SSO_URL', ''),
                         saml_idp_cert=os.environ.get('SAML_IDP_CERT', ''),
                         admin_groups=os.environ.get('SAML_ADMIN_GROUPS', ''))

@admin_bp.route('/toggle-admin/<int:user_id>', methods=['POST'])
@login_required
def toggle_admin(user_id):
    if not current_user.is_owner:
        flash('Only owners can modify admin status', 'error')
        return redirect(url_for('admin.sso_config'))
    
    user = Employer.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    flash(f"Admin status updated for {user.email}", 'success')
    return redirect(url_for('admin.sso_config'))

@admin_bp.route('/verify-domain/<provider>')
@login_required
@admin_required
def verify_domain(provider):
    domain = request.args.get('domain')
    if not domain:
        return jsonify({'verified': False, 'error': 'No domain provided'})
    
    verified = verify_domain_records(domain, provider.lower())
    if verified:
        employer = Employer.query.get(current_user.id)
        employer.domain_verified = True
        db.session.commit()
    
    return jsonify({'verified': verified})

@admin_bp.route('/update-github-config', methods=['POST'])
@login_required
@admin_required
def update_github_config():
    os.environ['GITHUB_CLIENT_ID'] = request.form.get('github_client_id', '')
    os.environ['GITHUB_CLIENT_SECRET'] = request.form.get('github_client_secret', '')
    flash('GitHub settings updated successfully', 'success')
    return redirect(url_for('admin.sso_config'))

@admin_bp.route('/update-saml-config', methods=['POST'])
@login_required
@admin_required
def update_saml_config():
    os.environ['SAML_IDP_ENTITY_ID'] = request.form.get('entity_id', '')
    os.environ['SAML_SSO_URL'] = request.form.get('sso_url', '')
    os.environ['SAML_IDP_CERT'] = request.form.get('idp_cert', '')
    flash('SAML settings updated successfully', 'success')
    return redirect(url_for('admin.sso_config'))
@admin_bp.route('/save-domain', methods=['POST'])
@login_required
@admin_required
def save_domain():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
        
    provider = data.get('provider')
    domain = data.get('domain')
    csrf_token = data.get('csrf_token')
    
    if not domain:
        flash('Domain is required', 'error')
        return redirect(url_for('admin.sso_config'))
        
    employer = Employer.query.get(current_user.id)
    employer.sso_domain = domain
    db.session.commit()
    
    # Generate verification records
    domain_hash = hashlib.sha256(f"{domain}:{provider}".encode()).hexdigest()[:16]
    cname_record = f"CNAME {domain} auth.{request.host}"
    txt_record = f"TXT {domain} \"v=sso provider={provider} verify={domain_hash}\""
    
    return jsonify({
        'success': True,
        'cname_record': cname_record,
        'txt_record': txt_record
    })
