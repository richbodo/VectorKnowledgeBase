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
    app.register_blueprint(api_bp)

    # Error handlers
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Server error: {str(error)}", exc_info=True)
        return {"error": "Internal server error occurred"}, 500

    return app

# Create the application instance
app = create_app()

if __name__ == "__main__":
    # Use Gunicorn with increased timeout for long-running operations
    from gunicorn.app.base import BaseApplication

    class StandaloneApplication(BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()

        def load_config(self):
            for key, value in self.options.items():
                self.cfg.set(key.lower(), value)

        def load(self):
            return self.application

    options = {
        'bind': '0.0.0.0:5000',
        'workers': 1,
        'timeout': 300,  # Increase timeout to 300 seconds
        'reload': True,
        'preload_app': True,  # Preload app to reduce memory usage
        'max_requests': 1,    # Restart worker after each request to prevent memory leaks
        'worker_class': 'sync'
    }

    StandaloneApplication(app, options).run()
else:
    # For production gunicorn
    application = app