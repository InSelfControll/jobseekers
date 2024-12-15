import os
import time
from datetime import datetime, timedelta
import subprocess
import logging
from models import Employer
from extensions import db, create_app
from certbot import main as certbot_main
from flask import current_app

class SSLService:
    def __init__(self, domain, email):
        self.domain = domain
        self.email = email
        self.cert_dir = os.path.join(current_app.root_path, 'ssl', 'letsencrypt')
        self.webroot_path = os.path.join(current_app.root_path, 'static')
        self.acme_path = os.path.join(self.webroot_path, '.well-known', 'acme-challenge')
        
        # Ensure all directories exist with proper permissions
        os.makedirs(self.cert_dir, exist_ok=True)
        os.makedirs(self.acme_path, exist_ok=True)
        os.chmod(self.webroot_path, 0o755)
        os.chmod(os.path.join(self.webroot_path, '.well-known'), 0o755)
        os.chmod(self.acme_path, 0o755)
        
    def generate_certificate(self):
        """Generate a new Let's Encrypt SSL certificate"""
        try:
            import subprocess
            
            cmd = [
                'certbot', 'certonly',
                '--webroot',
                '--webroot-path', self.webroot_path,
                '--preferred-challenges', 'http-01',
                '--email', self.email,
                '--agree-tos',
                '--no-eff-email',
                '-d', self.domain,
                '--config-dir', self.cert_dir,
                '--work-dir', os.path.join(self.cert_dir, 'work'),
                '--logs-dir', os.path.join(self.cert_dir, 'logs'),
                '--non-interactive'
            ]
            
            process = subprocess.run(cmd, capture_output=True, text=True)
            if process.returncode != 0:
                return False, f"Certificate generation failed: {process.stderr}"
            
            # Update certificate paths in database
            employer = Employer.query.filter_by(sso_domain=self.domain).first()
            if employer:
                cert_path = os.path.join(self.cert_dir, 'live', self.domain, 'fullchain.pem')
                key_path = os.path.join(self.cert_dir, 'live', self.domain, 'privkey.pem')
                
                if os.path.exists(cert_path) and os.path.exists(key_path):
                    employer.ssl_cert_path = cert_path
                    employer.ssl_key_path = key_path
                    employer.ssl_enabled = True
                    employer.ssl_expiry = self._get_cert_expiry()
                    
                    # Configure the domain with SSL
                    employer.domain_verified = True
                    employer.sso_domain = self.domain
                    db.session.commit()
                    
                    return True, "Certificate generated and domain configured successfully"
                else:
                    return False, "Certificate files not found"
            
            return False, "Employer not found"
            
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
            
            certbot_main.main(certbot_args)
            
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