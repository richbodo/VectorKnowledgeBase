import logging
import os
from flask import Flask
from api.routes import bp as api_bp
from services.vector_store import init_vector_store

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Initialize services state
_services_initialized = False

# Register blueprints
app.register_blueprint(api_bp)

# Error handlers
@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Server error: {str(error)}", exc_info=True)
    return {"error": "Internal server error occurred"}, 500

@app.before_request
def init_services():
    """Initialize services on first request"""
    global _services_initialized
    if not _services_initialized:
        try:
            logger.info("Starting vector store initialization...")
            init_vector_store()
            logger.info("Vector store initialized successfully")
            _services_initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize services: {str(e)}", exc_info=True)
            raise

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)