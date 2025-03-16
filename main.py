import logging
import os
from flask import Flask, jsonify, request, render_template
from api.routes import bp as api_bp
from web.routes import bp as web_bp
from web.monitoring import bp as monitoring_bp
from services.vector_store import init_vector_store
from utils.object_storage import get_chroma_storage
from utils.privacy_log_handler import PrivacyLogFilter

# Configure logging
# Determine if we're in a production environment
is_production = bool(os.environ.get("REPL_DEPLOYMENT", False))
log_level = logging.DEBUG  # Use DEBUG level for both production and development
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Create privacy filter for logs
privacy_filter = PrivacyLogFilter()

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(log_level)

# Clear any existing handlers
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(log_format))
console_handler.setLevel(log_level)
console_handler.addFilter(privacy_filter)  # Add privacy filter to console handler
root_logger.addHandler(console_handler)

# Add file handler if not in production
if not is_production:
    file_handler = logging.FileHandler('app.log', mode='a')
    file_handler.setFormatter(logging.Formatter(log_format))
    file_handler.setLevel(log_level)
    file_handler.addFilter(privacy_filter)  # Add privacy filter to file handler
    root_logger.addHandler(file_handler)

# Create logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(log_level)

# Log that privacy filter has been applied
logger.info("Privacy log filter applied to all log handlers")

# Ensure all imported modules log at the appropriate level
logging.getLogger('api').setLevel(log_level)
logging.getLogger('web').setLevel(log_level)
logging.getLogger('services').setLevel(log_level)

# In production, set SQLAlchemy and other verbose loggers to WARNING level
if is_production:
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
else:
    # In development, we want to see everything
    logging.getLogger('sqlalchemy').setLevel(logging.INFO)
    logging.getLogger('werkzeug').setLevel(logging.INFO)

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
        
        # Create a copy of headers and remove potentially sensitive ones before logging
        safe_headers = dict(request.headers)
        sensitive_headers = ['Authorization', 'Cookie', 'X-API-Key']
        for header in sensitive_headers:
            if header in safe_headers:
                safe_headers[header] = '[REDACTED]'
        
        logger.info(f"Headers: {safe_headers}")

    # Defer vector store initialization until first request
    @app.before_request
    def initialize_vector_store():
        if not hasattr(app, '_vector_store_initialized'):
            try:
                # Only check for OpenAI key as it's essential
                if not os.environ.get("OPENAI_API_KEY"):
                    logger.error("Missing OPENAI_API_KEY")
                    app._vector_store_initialized = False
                    return

                # Sync ChromaDB with Replit Object Storage before initializing
                logger.info("Syncing ChromaDB with Replit Object Storage...")
                chroma_storage = get_chroma_storage()
                sync_success, sync_message = chroma_storage.sync_with_object_storage()
                if sync_success:
                    logger.info(f"ChromaDB sync successful: {sync_message}")
                else:
                    logger.warning(f"ChromaDB sync issue: {sync_message}")
                
                logger.info("Starting vector store initialization...")
                init_vector_store()
                logger.info("Vector store initialized successfully")
                app._vector_store_initialized = True
            except Exception as e:
                logger.error(f"Failed to initialize vector store: {str(e)}", exc_info=True)
                app._vector_store_initialized = False
                raise  # Always raise in both dev and deployment

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

    # We've removed the shutdown backup hook as it's not needed with our improved backup system

    logger.info("Flask application configured successfully")
    return app

app = create_app()

if __name__ == "__main__":
    logger.info("Starting Flask application on port 8080")
    app.run(host='0.0.0.0', port=8080, debug=False)