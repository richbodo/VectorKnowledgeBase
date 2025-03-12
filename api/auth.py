from functools import wraps
from flask import request, jsonify
from config import VKB_API_KEY
import logging

logger = logging.getLogger(__name__)

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Allow OPTIONS requests without API key for CORS preflight
        if request.method == 'OPTIONS':
            return f(*args, **kwargs)

        api_key = request.headers.get('X-API-KEY')

        if not api_key:
            logger.warning("API request missing X-API-KEY header")
            return jsonify({"error": "Missing API key"}), 401

        if api_key != VKB_API_KEY:
            logger.warning("Invalid API key provided")
            return jsonify({"error": "Invalid API key"}), 401

        return f(*args, **kwargs)
    return decorated_function