import os
import logging
from typing import Dict, Optional, Tuple
import jinja2
from models import Employer
from services.ssl_service import SSLService
from extensions import db

logger = logging.getLogger(__name__)

class DomainService:
    def __init__(self):
        self.nginx_template_dir = os.path.join(os.path.dirname(__file__), '../templates/nginx')
        self.nginx_sites_dir = '/etc/nginx/sites-available'
        self.nginx_enabled_dir = '/etc/nginx/sites-enabled'
        
        # Ensure directories exist
        os.makedirs(self.nginx_template_dir, exist_ok=True)
        os.makedirs(self.nginx_sites_dir, exist_ok=True)
        os.makedirs(self.nginx_enabled_dir, exist_ok=True)
        
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.nginx_template_dir)
        )

    async def setup_custom_domain(self, employer_id: int) -> Tuple[bool, str]:
        """
        Complete domain setup process including SSL and Nginx configuration
        """
        try:
            employer = Employer.query.get(employer_id)
            if not employer or not employer.domain_verified:
                return False, "Domain not verified"

            # 1. Setup SSL certificate
            ssl_service = SSLService(employer.sso_domain, employer.email)
            if employer.ssl_enabled:
                # Verify existing certificate
                if not ssl_service.check_existing_certificate():
                    return False, "SSL certificate validation failed"
            else:
                # Generate new certificate
                success, message = await ssl_service.generate_certificate()
                if not success:
                    return False, f"SSL certificate generation failed: {message}"
                
                employer.ssl_enabled = True
                employer.ssl_cert_path = ssl_service.get_cert_path()
                employer.ssl_key_path = ssl_service.get_key_path()
                employer.ssl_expiry = ssl_service._get_cert_expiry()

            # 2. Generate and deploy Nginx configuration
            success, message = self._deploy_nginx_config(employer)
            if not success:
                return False, f"Nginx configuration failed: {message}"

            # 3. Configure SSO
            success, message = self._configure_sso(employer)
            if not success:
                return False, f"SSO configuration failed: {message}"

            db.session.commit()
            return True, "Domain setup completed successfully"

        except Exception as e:
            logger.exception("Error in setup_custom_domain")
            db.session.rollback()
            return False, str(e)

    def _deploy_nginx_config(self, employer: Employer) -> Tuple[bool, str]:
        """
        Generate and deploy Nginx configuration for the custom domain
        """
        try:
            template = self.template_env.get_template('custom_domain.conf.j2')
            config_content = template.render(
                domain=employer.sso_domain,
                ssl_cert=employer.ssl_cert_path,
                ssl_key=employer.ssl_key_path,
                upstream_app="localhost:3000"
            )

            config_path = os.path.join(self.nginx_sites_dir, f"{employer.sso_domain}.conf")
            enabled_path = os.path.join(self.nginx_enabled_dir, f"{employer.sso_domain}.conf")

            # Write configuration
            with open(config_path, 'w') as f:
                f.write(config_content)

            # Enable site if not already enabled
            if not os.path.exists(enabled_path):
                os.symlink(config_path, enabled_path)

            # Test Nginx configuration
            if os.system('nginx -t') != 0:
                raise Exception("Invalid Nginx configuration")

            # Reload Nginx
            if os.system('systemctl reload nginx') != 0:
                raise Exception("Failed to reload Nginx")

            return True, "Nginx configuration deployed successfully"

        except Exception as e:
            logger.exception("Error in _deploy_nginx_config")
            return False, str(e)

    def _configure_sso(self, employer: Employer) -> Tuple[bool, str]:
        """
        Configure SSO settings for the custom domain
        """
        try:
            if not employer.sso_provider:
                return True, "No SSO provider configured"

            if employer.sso_provider == 'AZURE':
                return self._configure_azure_sso(employer)
            elif employer.sso_provider == 'GITHUB':
                return self._configure_github_sso(employer)
            else:
                return False, f"Unsupported SSO provider: {employer.sso_provider}"

        except Exception as e:
            logger.exception("Error in _configure_sso")
            return False, str(e)

    def _configure_azure_sso(self, employer: Employer) -> Tuple[bool, str]:
        """
        Configure Azure AD SSO settings
        """
        try:
            if not employer.sso_config or 'manifest' not in employer.sso_config:
                return False, "Azure AD manifest not provided"

            # Update SSO config with custom domain URLs
            employer.sso_config.update({
                'reply_url': f"https://{employer.sso_domain}/auth/saml/callback",
                'logout_url': f"https://{employer.sso_domain}/auth/saml/logout"
            })

            return True, "Azure SSO configured successfully"

        except Exception as e:
            logger.exception("Error in _configure_azure_sso")
            return False, str(e)

    def _configure_github_sso(self, employer: Employer) -> Tuple[bool, str]:
        """
        Configure GitHub SSO settings
        """
        try:
            if not employer.sso_config or 'client_id' not in employer.sso_config:
                return False, "GitHub SSO credentials not provided"

            # Update SSO config with custom domain URLs
            employer.sso_config.update({
                'callback_url': f"https://{employer.sso_domain}/auth/github/callback",
                'return_url': f"https://{employer.sso_domain}/auth/github/return"
            })

            return True, "GitHub SSO configured successfully"

        except Exception as e:
            logger.exception("Error in _configure_github_sso")
            return False, str(e)
