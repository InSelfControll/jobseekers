import time
import logging
from functools import wraps
from flask import request, abort, current_app, session, g
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import hmac
import hashlib
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)

def init_csrf(app):
    """Initialize CSRF protection and rate limiting"""
    csrf.init_app(app)
    limiter.init_app(app)
    
    # Enhanced CSRF security settings
    app.config.update({
        'WTF_CSRF_TIME_LIMIT': 3600,  # 1 hour
        'WTF_CSRF_SSL_STRICT': False,  # Less strict for development
        'WTF_CSRF_METHODS': ['POST', 'PUT', 'PATCH', 'DELETE'],
        'WTF_CSRF_CHECK_DEFAULT': True,
        'WTF_CSRF_ENABLED': True,
        'CSRF_COOKIE_SECURE': False,  # Allow non-HTTPS for development
        'CSRF_COOKIE_HTTPONLY': True,
        'CSRF_COOKIE_SAMESITE': 'Lax',  # Less strict SameSite policy
        'WTF_CSRF_CHECK_REFERRER': False,  # Disable referrer check
        'WTF_CSRF_SSL_STRICT': False,      # Allow non-HTTPS during development
        'WTF_CSRF_TIME_LIMIT': 3600,       # 1 hour token lifetime
    })
    
    # Register security headers and token generator
    @app.after_request
    def add_security_headers(response):
        # Add security headers
        response.headers.update({
            'X-Frame-Options': 'SAMEORIGIN',
            'X-Content-Type-Options': 'nosniff',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';",
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
        })

        # Add CSRF token for HTML responses
        if 'text/html' in response.headers.get('Content-Type', ''):
            token = generate_csrf()
            # Store token hash with timestamp in session
            timestamp = int(time.time())
            session['csrf_token_hash'] = {
                'hash': hmac.new(
                    current_app.secret_key.encode(),
                    f"{token}{timestamp}".encode(),
                    hashlib.sha256
                ).hexdigest(),
                'timestamp': timestamp
            }
            
            response.set_cookie(
                'csrf_token',
                token,
                secure=True,
                httponly=True,
                samesite='Strict',
                max_age=3600,  # 1 hour
                domain=request.host.split(':')[0],
                path='/'
            )
        return response

def csrf_protected(func):
    """Enhanced decorator for routes that require CSRF protection with rate limiting"""
    
    # Apply rate limiting
    rate_limited = limiter.limit("5 per minute")(func)
    
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if request.method not in ['GET', 'HEAD', 'OPTIONS']:
            # Validate request origin
            origin = request.headers.get('Origin')
            if origin:
                allowed_origins = current_app.config.get('ALLOWED_ORIGINS', [])
                if not any(origin.endswith(allowed) for allowed in allowed_origins):
                    logger.warning(f"Invalid origin: {origin}")
                    abort(403, "Invalid origin")

            # Get token from multiple possible locations
            token = (
                request.form.get('csrf_token') or
                request.headers.get('X-CSRF-Token') or
                request.headers.get('X-CSRFToken')
            )
            
            if not token:
                logger.warning("CSRF token missing")
                abort(403, "CSRF token missing")
                
            try:
                csrf.protect()
                
                # Enhanced double-submit validation with timestamp check
                stored_data = session.get('csrf_token_hash')
                if not stored_data:
                    logger.warning("CSRF session expired")
                    abort(403, "CSRF session expired")
                
                stored_hash = stored_data['hash']
                timestamp = stored_data['timestamp']
                
                # Verify token age
                if int(time.time()) - timestamp > current_app.config['WTF_CSRF_TIME_LIMIT']:
                    logger.warning("CSRF token expired")
                    abort(403, "CSRF token expired")
                
                # Calculate and verify token hash
                current_hash = hmac.new(
                    current_app.secret_key.encode(),
                    f"{token}{timestamp}".encode(),
                    hashlib.sha256
                ).hexdigest()
                
                if not hmac.compare_digest(stored_hash, current_hash):
                    logger.warning("CSRF token mismatch")
                    abort(403, "CSRF token mismatch")
                    
            except Exception as e:
                logger.error(f"CSRF validation error: {str(e)}")
                abort(403, "Invalid CSRF token")
                
        return rate_limited(*args, **kwargs)
    return decorated_function

def exempt_csrf(view_function):
    """Mark a view function as exempt from CSRF protection"""
    if isinstance(view_function, str):
        view_function = current_app.view_functions[view_function]
    view_function.csrf_exempt = True
    return view_function
