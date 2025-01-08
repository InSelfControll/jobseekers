from flask import Blueprint

# Create blueprint for authentication routes
auth = Blueprint('auth', __name__, url_prefix='/auth')

# Import views after blueprint creation to avoid circular imports
from . import views

# Export the blueprint
__all__ = ['auth']