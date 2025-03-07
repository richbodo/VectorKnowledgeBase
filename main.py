import logging
import os
from flask import Flask
from api.routes import bp as api_bp
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
        # Log error but don't raise - let the app start anyway
        # Individual endpoints will handle vector store failures

    # Register blueprints
    logger.info("Registering API blueprint...")
    # Register without URL prefix so /upload is accessible at root
    app.register_blueprint(api_bp)

    # Add CORS headers
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        return response

    # Handle OPTIONS requests
    @app.route('/upload', methods=['OPTIONS'])
    def handle_options():
        return '', 200

    # Error handlers
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Server error: {str(error)}", exc_info=True)
        return {"error": "Internal server error occurred"}, 500

    logger.info("Flask application configured successfully")
    return app

app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)