from flask import Blueprint, render_template
from flask_login import login_required

employer_bp = Blueprint('employer', __name__)

@employer_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('employer/dashboard.html')
