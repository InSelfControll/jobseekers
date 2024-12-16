
import os
import time
from datetime import datetime, timedelta
import subprocess
import logging
from models import Employer
from extensions import db, create_app
from certbot import main as certbot_main
from flask import current_app
import shutil

class SSLService:
    def __init__(self, domain, email):
        self.domain = domain
        self.email = email
        self.cert_dir = '/home/runner/letsencrypt'
        self.live_cert_dir = f'{self.cert_dir}/live/{domain}'
        
        # Create cert directory
        os.makedirs(self.cert_dir, exist_ok=True)
        os.chmod(self.cert_dir, 0o755)

    def check_existing_certificate(self):
        """Check if valid certificate exists for domain"""
        if not os.path.exists(self.live_cert_dir):
            return False
            
        try:
            # Check certificate expiry
            cert_path = os.path.join(self.live_cert_dir, 'cert.pem')
            if not os.path.exists(cert_path):
                return False
                
            output = subprocess.check_output(
                ['openssl', 'x509', '-enddate', '-noout', '-in', cert_path],
                universal_newlines=True)
            expiry_str = output.split('=')[1].strip()
            expiry_date = datetime.strptime(expiry_str, '%b %d %H:%M:%S %Y %Z')
            
            # Return True if certificate is still valid (not expired)
            return expiry_date > datetime.now()
        except Exception as e:
            logging.error(f"Error checking certificate: {str(e)}")
            return False

    def configure_certificate(self):
        """Configure existing certificate for the domain"""
        try:
            cert_path = os.path.join(self.live_cert_dir, 'fullchain.pem')
            key_path = os.path.join(self.live_cert_dir, 'privkey.pem')
            
            if not os.path.exists(cert_path) or not os.path.exists(key_path):
                return False, "Certificate files not found"

            employer = Employer.query.filter_by(sso_domain=self.domain).first()
            if not employer:
                return False, "Employer not found"

            employer.ssl_cert_path = cert_path
            employer.ssl_key_path = key_path
            employer.ssl_enabled = True
            employer.ssl_expiry = self._get_cert_expiry()
            employer.domain_verified = True

            db.session.commit()
            logging.info("SSL certificate configured successfully")
            return True, "Certificate configured successfully"
        except Exception as e:
            logging.error(f"Certificate configuration failed: {str(e)}")
            return False, str(e)

    def generate_certificate(self):
        """Generate or renew Let's Encrypt SSL certificate"""
        try:
            logging.info(f"Starting certificate process for {self.domain}")
            
            # Check for existing valid certificate
            if self.check_existing_certificate():
                logging.info("Valid certificate exists, configuring it")
                return self.configure_certificate()

            # Get Cloudflare API token from Replit secrets
            cloudflare_token = os.getenv('CLOUDFLARE_API_TOKEN')
            if not cloudflare_token:
                logging.error("Cloudflare API token not found in secrets")
                return False, "Cloudflare API token not configured"

            # Configure Cloudflare credentials
            credentials_path = f'{self.cert_dir}/cloudflare.ini'
            with open(credentials_path, 'w') as f:
                f.write(f"dns_cloudflare_api_token = {cloudflare_token}\n")
            os.chmod(credentials_path, 0o600)

            cmd = [
                'certbot', 'certonly', '--dns-cloudflare',
                '--dns-cloudflare-credentials', credentials_path,
                '--non-interactive', '--agree-tos', '--email', self.email,
                '-d', self.domain, '--config-dir', self.cert_dir,
                '--work-dir', self.cert_dir, '--logs-dir',
                self.cert_dir, '--preferred-challenges', 'dns-01',
                '--force-renewal', '-v'
            ]

            process = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            if process.returncode != 0:
                logging.error(f"Certbot error: {process.stderr}")
                return False, f"Certificate generation failed: {process.stderr}"

            # Configure the newly generated certificate
            return self.configure_certificate()

        except Exception as e:
            logging.error(f"Certificate generation failed: {str(e)}")
            return False, str(e)

    def _get_cert_expiry(self):
        """Get certificate expiry date"""
        cert_path = os.path.join(self.live_cert_dir, 'cert.pem')
        try:
            output = subprocess.check_output(
                ['openssl', 'x509', '-enddate', '-noout', '-in', cert_path],
                universal_newlines=True)
            expiry_str = output.split('=')[1].strip()
            return datetime.strptime(expiry_str, '%b %d %H:%M:%S %Y %Z')
        except Exception as e:
            logging.error(f"Failed to get certificate expiry: {str(e)}")
            return None
