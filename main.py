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

    # Initialize vector store
    try:
        logger.info("Starting vector store initialization...")
        init_vector_store()
        logger.info("Vector store initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize vector store: {str(e)}", exc_info=True)
        # Individual endpoints will handle vector store failures

    # Register blueprints
    logger.info("Registering blueprints...")
    # Register API routes at root level for direct API access
    app.register_blueprint(api_bp)
    # Register web interface routes under /web prefix
    app.register_blueprint(web_bp, url_prefix="/web")
    # Register monitoring routes
    app.register_blueprint(monitoring_bp)

    # Add CORS headers to all responses
    @app.after_request
    def after_request(response):
        # Don't modify the Content-Type for web routes
        if not request.path.startswith('/web/'):
            response.headers['Content-Type'] = 'application/json'
            response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        return response

    # Error handlers for API routes
    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith('/web/'):
            return web_bp.error_handler(error)
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        if request.path.startswith('/web/'):
            return web_bp.error_handler(error)
        return jsonify({"error": "Internal server error"}), 500

    logger.info("Flask application configured successfully")
    return app

app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)