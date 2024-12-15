
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

@admin_bp.route('/sso-config')
@login_required
@admin_required
def sso_config():
    if not current_user.is_admin:
        abort(403)
    return render_template('admin/sso_config.html')

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
    db.session.commit()
    
    # Generate verification records
    domain_hash = hashlib.sha256(f"{domain}:{provider}".encode()).hexdigest()[:16]
    cname_record = f"CNAME {domain} auth.{request.host}"
    txt_record = f"TXT {domain} \"v=sso provider={provider} verify={domain_hash}\""
    
    return jsonify({
        'success': True,
        'cname_record': cname_record,
        'txt_record': txt_record,
        'shadow_url': f"https://{domain}/login"
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
        
    employer = Employer.query.get(current_user.id)
    employer.sso_domain = domain
    employer.domain_verified = False
    db.session.commit()
    
    return jsonify({'success': True})
