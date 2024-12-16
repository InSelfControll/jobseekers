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
        self.cert_dir = '/home/runner/letsencrypt'
        
        # Create cert directory
        os.makedirs(self.cert_dir, exist_ok=True)
        os.chmod(self.cert_dir, 0o755)

    def generate_certificate(self):
        """Generate a new Let's Encrypt SSL certificate using Cloudflare DNS challenge"""
        try:
            logging.info(f"Starting certificate generation for {self.domain}")

            # Get Cloudflare API token from Replit secrets
            cloudflare_token = os.getenv('CLOUDFLARE_API_TOKEN')
            if not cloudflare_token:
                logging.error("Cloudflare API token not found in secrets")
                return False, "Cloudflare API token not configured"

            # Create credentials file for Cloudflare
            os.makedirs('/home/runner/letsencrypt/', exist_ok=True)
            credentials_path = '/home/runner/letsencrypt/cloudflare.ini'
            with open(credentials_path, 'w') as f:
                f.write(f"dns_cloudflare_api_token = {cloudflare_token}\n")
            os.chmod(credentials_path, 0o600)

            logging.info("Cloudflare credentials configured")

            cmd = [
                'certbot', 'certonly', '--dns-cloudflare',
                '--dns-cloudflare-credentials', credentials_path,
                '--non-interactive', '--agree-tos', '--email', self.email,
                '-d', self.domain, '--config-dir', '/home/runner/letsencrypt/',
                '--work-dir', '/home/runner/letsencrypt/', '--logs-dir',
                '/home/runner/letsencrypt/', '--preferred-challenges',
                'dns-01', '-v'
            ]

            logging.info(f"Executing certbot command: {' '.join(cmd)}")

            process = subprocess.run(cmd,
                                     capture_output=True,
                                     text=True,
                                     check=False)

            if process.stdout:
                logging.info(f"Certbot output: {process.stdout}")
            if process.stderr:
                logging.error(f"Certbot error output: {process.stderr}")

            if process.returncode != 0:
                return False, f"Certificate generation failed: {process.stderr}"

            # Update certificate paths in database
            employer = Employer.query.filter_by(sso_domain=self.domain).first()
            if not employer:
                return False, "Employer not found"

            cert_path = os.path.join('/home/runner/letsencrypt/live',
                                     self.domain, 'fullchain.pem')
            key_path = os.path.join('/home/runner/letsencrypt/live',
                                    self.domain, 'privkey.pem')

            if not os.path.exists(cert_path) or not os.path.exists(key_path):
                return False, "Certificate files not generated"

            employer.ssl_cert_path = cert_path
            employer.ssl_key_path = key_path
            employer.ssl_enabled = True
            employer.ssl_expiry = self._get_cert_expiry()
            employer.domain_verified = True

            db.session.commit()
            logging.info(
                "SSL certificate generated and configured successfully")
            return True, "Certificate generated and configured successfully"

        except Exception as e:
            logging.error(
                f"Certificate generation failed with error: {str(e)}")
            return False, str(e)

    def _get_cert_expiry(self):
        """Get certificate expiry date"""
        cert_path = os.path.join('/home/runner/letsencrypt/live', self.domain,
                                 'cert.pem')
        try:
            output = subprocess.check_output(
                ['openssl', 'x509', '-enddate', '-noout', '-in', cert_path],
                universal_newlines=True)
            expiry_str = output.split('=')[1].strip()
            return datetime.strptime(expiry_str, '%b %d %H:%M:%S %Y %Z')
        except Exception as e:
            logging.error(f"Failed to get certificate expiry: {str(e)}")
            return None