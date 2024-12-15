
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
        # Check CNAME record
        try:
            cname_answers = dns.resolver.resolve(domain, 'CNAME')
            cname_valid = any(str(rdata.target).rstrip('.') == request.host for rdata in cname_answers)
        except:
            cname_valid = False
        
        # Check A record if CNAME fails
        if not cname_valid:
            try:
                expected_ip = request.host.split(':')[0]  # Get IP without port
                a_answers = dns.resolver.resolve(domain, 'A')
                a_valid = any(str(rdata).rstrip('.') == expected_ip for rdata in a_answers)
            except:
                a_valid = False
            cname_valid = a_valid
        
        if not cname_valid:
            return False
            
        # Verify TXT record
        try:
            domain_hash = hashlib.sha256(f"{domain}:{provider}".encode()).hexdigest()[:16]
            expected_txt = f"v=sso provider={provider} verify={domain_hash}"
            txt_answers = dns.resolver.resolve(domain, 'TXT')
            for rdata in txt_answers:
                txt_record = str(rdata).strip('"').strip()
                if txt_record == expected_txt:
                    return True
        except Exception as e:
            print(f"TXT verification error: {str(e)}")
            pass
            
        return False
    except Exception as e:
        print(f"Domain verification error: {str(e)}")
        return False

@admin_bp.route('/generate-ssl', methods=['POST'])
@login_required
@admin_required
def generate_ssl():
    try:
        from services.ssl_service import SSLService
        
        if not current_user.sso_domain:
            return jsonify({'success': False, 'error': 'Please configure domain first'})
            
        ssl_service = SSLService(current_user.sso_domain, current_user.email)
        success, message = ssl_service.generate_certificate()
        
        return jsonify({
            'success': success,
            'message': message
        })
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
    try:
        employer = Employer.query.get(current_user.id)
        provider = request.form.get('provider')
        employer.sso_provider = provider
        
        if provider == 'GITHUB':
            client_id = request.form.get('client_id')
            client_secret = request.form.get('client_secret')
            
            if not client_id or not client_secret:
                flash('Client ID and Client Secret are required for GitHub SSO', 'error')
                return redirect(url_for('admin.sso_config'))
                
            employer.sso_config = {
                'client_id': client_id,
                'client_secret': client_secret
            }
            
        elif provider == 'AZURE':
            manifest_file = request.files.get('manifest_file')
            if not manifest_file:
                flash('Manifest file is required for Azure SSO', 'error')
                return redirect(url_for('admin.sso_config'))
                
            manifest_content = manifest_file.read().decode('utf-8')
            employer.sso_config = {
                'manifest': manifest_content
            }
            
        db.session.commit()
        flash('SSO settings saved successfully', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error saving SSO settings: {str(e)}', 'error')
        
    return redirect(url_for('admin.sso_config'))
        
    employer = Employer.query.get(current_user.id)
    employer.sso_domain = domain
    employer.domain_verified = False
    db.session.commit()
    
    return jsonify({'success': True})
