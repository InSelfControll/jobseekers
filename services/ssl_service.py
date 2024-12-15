import os
import time
from datetime import datetime, timedelta
import subprocess
import logging
from models import Employer
from extensions import db, create_app
import certbot.main
from flask import current_app

from certbot import main as certbot
import os
from flask import current_app
from models import Employer
from extensions import db

class SSLService:
    def __init__(self, domain, email):
        self.domain = domain
        self.email = email
        self.cert_dir = os.path.join(current_app.root_path, 'ssl', 'letsencrypt')
        self.webroot_path = os.path.join(current_app.root_path, 'static', '.well-known')
        os.makedirs(self.cert_dir, exist_ok=True)
        os.makedirs(self.webroot_path, exist_ok=True)
        
    def generate_certificate(self):
        """Generate a new Let's Encrypt SSL certificate"""
        try:
            certbot_args = [
                'certonly',
                '--webroot',
                '--webroot-path', self.webroot_path,
                '--email', self.email,
                '--agree-tos',
                '--no-eff-email',
                '-d', self.domain,
                '--config-dir', self.cert_dir,
                '--work-dir', os.path.join(self.cert_dir, 'work'),
                '--logs-dir', os.path.join(self.cert_dir, 'logs'),
                '--non-interactive'
            ]
            
            certbot.main.main(certbot_args)
            
            # Update certificate paths in database
            employer = Employer.query.filter_by(sso_domain=self.domain).first()
            if employer:
                employer.ssl_cert_path = os.path.join(self.cert_dir, 'live', self.domain, 'fullchain.pem')
                employer.ssl_key_path = os.path.join(self.cert_dir, 'live', self.domain, 'privkey.pem')
                employer.ssl_enabled = True
                employer.ssl_expiry = self._get_cert_expiry()
                db.session.commit()
            
            return True, "Certificate generated successfully"
            
        except Exception as e:
            logging.error(f"Certificate generation failed: {str(e)}")
            return False, str(e)
            
    def renew_certificate(self):
        """Renew the SSL certificate if it's close to expiry"""
        try:
            employer = Employer.query.filter_by(sso_domain=self.domain).first()
            if not employer or not employer.ssl_enabled:
                return False, "No certificate found for domain"
                
            if not self._needs_renewal(employer.ssl_expiry):
                return True, "Certificate still valid"
                
            certbot_args = [
                'renew',
                '--webroot',
                '--webroot-path', self.webroot_path,
                '--config-dir', self.cert_dir,
                '--work-dir', os.path.join(self.cert_dir, 'work'),
                '--logs-dir', os.path.join(self.cert_dir, 'logs'),
                '--non-interactive'
            ]
            
            certbot.main.main(certbot_args)
            
            # Update certificate expiry in database
            employer.ssl_expiry = self._get_cert_expiry()
            db.session.commit()
            
            return True, "Certificate renewed successfully"
            
        except Exception as e:
            logging.error(f"Certificate renewal failed: {str(e)}")
            return False, str(e)
            
    def _needs_renewal(self, expiry_date):
        """Check if certificate needs renewal (30 days before expiry)"""
        if not expiry_date:
            return True
        return datetime.utcnow() + timedelta(days=30) >= expiry_date
        
    def _get_cert_expiry(self):
        """Get certificate expiry date"""
        cert_path = os.path.join(self.cert_dir, 'live', self.domain, 'cert.pem')
        try:
            output = subprocess.check_output(
                ['openssl', 'x509', '-enddate', '-noout', '-in', cert_path],
                universal_newlines=True
            )
            expiry_str = output.split('=')[1].strip()
            return datetime.strptime(expiry_str, '%b %d %H:%M:%S %Y %Z')
        except:
            return None

def setup_cert_renewal_check():
    """Setup periodic certificate renewal checks"""
    app = create_app()
    with app.app_context():
        while True:
            try:
                employers = Employer.query.filter_by(ssl_enabled=True).all()
                for employer in employers:
                    if employer.sso_domain and employer.email:
                        ssl_service = SSLService(employer.sso_domain, employer.email)
                        success, message = ssl_service.renew_certificate()
                        if not success:
                            logging.error(f"Failed to renew certificate for {employer.sso_domain}: {message}")
            except Exception as e:
                logging.error(f"Certificate renewal check failed: {str(e)}")
            # Sleep for 24 hours before next check
            time.sleep(86400)
