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
    app.register_blueprint(api_bp)

    # Error handlers
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Server error: {str(error)}", exc_info=True)
        return {"error": "Internal server error occurred"}, 500

    logger.info("Flask application configured successfully")
    return app

app = create_app()

if __name__ == "__main__":
    # Use Gunicorn with worker configuration for better resource management
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
        'workers': 2,  # Use 2 workers to handle requests
        'worker_class': 'sync',
        'timeout': 300,  # 5 minute timeout for long operations
        'graceful_timeout': 30,
        'keepalive': 2,
        'max_requests': 10,  # Restart workers after 10 requests to prevent memory leaks
        'max_requests_jitter': 3,
        'preload_app': True,  # Preload app to reduce memory usage
        'worker_tmp_dir': '/dev/shm',  # Use shared memory for worker temp files
        'worker_exit': lambda server, worker: logger.info(f'Worker {worker.pid} exited'),
    }

    logger.info("Starting Gunicorn server with worker management...")
    StandaloneApplication(app, options).run()
else:
    # For production deployment
    application = app