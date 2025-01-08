yea tfrom flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email
from models import Employer
from extensions import db
from core.db_utils import session_scope
from services.logging_service import logging_service
from jinja2.exceptions import TemplateError

logger = logging_service.get_structured_logger(__name__)

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    company_name = StringField('Company Name', validators=[DataRequired()])
    submit = SubmitField('Register')

auth_bp = Blueprint('auth', __name__)

# routes/auth/routes.py
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('employer.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        employer = Employer.query.filter_by(email=email).first()
        if employer and employer.check_password(password):
            login_user(employer, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('employer.dashboard'))
            
        flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('employer.dashboard'))
    
    try:
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            company_name = request.form.get('company_name')
            
            with session_scope() as session:
                if session.query(Employer).filter_by(email=email).first():
                    logger.info(f'Registration attempt with existing email: {email}')
                    flash('This email is already registered. Please use a different email or try logging in.', 'danger')
                    return redirect(url_for('auth.register'))
                
                employer = Employer(email=email, company_name=company_name)
                employer.set_password(password)
                
                session.add(employer)
                session.commit()
                
                login_user(employer)
                logger.info(f'New employer registered: {email}')
                return redirect(url_for('employer.dashboard'))
        
        form = RegistrationForm()
        return render_template('auth/register.html', form=form)
    except TemplateError as e:
        logger.error(f'Template rendering error in registration: {str(e)}')
        return render_template('errors/500.html'), 500
    except Exception as e:
        logger.error(f'Unexpected error in registration: {str(e)}')
        flash('An unexpected error occurred during registration. Please try again later.', 'danger')
        return render_template('errors/500.html'), 500