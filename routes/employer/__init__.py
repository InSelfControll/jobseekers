from flask import Blueprint

# Create employer blueprint with template folder configuration
employer = Blueprint('employer', __name__, 
                    template_folder='../../templates/employer')

# Import route handlers
from . import routes

except ImportError:
    from routes.employer import routes

# Export the blueprint
__all__ = ['employer']
