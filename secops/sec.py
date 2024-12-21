from functools import wraps
from flask import request, abort, current_app, session
from flask_wtf.csrf import CSRFProtect, generate_csrf
import hmac
import hashlib
import time

csrf = CSRFProtect()

def init_csrf(app):
    """Initialize CSRF protection for the application"""
    csrf.init_app(app)
    
    # Enhanced CSRF security settings
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour
    app.config['WTF_CSRF_SSL_STRICT'] = True
    app.config['WTF_CSRF_METHODS'] = ['POST', 'PUT', 'PATCH', 'DELETE']
    app.config['WTF_CSRF_CHECK_DEFAULT'] = True
    app.config['WTF_CSRF_ENABLED'] = True
    
    # Register token generator with enhanced security
    @app.after_request
    def add_csrf_token(response):
        if 'text/html' in response.headers.get('Content-Type', ''):
            token = generate_csrf()
            # Store token hash in session for double-submit validation
            session['csrf_token_hash'] = hmac.new(
                app.secret_key.encode(),
                token.encode(),
                hashlib.sha256
            ).hexdigest()
            
            response.set_cookie(
                'csrf_token',
                token,
                secure=True,
                httponly=True,
                samesite='Strict',
                max_age=3600  # 1 hour
            )
        return response

def csrf_protected(func):
    """Enhanced decorator for routes that require CSRF protection"""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if request.method not in ['GET', 'HEAD', 'OPTIONS']:
            # Get token from multiple possible locations
            token = (
                request.form.get('csrf_token') or
                request.headers.get('X-CSRF-Token') or
                request.headers.get('X-CSRFToken')
            )
            
            if not token:
                abort(403, "CSRF token missing")
                
            try:
                # Use the public validate_csrf method instead
                csrf.protect()
                
                # Additional double-submit validation
                stored_hash = session.get('csrf_token_hash')
                if not stored_hash:
                    abort(403, "CSRF session expired")
                    
                current_hash = hmac.new(
                    current_app.secret_key.encode(),
                    token.encode(),
                    hashlib.sha256
                ).hexdigest()
                
                if not hmac.compare_digest(stored_hash, current_hash):
                    abort(403, "CSRF token mismatch")
                    
            except Exception:
                abort(403, "Invalid CSRF token")
                
        return func(*args, **kwargs)
    return decorated_function

def exempt_csrf(view_function):
    """Mark a view function as exempt from CSRF protection"""
    if isinstance(view_function, str):
        view_function = current_app.view_functions[view_function]
    view_function.csrf_exempt = True
    return view_function
