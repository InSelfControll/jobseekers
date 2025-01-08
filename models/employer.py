from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import JSON, Text
from extensions import db
from .base import Base
import ssl
import socket
import OpenSSL
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlparse
from functools import lru_cache
import logging

class Employer(Base, UserMixin):
    """
    Employer model representing company/organization accounts in the system.
    Provides employer-specific attributes and authentication support.
    """
    __tablename__ = 'employer'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    company_name = db.Column(db.String(120), nullable=False)
    sso_domain = db.Column(db.String(255), unique=True)
    sso_provider = db.Column(db.String(50))
    sso_config = db.Column(JSON)
    company_domain = db.Column(db.String(120))
    tenant_id = db.Column(db.String(50), unique=True)  # Unique identifier for company's database
    db_name = db.Column(db.String(120))  # Name of company's database
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    is_owner = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    email_footer = db.Column(Text)
    notify_new_applications = db.Column(db.Boolean, default=True)
    notify_status_changes = db.Column(db.Boolean, default=True)
    ssl_enabled = db.Column(db.Boolean, default=False)
    ssl_cert_path = db.Column(db.String(512))
    ssl_key_path = db.Column(db.String(512))
    ssl_expiry = db.Column(db.DateTime)
    domain_verification_date = db.Column(db.DateTime)
    domain_verified = db.Column(db.Boolean, default=False)

    jobs = db.relationship('Job', back_populates='employer', lazy='select')

    def __init__(self, **kwargs):
        super().__init__()
        for key, value in kwargs.items():
            setattr(self, key, value)

    def set_password(self, password):
        """Hash and set the password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if provided password matches hash"""
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

from functools import lru_cache
import socket
import logging
from urllib.parse import urlparse
from datetime import datetime

class DomainValidator:
    def __init__(self, company_domain):
        self.company_domain = company_domain
        self.domain_verified = False
        self.domain_verification_date = None

    @lru_cache(maxsize=128)
    def _resolve_domain(self, domain):
        """
        Cached DNS resolution for domain.
        
        Args:
            domain (str): Domain name to resolve
        
        Returns:
            str: IP address for the domain
        
        Raises:
            socket.gaierror: If domain cannot be resolved
        """
        return socket.gethostbyname(domain)
    def validate_domain(self):
        """
        Validate company domain ownership and accessibility.
        
        Returns:
            tuple: (bool, str) - (success status, message)
        """
        if not self.company_domain:
            return False, "Company domain is not set"

        try:
            # Clean and parse domain
            parsed = urlparse(self.company_domain)
            domain = parsed.netloc or parsed.path
            
            # Remove protocol prefixes and trailing slashes
            domain = domain.rstrip('/').lower()
            if '://' in domain:
                domain = domain.split('://')[-1]
            
            # Basic domain format validation
            if len(domain) > 255:
                return False, "Domain validation failed: Domain too long"
            
            # Check for valid domain parts
            parts = domain.split('.')
            if len(parts) < 2:
                return False, "Domain validation failed: Invalid domain structure"
            
            # Validate each domain part
            for part in parts:
                if not part:
                    return False, "Domain validation failed: Empty domain part"
                if len(part) > 63:
                    return False, "Domain validation failed: Domain part too long"
                if not all(c.isalnum() or c == '-' for c in part):
                    return False, "Domain validation failed: Invalid characters in domain"
                if part.startswith('-') or part.endswith('-'):
                    return False, "Domain validation failed: Domain parts cannot start or end with hyphens"

            # Attempt DNS resolution using cached method
            self._resolve_domain(domain)

            # Update verification status
            self.domain_verified = True
            self.domain_verification_date = datetime.utcnow()
            return True, "Domain verified successfully"
        except socket.gaierror as e:
            logging.error(f"DNS resolution failed for domain {domain}: {str(e)}")
            return False, "Domain validation failed: Unable to resolve DNS"
        except ValueError as e:
            logging.error(f"Invalid domain format for {self.company_domain}: {str(e)}")
            return False, "Domain validation failed: Invalid domain format"
    def validate_ssl_config(self):
        """
        Validate SSL certificate configuration and expiry.
        
        Checks:
        - SSL enablement status
        - Certificate and key file presence
        - Certificate validity and expiration
        - Private key validity
        
        Returns:
            tuple: (bool, str) - (success status, message)
        """
        if not self.ssl_enabled:
            return True, "SSL is not enabled"

        if not (self.ssl_cert_path and self.ssl_key_path):
            return False, "SSL certificate or key path is missing"

        try:
            with open(self.ssl_cert_path, 'rb') as cert_file:
                cert_data = cert_file.read()
                cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert_data)
                
                expiry = datetime.strptime(cert.get_notAfter().decode('ascii'), '%Y%m%d%H%M%SZ')
                self.ssl_expiry = expiry
                
                if expiry < datetime.utcnow():
                    logging.warning(f"SSL certificate expired for {self.company_name}")
                    return False, "SSL certificate has expired"

            with open(self.ssl_key_path, 'rb') as key_file:
                key_data = key_file.read()
                OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, key_data)

            return True, "SSL configuration is valid"
        except FileNotFoundError as e:
            logging.error(f"SSL certificate or key file not found for {self.company_name}: {str(e)}")
            return False, "SSL validation failed: Certificate or key file not found"
        except OpenSSL.crypto.Error as e:
            logging.error(f"Invalid SSL certificate or key for {self.company_name}: {str(e)}")
            return False, "SSL validation failed: Invalid certificate or key format"
        except Exception as e:
            logging.error(f"Unexpected error during SSL validation for {self.company_name}: {str(e)}")
            return False, "SSL validation failed: Unexpected error occurred"
