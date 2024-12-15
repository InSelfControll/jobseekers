
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from extensions import db
from functools import wraps
import os
import hashlib
import dns.resolver
from models import Employer
from flask import abort

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/domain-config')
@login_required
@admin_required
def domain_config():
    return render_template('admin/domain_config.html')

@admin_bp.route('/sso-config')
@login_required
@admin_required
def sso_config():
    if not current_user.is_admin:
        abort(403)
    # Get all admins for the company
    admins = Employer.query.filter(
        (Employer.is_admin == True) & 
        (Employer.company_domain == current_user.company_domain)
    ).all()
    return render_template('admin/sso_config.html', admins=admins)

@admin_bp.route('/remove-admin/<int:admin_id>', methods=['POST'])
@login_required
@admin_required
def remove_admin(admin_id):
    if not current_user.is_owner:
        return jsonify({'success': False, 'error': 'Only owners can remove admins'})
        
    try:
        admin = Employer.query.get(admin_id)
        if admin.is_owner:
            return jsonify({'success': False, 'error': 'Cannot remove owner'})
            
        admin.is_admin = False
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

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

@admin_bp.route('/upload-ssl', methods=['POST'])
@login_required
@admin_required
def upload_ssl():
    if 'cert' not in request.files or 'key' not in request.files:
        return jsonify({'success': False, 'error': 'Missing certificate files'})
        
    cert_file = request.files['cert']
    key_file = request.files['key']
    
    try:
        # Save SSL files securely
        cert_path = f'ssl/{current_user.id}/cert.pem'
        key_path = f'ssl/{current_user.id}/key.pem'
        
        os.makedirs(os.path.dirname(cert_path), exist_ok=True)
        cert_file.save(cert_path)
        key_file.save(key_path)
        
        # Update employer SSL status
        employer = Employer.query.get(current_user.id)
        employer.ssl_enabled = True
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/save-domain', methods=['POST'])
@login_required
@admin_required
def save_domain():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
        
    domain = data.get('domain')
    
    if not domain:
        return jsonify({'success': False, 'error': 'Domain is required'}), 400
    
    employer = Employer.query.get(current_user.id)
    employer.sso_domain = domain
    employer.domain_verified = False
    
    # Generate verification records
    domain_hash = hashlib.sha256(f"{domain}:{employer.sso_provider or 'SSO'}".encode()).hexdigest()[:16]
    server_ip = request.host_url.split('://')[1].rstrip('/')
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'records': [
            {'type': 'CNAME', 'name': domain, 'value': request.host}
        ]
    })
    
    return jsonify({
        'success': True,
        'a_record': a_record,
        'txt_record': txt_record,
        'records': [
            {'type': 'A', 'name': domain, 'value': request.host_url.split('://')[1].split(':')[0]},
            {'type': 'TXT', 'name': domain, 'value': f'v=sso1 provider={provider} verify={domain_hash}'}
        ]
    })

@admin_bp.route('/email-settings', methods=['GET'])
@login_required
@admin_required
def email_settings():
    return render_template('admin/email_settings.html',
                         email_footer=current_user.email_footer,
                         notify_new_applications=current_user.notify_new_applications,
                         notify_status_changes=current_user.notify_status_changes)

@admin_bp.route('/update-email-settings', methods=['POST'])
@login_required
@admin_required
def update_email_settings():
    try:
        current_user.company_domain = request.form.get('email_domain')
        current_user.email_footer = request.form.get('email_footer')
        current_user.notify_new_applications = 'notify_new_applications' in request.form
        current_user.notify_status_changes = 'notify_status_changes' in request.form
        
        db.session.commit()
        flash('Email settings updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating email settings: {str(e)}', 'danger')
    
    return redirect(url_for('admin.email_settings'))

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
        
    try:
        employer = Employer.query.get(current_user.id)
        employer.sso_domain = domain
        employer.domain_verified = False
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/verify-domain', methods=['POST'])
@login_required
@admin_required
def verify_domain():
    data = request.get_json()
    if not data or not data.get('domain'):
        return jsonify({'success': False, 'error': 'Domain is required'}), 400
        
    try:
        if verify_domain_records(data['domain'], current_user.sso_provider):
            employer = Employer.query.get(current_user.id)
            employer.domain_verified = True
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Domain verification failed'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/save-sso-settings', methods=['POST'])
@login_required
@admin_required
def save_sso_settings():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
        
    try:
        employer = Employer.query.get(current_user.id)
        employer.sso_provider = data['provider']
        
        # Store encrypted credentials in environment variables
        if data['provider'] == 'GITHUB':
            os.environ[f'GITHUB_CLIENT_ID_{employer.id}'] = data['client_id']
            os.environ[f'GITHUB_CLIENT_SECRET_{employer.id}'] = data['client_secret']
        elif data['provider'] == 'SAML':
            os.environ[f'SAML_MANIFEST_{employer.id}'] = data['saml_manifest']
            
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
        
    employer = Employer.query.get(current_user.id)
    employer.sso_domain = domain
    employer.domain_verified = False
    db.session.commit()
    
    return jsonify({'success': True})
