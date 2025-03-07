import logging
import os
from flask import Flask, jsonify, request
from api.routes import bp as api_bp
from web.routes import bp as web_bp
from web.monitoring import bp as monitoring_bp
from services.vector_store import init_vector_store

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

def create_app():
    """Application factory function"""
    logger.info("=== Starting Flask PDF Processing Application ===")
    logger.info("Debug logs will be written to 'app.log' in the project root directory")

    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET")
    if not app.secret_key:
        logger.error("SESSION_SECRET environment variable not set")
        raise ValueError("SESSION_SECRET environment variable is required")

    # Disable Flask's default redirect behavior
    app.url_map.strict_slashes = False

    # Defer vector store initialization until first request
    @app.before_request
    def initialize_vector_store():
        if not hasattr(app, '_vector_store_initialized'):
            try:
                logger.info("Starting vector store initialization...")
                init_vector_store()
                logger.info("Vector store initialized successfully")
                app._vector_store_initialized = True
            except Exception as e:
                logger.error(f"Failed to initialize vector store: {str(e)}", exc_info=True)
                # Individual endpoints will handle vector store failures

    # Register blueprints
    logger.info("Registering blueprints...")
    # Register API routes first to ensure they have precedence
    app.register_blueprint(api_bp)
    # Register monitoring routes
    app.register_blueprint(monitoring_bp)
    # Register web interface routes last
    app.register_blueprint(web_bp)

    # Add CORS headers to all responses
    @app.after_request
    def after_request(response):
        logger.debug(f"Processing request: {request.method} {request.path}")
        logger.debug(f"Request headers: {dict(request.headers)}")
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response headers: {dict(response.headers)}")

        # For API routes, ensure JSON response
        if request.path.startswith('/api/'):
            logger.debug("API route detected, ensuring JSON response")
            # Only set Content-Type if it's not already set (for file uploads etc)
            if 'Content-Type' not in response.headers:
                response.headers['Content-Type'] = 'application/json'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            # Prevent redirects for API routes
            response.headers.pop('Location', None)
            response.autocorrect_location_header = False

        # Add CORS headers for all responses
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        return response

    # Error handlers for API routes
    @app.errorhandler(404)
    def not_found(error):
        logger.error(f"404 error for path: {request.path}")
        if request.path.startswith('/api/'):
            return jsonify({"error": "Resource not found"}), 404
        return web_bp.error_handler(error)

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 error for path: {request.path}")
        if request.path.startswith('/api/'):
            return jsonify({"error": "Internal server error"}), 500
        return web_bp.error_handler(error)

    # Log all registered routes
    logger.info("Registered routes:")
    for rule in app.url_map.iter_rules():
        logger.info(f"Route: {rule.rule} Methods: {rule.methods}")

    logger.info("Flask application configured successfully")
    return app

app = create_app()

if __name__ == "__main__":
    logger.info("Starting Flask application on port 8080")
    app.run(host='0.0.0.0', port=8080, debug=False)