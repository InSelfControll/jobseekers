from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from models import Employer
from extensions import db, logger
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

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

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('employer.dashboard'))
        
    form = LoginForm()
    error = None
    
    if form.validate_on_submit():
        try:
            email = form.email.data
            password = form.password.data
            
            # Use current_app to ensure we're in the application context
            with current_app.app_context():
                employer = Employer.query.filter_by(email=email).first()
            if employer and employer.check_password(password):
                login_user(employer)
                return redirect(url_for('employer.dashboard'))
            else:
                error = 'Invalid email or password'
                
        except SQLAlchemyError as e:
            logger.error(f"Database error during login: {str(e)}")
            error = 'Database connection error. Please try again later.'
        except Exception as e:
            logger.error(f"Unexpected error during login: {str(e)}")
            error = 'An unexpected error occurred. Please try again.'
    
    if error:
        flash(error, 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('employer_dashboard'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        company_name = form.company_name.data
        
        if Employer.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('auth.register'))
            
        employer = Employer(email=email, company_name=company_name)
        employer.set_password(password)
        
        try:
            logger.info(f"Attempting to register new employer with email: {email}")
            db.session.add(employer)
            db.session.commit()
            
            logger.info(f"Successfully registered employer: {email}")
            login_user(employer)
            return redirect(url_for('employer.dashboard'))
            
        except IntegrityError as e:
            logger.error(f"Database integrity error during registration: {str(e)}")
            db.session.rollback()
            flash('Email already registered', 'danger')
            return redirect(url_for('auth.register'))
            
        except SQLAlchemyError as e:
            logger.error(f"Database error during registration: {str(e)}")
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            return redirect(url_for('auth.register'))
            
        except Exception as e:
            logger.error(f"Unexpected error during registration: {str(e)}")
            db.session.rollback()
            flash('An unexpected error occurred. Please try again.', 'danger')
            return redirect(url_for('auth.register'))
    form = RegistrationForm()
    return render_template('auth/register.html', form=form)
