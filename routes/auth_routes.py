from quart import Blueprint, render_template, redirect, url_for, request
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import Employer
from extensions import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        employer = Employer.query.filter_by(email=email).first()
        if employer and check_password_hash(employer.password_hash, password):
            login_user(employer)
            return redirect(url_for('employer.dashboard'))
        
        flash('Invalid email or password', 'error')
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        company_name = request.form.get('company_name')
        password = request.form.get('password')
        
        if Employer.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('auth.register'))
        
        employer = Employer(
            email=email,
            company_name=company_name,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(employer)
        db.session.commit()
        
        flash('Registration successful!', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
