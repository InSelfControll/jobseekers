
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from functools import wraps
import os
from models import Employer

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
