
from flask_mail import Mail, Message
from flask import current_app, url_for
import os
from enum import Enum

class EmailProvider(Enum):
    SMTP = 'smtp'
    SENDGRID = 'sendgrid'

mail = Mail()

def send_verification_email(user_email):
    provider = os.environ.get('EMAIL_PROVIDER', 'smtp')
    
    if provider == EmailProvider.SENDGRID.value:
        msg = Message('Verify Your Account',
                    sender=os.environ.get('SENDGRID_FROM_EMAIL', 'noreply@jobhunter.com'),
                    recipients=[user_email])
    else:
        msg = Message('Verify Your Account',
                    sender=os.environ.get('SMTP_FROM_EMAIL', 'noreply@jobhunter.com'),
                    recipients=[user_email])
    
    verification_url = url_for('auth.verify_email', 
                             token=generate_token(user_email), 
                             _external=True)
    
    msg.body = f'''Welcome to Job Hunter!
Please click the following link to verify your account:
{verification_url}

If you did not create this account, please ignore this email.
'''
    mail.send(msg)

def generate_token(email):
    return current_app.ts.dumps(email, salt='email-verify-key')
