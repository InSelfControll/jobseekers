
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

def setup_cert_renewal_check():
    """Set up periodic SSL certificate renewal checks with enhanced monitoring and error handling"""
    from extensions import db, create_app
    from models import Employer
    import schedule
    import time
    import threading
    import logging
    from datetime import datetime, timedelta

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    def notify_admin(employer, message, level='info'):
        """Notify admin about certificate related events"""
        try:
            # Log the notification
            if level == 'error':
                logger.error(f"Certificate notification for {employer.sso_domain}: {message}")
            else:
                logger.info(f"Certificate notification for {employer.sso_domain}: {message}")
            
            # TODO: Implement admin notification system
            # This could be email, Slack, or other notification methods
            pass
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")

    def check_and_renew():
        """Check and renew certificates with enhanced error handling and monitoring"""
        try:
            app = create_app()
            with app.app_context():
                logger.info("Starting certificate renewal check")
                employers = Employer.query.filter_by(ssl_enabled=True).all()
                
                for employer in employers:
                    try:
                        if not employer.sso_domain or not employer.ssl_expiry:
                            logger.warning(f"Incomplete SSL configuration for {employer.sso_domain}")
                            continue
                            
                        days_until_expiry = (employer.ssl_expiry - datetime.now()).days
                        
                        # Alert if certificate is expiring soon
                        if days_until_expiry <= 7:
                            notify_admin(employer, f"Certificate expiring in {days_until_expiry} days", 'error')
                        elif days_until_expiry <= 14:
                            notify_admin(employer, f"Certificate expiring in {days_until_expiry} days", 'info')
                            
                        # Attempt renewal if less than 30 days until expiry
                        if days_until_expiry <= 30:
                            logger.info(f"Initiating certificate renewal for {employer.sso_domain}")
                            ssl_service = SSLService(employer.sso_domain, employer.email)
                            
                            # Attempt renewal with retry logic
                            max_retries = 3
                            for attempt in range(max_retries):
                                try:
                                    success, message = ssl_service.generate_certificate()
                                    if success:
                                        logger.info(f"Successfully renewed certificate for {employer.sso_domain}")
                                        notify_admin(employer, "Certificate renewed successfully")
                                        break
                                    else:
                                        logger.error(f"Renewal attempt {attempt + 1} failed: {message}")
                                        if attempt == max_retries - 1:
                                            notify_admin(employer, f"Certificate renewal failed: {message}", 'error')
                                except Exception as retry_error:
                                    logger.error(f"Renewal attempt {attempt + 1} error: {str(retry_error)}")
                                    if attempt == max_retries - 1:
                                        raise
                                time.sleep(300)  # Wait 5 minutes between retries
                                
                    except Exception as e:
                        logger.error(f"Error processing renewal for {employer.sso_domain}: {str(e)}")
                        notify_admin(employer, f"Certificate renewal error: {str(e)}", 'error')
                        continue
                        
        except Exception as e:
            logger.error(f"Error in certificate renewal check: {str(e)}")

    def run_scheduler():
        """Run the certificate renewal scheduler with improved reliability"""
        try:
            logger.info("Starting SSL certificate renewal scheduler")
            
            # Schedule multiple checks per day to ensure reliability
            schedule.every().day.at("00:00").do(check_and_renew)
            schedule.every().day.at("12:00").do(check_and_renew)
            
            # Add monitoring check every 4 hours
            def monitor_scheduler():
                logger.info("Certificate renewal scheduler health check")
            schedule.every(4).hours.do(monitor_scheduler)
            
            while True:
                try:
                    schedule.run_pending()
                    time.sleep(1800)  # Check every 30 minutes
                except Exception as e:
                    logger.error(f"Error in scheduler loop: {str(e)}")
                    time.sleep(60)  # Wait a minute before retrying
                    
        except Exception as e:
            logger.error(f"Fatal error in SSL renewal scheduler: {str(e)}")
            # Attempt to restart the scheduler
            time.sleep(300)  # Wait 5 minutes before restarting
            run_scheduler()

    # Start the scheduler in a daemon thread
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()
    logger.info("SSL certificate renewal checker initialized with enhanced monitoring")

class SSLService:
    def __init__(self, domain, email):
        self.domain = domain
        self.email = email
        self.cert_dir = '/home/runner/letsencrypt'
        self.live_cert_dir = f'{self.cert_dir}/live/{domain}'
        self.logger = logging.getLogger(__name__)
        
        try:
            # Create cert directory with proper permissions
            os.makedirs(self.cert_dir, exist_ok=True)
            os.chmod(self.cert_dir, 0o755)
            
            # Create logs directory
            logs_dir = os.path.join(self.cert_dir, 'logs')
            os.makedirs(logs_dir, exist_ok=True)
            os.chmod(logs_dir, 0o755)
            
            # Set up logging
            self.logger.setLevel(logging.INFO)
            handler = logging.FileHandler(os.path.join(logs_dir, f'{domain}_ssl.log'))
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)
            
        except Exception as e:
            self.logger.error(f"Error initializing SSL service: {str(e)}")
            raise

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
        """Generate or renew Let's Encrypt SSL certificate with enhanced error handling and cleanup"""
        credentials_path = None
        try:
            self.logger.info(f"Starting certificate process for {self.domain}")
            
            # Check for existing valid certificate
            if self.check_existing_certificate():
                self.logger.info("Valid certificate exists, configuring it")
                return self.configure_certificate()

            # Verify Cloudflare API token
            cloudflare_token = os.getenv('CLOUDFLARE_API_TOKEN')
            if not cloudflare_token:
                self.logger.error("Cloudflare API token not found in secrets")
                return False, "Cloudflare API token not configured"

            # Configure Cloudflare credentials with secure permissions
            credentials_path = f'{self.cert_dir}/cloudflare.ini'
            try:
                with open(credentials_path, 'w') as f:
                    f.write(f"dns_cloudflare_api_token = {cloudflare_token}\n")
                os.chmod(credentials_path, 0o600)
            except Exception as e:
                self.logger.error(f"Failed to write Cloudflare credentials: {str(e)}")
                return False, "Failed to configure Cloudflare credentials"

            # Prepare certbot command with enhanced options
            cmd = [
                'certbot', 'certonly',
                '--dns-cloudflare',
                '--dns-cloudflare-credentials', credentials_path,
                '--non-interactive',
                '--agree-tos',
                '--email', self.email,
                '-d', self.domain,
                '--config-dir', self.cert_dir,
                '--work-dir', self.cert_dir,
                '--logs-dir', os.path.join(self.cert_dir, 'logs'),
                '--preferred-challenges', 'dns-01',
                '--force-renewal',
                '--rsa-key-size', '4096',  # Enhanced security
                '--must-staple',  # Enable OCSP Stapling
                '-v'
            ]

            self.logger.info(f"Running certbot command: {' '.join(cmd)}")
            process = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            if process.returncode != 0:
                error_msg = process.stderr or "Unknown error occurred"
                self.logger.error(f"Certbot error: {error_msg}")
                return False, f"Certificate generation failed: {error_msg}"

            self.logger.info("Certificate generated successfully")
            return self.configure_certificate()
            
        except Exception as e:
            self.logger.error(f"Certificate generation failed: {str(e)}")
            return False, str(e)
            
        finally:
            # Clean up sensitive files
            try:
                if credentials_path and os.path.exists(credentials_path):
                    os.remove(credentials_path)
                    self.logger.info("Cleaned up Cloudflare credentials file")
                    
                # Clean up any temporary files
                temp_dir = os.path.join(self.cert_dir, 'temp')
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    self.logger.info("Cleaned up temporary directory")
            except Exception as e:
                self.logger.error(f"Error cleaning up credentials: {str(e)}")
                # Don't raise the exception as this is cleanup code

    def _set_secure_permissions(self, file_path, mode=0o600):
        """Set secure permissions for certificate files"""
        try:
            if os.path.exists(file_path):
                os.chmod(file_path, mode)
                self.logger.debug(f"Set permissions {mode:o} for {file_path}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to set permissions for {file_path}: {str(e)}")
            return False

    def _get_cert_expiry(self):
        """Get certificate expiry date with enhanced validation"""
        cert_path = os.path.join(self.live_cert_dir, 'cert.pem')
        try:
            if not os.path.exists(cert_path):
                self.logger.error(f"Certificate file not found: {cert_path}")
                return None

            # Verify file permissions
            if not self._set_secure_permissions(cert_path):
                self.logger.warning(f"Failed to set secure permissions for {cert_path}")

            # Get certificate expiry
            output = subprocess.check_output(
                ['openssl', 'x509', '-enddate', '-noout', '-in', cert_path],
                universal_newlines=True)
            expiry_str = output.split('=')[1].strip()
            expiry_date = datetime.strptime(expiry_str, '%b %d %H:%M:%S %Y %Z')

            # Validate expiry date
            if expiry_date < datetime.now():
                self.logger.error("Certificate has already expired")
                return None

            return expiry_date
        except subprocess.CalledProcessError as e:
            self.logger.error(f"OpenSSL command failed: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to get certificate expiry: {str(e)}")
            return None
