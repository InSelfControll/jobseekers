from flask import render_template, jsonify
from werkzeug.exceptions import HTTPException

def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request_error(error):
        if request_wants_json():
            return jsonify(error="Bad Request"), 400
        return render_template('errors/400.html'), 400

    @app.errorhandler(401)
    def unauthorized_error(error):
        if request_wants_json():
            return jsonify(error="Unauthorized"), 401
        return render_template('errors/401.html'), 401

    @app.errorhandler(403)
    def forbidden_error(error):
        if request_wants_json():
            return jsonify(error="Forbidden"), 403
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        if request_wants_json():
            return jsonify(error="Not Found"), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        if request_wants_json():
            return jsonify(error="Internal Server Error"), 500
        return render_template('errors/500.html'), 500

    @app.errorhandler(HTTPException)
    def handle_exception(e):
        if request_wants_json():
            return jsonify(error=str(e)), e.code
        return render_template(f'errors/{e.code}.html'), e.code

def request_wants_json():
    """Check if the request wants a JSON response"""
    best = request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']
