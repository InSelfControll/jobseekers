from flask import render_template, request
from sqlalchemy.exc import SQLAlchemyError
from jinja2.exceptions import TemplateError
from services.logging_service import logging_service

logger = logging_service.get_structured_logger(__name__)

def register_error_handlers(app):
    """Register all error handlers for the application"""
    app.register_error_handler(404, not_found_error)
    app.register_error_handler(500, internal_error)
    app.register_error_handler(SQLAlchemyError, database_error)
    app.register_error_handler(TemplateError, template_error)
    app.register_error_handler(Exception, general_error)

def internal_error(error):
    """Handle 500 internal server errors"""
    logger.error(f'Internal Server Error: {str(error)}')
    return render_template('errors/500.html'), 500

def not_found_error(error):
    """Handle 404 not found errors"""
    logger.warning(f'Page Not Found: {request.url}')
    return render_template('errors/404.html'), 404

def database_error(error):
    """Handle SQLAlchemy database errors"""
    logger.error(f'Database Error: {str(error)}')
    return render_template('errors/500.html'), 500

def template_error(error):
    """Handle template rendering errors"""
    logger.error(f'Template Error: {str(error)}')
    return render_template('errors/500.html'), 500

def general_error(error):
    """Handle any unhandled exceptions"""
    logger.error(f'Unhandled Exception: {str(error)}')
    return render_template('errors/500.html'), 500
