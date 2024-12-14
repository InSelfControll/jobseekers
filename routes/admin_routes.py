
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
from flask_login import login_required, current_user
from extensions import db
from functools import wraps
import os
import hashlib
import dns.resolver
from models import Employer
from flask import abort

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def verify_domain_records(domain, provider):
    try:
        # Check CNAME record or A record
        try:
            # Try CNAME first
            try:
                cname_answers = dns.resolver.resolve(domain, 'CNAME')
                cname_valid = any(str(rdata.target).rstrip('.') == f"auth.{request.host}" for rdata in cname_answers)
            except:
                cname_valid = False
                
            # Try A record if CNAME fails
            if not cname_valid:
                try:
                    expected_ip = dns.resolver.resolve(f"auth.{request.host}", 'A')[0].address
                    a_answers = dns.resolver.resolve(domain, 'A')
                    cname_valid = any(str(rdata.address) == expected_ip for rdata in a_answers)
                except:
                    pass
        except:
            cname_valid = False
            
        # Check TXT record
        try:
            domain_hash = hashlib.sha256(f"{domain}:{provider}".encode()).hexdigest()[:16]
            expected_txt = f"v=sso provider={provider} verify={domain_hash}"
            txt_answers = dns.resolver.resolve(domain, 'TXT')
            txt_valid = any(str(rdata).strip('"') == expected_txt for rdata in txt_answers)
        except:
            txt_valid = False
            
        return cname_valid or txt_valid
    except:
        return False

@admin_bp.route('/save-domain', methods=['POST'])
@login_required
@admin_required
def save_domain():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
        
    provider = data.get('provider')
    domain = data.get('domain')
    github_client_id = data.get('github_client_id')
    github_client_secret = data.get('github_client_secret')
    
    if not domain:
        return jsonify({'success': False, 'error': 'Domain is required'}), 400
        
    # Check if domain is already in use by another employer
    existing = Employer.query.filter(
        Employer.sso_domain == domain,
        Employer.id != current_user.id
    ).first()
    
    if existing:
        return jsonify({'success': False, 'error': 'Domain already in use'}), 400
        
    employer = Employer.query.get(current_user.id)
    employer.sso_domain = domain
    employer.sso_provider = provider.upper()
    if provider.upper() == 'GITHUB' and github_client_id:
        employer.github_client_id = github_client_id
        if github_client_secret:
            employer.github_client_secret = github_client_secret
    employer.is_admin = True  # Ensure admin status
    db.session.commit()
    
    # Generate verification records
    domain_hash = hashlib.sha256(f"{domain}:{provider}".encode()).hexdigest()[:16]
    cname_record = f"CNAME {domain} auth.{request.host}"
    txt_record = f"TXT {domain} \"v=sso provider={provider} verify={domain_hash}\""
    
    return jsonify({
        'success': True,
        'cname_record': cname_record,
        'txt_record': txt_record,
        'shadow_url': f"https://{domain}/login"  # Shadow interface URL
    })

@admin_bp.route('/sso-config', methods=['GET'])
@login_required
@admin_required
def sso_config():
    users = Employer.query.all()
    return render_template('admin/sso_config.html', 
                         users=users,
                         current_user=current_user,
                         saml_idp_cert=current_user.saml_idp_cert if hasattr(current_user, 'saml_idp_cert') else None,
                         admin_groups=current_user.admin_groups if hasattr(current_user, 'admin_groups') else '')

@admin_bp.route('/toggle-admin/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    if not current_user.is_owner:
        abort(403)
        
    user = Employer.query.get(user_id)
    if not user:
        abort(404)
        
    user.is_admin = not user.is_admin
    db.session.commit()
    return redirect(url_for('admin.sso_config'))

@admin_bp.route('/update-domain', methods=['POST'])
@login_required
@admin_required
def update_domain():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
        
    domain = data.get('domain')
    if not domain:
        return jsonify({'success': False, 'error': 'Domain is required'}), 400
        
    employer = Employer.query.get(current_user.id)
    employer.sso_domain = domain
    employer.domain_verified = False  # Reset verification status
    db.session.commit()
    
    return jsonify({'success': True})



@admin_bp.route('/verify-domain', methods=['POST'])
@login_required
@admin_required
def verify_domain():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
        
    domain = data.get('domain')
    provider = data.get('provider')
    
    if not domain or not provider:
        return jsonify({'success': False, 'error': 'Domain and provider are required'}), 400
        
    is_verified = verify_domain_records(domain, provider)
    if is_verified:
        employer = Employer.query.get(current_user.id)
        employer.domain_verified = True
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Domain verification failed'})

@admin_bp.route('/update-saml-config', methods=['POST'])
@login_required
@admin_required
def update_saml_config():
    if request.is_json:
        data = request.get_json()
        entity_id = data.get('entity_id')
        sso_url = data.get('sso_url')
        idp_cert = data.get('idp_cert')
        admin_groups = data.get('admin_groups')
    else:
        entity_id = request.form.get('entity_id')
        sso_url = request.form.get('sso_url')
        idp_cert = request.form.get('idp_cert')
        admin_groups = request.form.get('admin_groups')

    employer = Employer.query.get(current_user.id)
    if entity_id:
        employer.saml_entity_id = entity_id
    if sso_url:
        employer.saml_sso_url = sso_url
    if idp_cert:
        employer.saml_idp_cert = idp_cert
    if admin_groups:
        employer.admin_groups = admin_groups

    db.session.commit()
    flash('SAML configuration updated successfully', 'success')
    return redirect(url_for('admin.sso_config'))

