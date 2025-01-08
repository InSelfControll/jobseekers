from flask import Blueprint

# Create the admin blueprint with url_prefix
admin = Blueprint('admin', __name__, url_prefix='/admin')

# Import all admin routes
from . import email_settings
from . import domain_config 
from . import sso_config
from . import bot_monitoring

# Export the blueprint
__all__ = ['admin']