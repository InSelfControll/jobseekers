from builtins import Exception, str
import logging
from flask import Blueprint, render_template, request, jsonify, abort, Response
from flask_login import login_required, current_user
from functools import wraps
import json
import psutil
from routes import admin
import time
from datetime import datetime
from models import Employer, db
from services.domain_service import DomainService
from services.ssl_service import SSLService
from services.email_service import EmailService
from services.bot_service import BotService
from core.db_utils import session_scope, cleanup_session, safe_commit
logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        allowed_admins = ['admin@hostme.co.il', 'admin@aijobsearch.tech']
        if current_user.email not in allowed_admins:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/email-settings', methods=['GET', 'POST'])
@login_required
@admin_required
def email_settings():
    if request.method == 'POST':
        email_domain = request.form.get('email_domain')
        email_footer = request.form.get('email_footer')
        notify_new_applications = bool(request.form.get('notify_new_applications'))
        notify_status_changes = bool(request.form.get('notify_status_changes'))
        
        try:
            with session_scope():
                email_service = EmailService()
                email_service.update_settings(
                    current_user.id,
                    email_domain,
                    email_footer,
                    notify_new_applications,
                    notify_status_changes
                )
                return jsonify(success=True)
        except Exception as e:
            logger.error(f"Error updating email settings: {str(e)}", extra={'user_id': current_user.id})
            cleanup_session()
            return render_template('errors/500.html', error_message="Failed to update email settings. Please try again."), 500
            
    return render_template(
        'admin/email_settings.html',
        email_footer=current_user.email_footer,
        notify_new_applications=current_user.notify_new_applications,
        notify_status_changes=current_user.notify_status_changes
    )

@admin_bp.route('/domain-config', methods=['GET'])
@login_required
@admin_required
def domain_config():
    return render_template('admin/domain_config.html')

@admin_bp.route('/save-domain', methods=['POST'])
@login_required
@admin_required
def save_domain():
    data = request.get_json()
    domain = data.get('domain')
    
    if not domain:
        return jsonify(error="Domain is required"), 400
        
    try:
        with session_scope():
            domain_service = DomainService()
            success, message = domain_service.save_domain(current_user.id, domain)
            if success:
                return jsonify(success=True, records=[{"type": "CNAME", "value": request.host}])
            return jsonify(error=message), 400
    except Exception as e:
        logger.error(f"Error saving domain: {str(e)}", extra={'user_id': current_user.id, 'domain': domain})
        cleanup_session()
        return render_template('errors/500.html', error_message="Failed to save domain configuration. Please try again."), 500

@admin_bp.route('/verify-domain', methods=['POST'])
@login_required
@admin_required
def verify_domain():
    data = request.get_json()
    domain = data.get('domain')
    
    if not domain:
        return jsonify(error="Domain is required"), 400
        
    try:
        domain_service = DomainService()
        success, message = domain_service.verify_domain(current_user.id, domain)
        if success:
            return jsonify(success=True, domain=domain)
        return jsonify(error=message), 400
    except Exception as e:
        logger.error(f"Error verifying domain: {e}")
        return jsonify(error=str(e)), 400

@admin_bp.route('/generate-ssl', methods=['POST'])
@login_required
@admin_required
def generate_ssl():
    try:
        ssl_service = SSLService()
        success, message = ssl_service.generate_certificate(current_user.sso_domain)
        if success:
            return jsonify(success=True)
        return jsonify(error=message), 400
    except Exception as e:
        logger.error(f"Error generating SSL certificate: {e}")
        return jsonify(error=str(e)), 400

@admin_bp.route('/upload-ssl', methods=['POST'])
@login_required
@admin_required
def upload_ssl():
    if 'cert_file' not in request.files or 'key_file' not in request.files:
        return jsonify(error="Certificate and key files are required"), 400
        
    try:
        ssl_service = SSLService()
        cert_file = request.files['cert_file']
        key_file = request.files['key_file']
        success, message = ssl_service.upload_certificate(
            current_user.sso_domain,
            cert_file,
            key_file
        )
        if success:
            return jsonify(success=True)
        return jsonify(error=message), 400
    except Exception as e:
        logger.error(f"Error uploading SSL certificate: {e}")
        return jsonify(error=str(e)), 400

@admin_bp.route('/sso-config', methods=['GET'])
@login_required
@admin_required
def sso_config():
    return render_template('admin/sso_config.html')

@admin_bp.route('/sso/settings', methods=['POST'])
@login_required
@admin_required
def save_sso_settings():
    try:
        provider = request.form.get('provider')
        if provider == 'GITHUB':
            sso_config = {
                'client_id': request.form.get('client_id'),
                'client_secret': request.form.get('client_secret')
            }
        elif provider == 'AUTH0':
            sso_config = {
                'domain': request.form.get('domain'),
                'client_id': request.form.get('client_id'),
                'client_secret': request.form.get('client_secret'),
                'callback_url': f"https://{current_user.sso_domain}/auth/auth0/callback"
            }
        else:
            return jsonify(error="Invalid SSO provider"), 400
            
        with session_scope() as session:
            current_user.sso_provider = provider
            current_user.sso_config = sso_config
            return jsonify(success=True)
    except Exception as e:
        logger.error(f"Error saving SSO settings: {str(e)}", extra={'user_id': current_user.id})
        cleanup_session()
        return render_template('errors/500.html', error_message="Failed to save SSO settings. Please try again."), 500

@admin_bp.route('/bot-status')
@login_required
@admin_required
def bot_status():
    return render_template('admin/bot_status.html')
from flask import current_app, jsonify

async def bot_status():
    try:
        bot_service = current_app.service_manager.get_service('bot')
        status = await bot_service.get_status()
        return jsonify({
            'online': status.get('running', False),
            'metrics': status.get('metrics', {})
        })
    except Exception as e:
        logger.error(f"Error getting bot status: {e}")
        return jsonify({'online': False, 'error': str(e)}), 500


@admin_bp.route('/bot-metrics-stream')
@login_required
@admin_required
def bot_metrics_stream():
    def generate():
        bot_service = BotService()
        while True:
            metrics = {
                'status': bot_service.get_status(),
                'message_count': bot_service.get_message_count(),
                'memory_usage': psutil.Process().memory_info().rss / 1024 / 1024,
                'cpu_usage': psutil.Process().cpu_percent(),
                'uptime': bot_service.get_uptime(),
                'last_message_time': bot_service.get_last_message_time(),
                'recent_errors': bot_service.get_recent_errors(),
                'response_times': bot_service.get_response_times(),
                'health_analysis': bot_service.get_health_analysis()
            }
            yield f"data: {json.dumps(metrics)}\n\n"
            time.sleep(5)
            
    return Response(generate(), mimetype='text/event-stream')