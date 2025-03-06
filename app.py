import os
import logging
from flask import Flask

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

    # Register blueprints
    from api.routes import bp as api_bp
    app.register_blueprint(api_bp)

    # Error handlers
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Server error: {str(error)}", exc_info=True)
        return {"error": "Internal server error occurred"}, 500

    logger.info("Flask application configured successfully")
    return app
