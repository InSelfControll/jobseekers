from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from extensions import db
from functools import wraps
import os
import hashlib
import dns.resolver
from models import Employer
from flask import abort
from datetime import datetime, timedelta
import json
from services.monitoring_service import bot_monitor
from flask import Response, stream_with_context
import time #added import for time.sleep

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
        print(f"Verifying domain: {domain} for provider: {provider}")
        expected_host = request.host.lower()

        # Try CNAME first
        try:
            cname_answers = dns.resolver.resolve(domain, 'CNAME')
            print(f"CNAME records found: {[str(rdata.target) for rdata in cname_answers]}")
            print(f"Expected host: {expected_host}")
            
            for rdata in cname_answers:
                target = str(rdata.target).rstrip('.').lower()
                if target == expected_host:
                    print("CNAME verification successful")
                    return True
                # Check if target contains the expected host (for wildcard/subdomain cases)
                if expected_host in target or target in expected_host:
                    print("CNAME verification successful (partial match)")
                    return True
        except Exception as e:
            print(f"CNAME lookup failed: {str(e)}")
        
        # Check A record if CNAME fails
        if not cname_valid:
            try:
                import socket
                # Get all possible IPs for the host
                expected_ips = []
                try:
                    host_info = socket.getaddrinfo(request.host.split(':')[0], None)
                    expected_ips = [info[4][0] for info in host_info if info[0] == socket.AF_INET]
                except Exception as e:
                    print(f"Failed to resolve host IPs: {str(e)}")
                    expected_ips = [request.host.split(':')[0]]

                print(f"Checking A record. Expected IPs: {expected_ips}")
                a_answers = dns.resolver.resolve(domain, 'A')
                print(f"A records found: {[str(rdata) for rdata in a_answers]}")
                
                for rdata in a_answers:
                    if str(rdata).rstrip('.') in expected_ips:
                        print("A record verification successful")
                        return True
                        
            except Exception as e:
                print(f"A record lookup failed: {str(e)}")
        
        print("Domain verification failed - no matching records found")
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
        import logging
        
        if not current_user.sso_domain:
            return jsonify({'success': False, 'error': 'Please configure and verify domain first'})
            
        if not current_user.domain_verified:
            return jsonify({'success': False, 'error': 'Domain must be verified before generating SSL certificate'})
            
        logging.info(f"Starting SSL certificate generation for domain: {current_user.sso_domain}")
        
        ssl_service = SSLService(current_user.sso_domain, current_user.email)
        success, message = ssl_service.generate_certificate()
        
        if success:
            # Get certificate expiry for display
            expiry = current_user.ssl_expiry.strftime('%Y-%m-%d') if current_user.ssl_expiry else 'Unknown'
            
            logging.info(f"SSL certificate generated successfully for {current_user.sso_domain}")
            return jsonify({
                'success': True,
                'message': message,
                'domain': current_user.sso_domain,
                'ssl_enabled': True,
                'cert_expiry': expiry
            })
        
        logging.error(f"SSL certificate generation failed for {current_user.sso_domain}: {message}")
        return jsonify({
            'success': False,
            'message': message
        })
    except Exception as e:
        logging.error(f"Error in SSL certificate generation: {str(e)}")
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
    
    try:
        # Check if domain is already in use
        existing = Employer.query.filter_by(sso_domain=domain).first()
        if existing and existing.id != current_user.id:
            return jsonify({'success': False, 'error': 'Domain already in use'}), 400
            
        employer = Employer.query.get(current_user.id)
        employer.sso_domain = domain
        employer.domain_verified = False
        employer.ssl_enabled = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'records': [
                {'type': 'CNAME', 'name': domain, 'value': request.host}
            ]
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    
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
    domain = data.get('domain', '').lower()
    
    if not domain:
        return jsonify({'success': False, 'error': 'Domain is required'})

    # Check if domain is already verified
    employer = Employer.query.filter_by(sso_domain=domain).first()
    if employer and employer.domain_verified:
        return jsonify({'success': True, 'domain': domain, 'already_verified': True})
        
    # Update user's domain
    current_user.sso_domain = domain
    
    # Verify domain records
    if verify_domain_records(domain, current_user.sso_provider):
        current_user.domain_verified = True
        current_user.domain_verification_date = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True, 'domain': domain})
    else:
        return jsonify({'success': False, 'error': 'Domain verification failed'})

@admin_bp.route('/save-sso-settings', methods=['POST'])
@login_required
@admin_required
def save_sso_settings():
    try:
        employer = Employer.query.get(current_user.id)
        if request.is_json:
            data = request.get_json()
            provider = data.get('provider')
            employer.sso_provider = provider
            employer.sso_config = data
        else:
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
                if manifest_file:
                    manifest_content = manifest_file.read().decode('utf-8')
                    employer.sso_config = {
                        'manifest': manifest_content
                    }
                elif not employer.sso_config or 'manifest' not in employer.sso_config:
                    flash('Manifest file is required for Azure SSO', 'error')
                    return redirect(url_for('admin.sso_config'))
                
        db.session.commit()
        
        if request.is_json:
            return jsonify({'success': True})
        flash('SSO settings saved successfully', 'success')
        return redirect(url_for('admin.sso_config'))
        
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)})
        flash(f'Error saving SSO settings: {str(e)}', 'error')
        return redirect(url_for('admin.sso_config'))
        
    employer = Employer.query.get(current_user.id)
    employer.sso_domain = domain
    employer.domain_verified = False
@admin_bp.route('/bot-monitoring')
@login_required
@admin_required
def bot_monitoring():
    return render_template('admin/bot_monitoring.html')

@admin_bp.route('/bot-metrics-stream')
@login_required
@admin_required
def bot_metrics_stream():
    from services.ai_health_service import AIHealthAnalyzer #added import
    health_analyzer = AIHealthAnalyzer() #instantiate health analyzer

    def generate():
        while True:
            try:
                metrics = bot_monitor.get_metrics()
                # Add metrics to AI analyzer
                health_analyzer.add_metrics_snapshot(metrics)
                
                # Get AI health analysis every 5 minutes
                health_analysis = {}
                if (not health_analyzer.last_analysis_time or 
                    datetime.now() - health_analyzer.last_analysis_time > timedelta(minutes=5)):
                    health_analysis = health_analyzer.analyze_health() #removed await, assuming analyze_health is synchronous
                    health_analyzer.last_analysis_time = datetime.now()

                data = json.dumps({
                    'status': metrics.status,
                    'uptime': metrics.uptime,
                    'message_count': metrics.message_count,
                    'error_count': metrics.error_count,
                    'memory_usage': metrics.memory_usage,
                    'cpu_usage': metrics.cpu_usage,
                    'last_message_time': metrics.last_message_time.isoformat() if metrics.last_message_time else None,
                    'recent_errors': metrics.recent_errors,
                    'response_times': metrics.response_times,
                    'health_analysis': health_analysis
                })
                yield f"data: {data}\n\n"
                time.sleep(2)  # Update every 2 seconds
            except Exception as e:
                print(f"Error in bot-metrics-stream: {e}")
                yield f"data: {{'error': '{str(e)}'}}\n\n"
                time.sleep(10) #wait longer before trying again


    return Response(stream_with_context(generate()),
                   mimetype='text/event-stream')