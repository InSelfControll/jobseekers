
from functools import wraps
from flask import current_app, request, redirect, g
from urllib.parse import urljoin

def ssl_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if hasattr(g, 'custom_domain') and g.custom_domain:
            if not request.is_secure:
                url = request.url.replace('http://', 'https://', 1)
                return redirect(url, code=301)
        return f(*args, **kwargs)
    return decorated_function
