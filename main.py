import logging
import os
from flask import Flask, jsonify, request, render_template
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
        logging.FileHandler('app.log', mode='a')
    ]
)

# Make sure all loggers output to both console and file
for handler in logging.getLogger().handlers:
    handler.setLevel(logging.DEBUG)

# Create logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Ensure all imported modules also log at DEBUG level
logging.getLogger('api').setLevel(logging.DEBUG)
logging.getLogger('web').setLevel(logging.DEBUG)
logging.getLogger('services').setLevel(logging.DEBUG)

def create_app():
    """Application factory function"""
    logger.info("=== Starting Flask PDF Processing Application ===")
    logger.info("Debug logs will be written to 'app.log' in the project root directory")

    app = Flask(__name__)
    
    # Detect deployment mode
    is_deployment = bool(os.environ.get("REPL_DEPLOYMENT", False))
    
    # Use a default secret key in deployment if not provided
    app.secret_key = os.environ.get("SESSION_SECRET")
    if not app.secret_key:
        if is_deployment:
            logger.warning("SESSION_SECRET not set in deployment, using default")
            app.secret_key = "default-deployment-secret-key"
        else:
            logger.error("SESSION_SECRET environment variable not set")
            raise ValueError("SESSION_SECRET environment variable is required")

    # Disable Flask's default redirect behavior
    app.url_map.strict_slashes = False

    # Add request logging middleware
    @app.before_request
    def log_request_info():
        logger.info("=== New Request ===")
        logger.info(f"Method: {request.method}")
        logger.info(f"Path: {request.path}")
        logger.info(f"Headers: {dict(request.headers)}")
        
        # Log form data for POST requests
        if request.method == 'POST':
            if request.is_json:
                logger.info(f"JSON Data: {request.get_json(silent=True)}")
            elif request.form:
                logger.info(f"Form Data: {dict(request.form)}")
                
        # Log files if present
        if request.files:
            logger.info(f"Files: {list(request.files.keys())}")
            for file_key in request.files:
                file = request.files[file_key]
                logger.info(f"File: {file_key}, Filename: {file.filename}, Content Type: {file.content_type}")

    # Defer vector store initialization until first request
    @app.before_request
    def initialize_vector_store():
        if not hasattr(app, '_vector_store_initialized'):
            try:
                # Check if we're in deployment with missing API keys
                if os.environ.get("REPL_DEPLOYMENT") and (
                    not os.environ.get("OPENAI_API_KEY") or 
                    not os.environ.get("VKB_API_KEY")
                ):
                    logger.warning("Deployment mode with missing API keys - skipping vector store")
                    app._vector_store_initialized = False
                    return
                
                logger.info("Starting vector store initialization...")
                init_vector_store()
                logger.info("Vector store initialized successfully")
                app._vector_store_initialized = True
            except Exception as e:
                logger.error(f"Failed to initialize vector store: {str(e)}", exc_info=True)
                app._vector_store_initialized = False
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
        logger.info("=== Processing Response ===")
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Response Headers: {dict(response.headers)}")

        # For API routes, ensure JSON response
        if request.path.startswith('/api/'):
            logger.info("API route detected, ensuring JSON response")
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
        return render_template('error.html', error=error), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 error for path: {request.path}", exc_info=True)
        if request.path.startswith('/api/'):
            return jsonify({"error": "Internal server error"}), 500
        return render_template('error.html', error=error), 500

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