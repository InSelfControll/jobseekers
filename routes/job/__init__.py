from flask import Blueprint
from models.job import Job

# Create blueprint for job routes
bp = Blueprint('job', __name__)

# Import routes after blueprint creation to avoid circular imports
from . import routes  # noqa

# Export the blueprint
__all__ = ['bp']