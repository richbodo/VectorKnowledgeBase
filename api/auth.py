from functools import wraps
from flask import request, jsonify
import os
import logging

logger = logging.getLogger(__name__)

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == 'OPTIONS':
            return f(*args, **kwargs)

        # Skip API key check if we're in a deployment environment or API key isn't set
        if os.environ.get("REPL_DEPLOYMENT"):
            logger.warning("Deployment mode detected, skipping API key check.")
            return f(*args, **kwargs)

        # Always fetch the latest API key from environment
        VKB_API_KEY = os.environ.get("VKB_API_KEY")
        if not VKB_API_KEY:
            logger.error("Server-side API key (VKB_API_KEY) is not set.")
            return jsonify({"error": "Server configuration error: Missing API key"}), 500

        api_key = None

        # Check HTTP header first (standard practice)
        if 'X-API-KEY' in request.headers:
            api_key = request.headers.get('X-API-KEY')
            logger.info("API key found in HTTP header.")
        else:
            # Check JSON body parameters (OpenAI's behavior)
            json_data = request.get_json(silent=True)
            if json_data := json_data_or_empty(request):
                if 'X-API-KEY' in json_data:
                    api_key = json_data.get('X-API-KEY')
                    logger.info("API key found in JSON body as 'X-API-KEY'.")
                elif 'X__API__KEY' in json_data:
                    api_key = json_data.get('X__API__KEY')
                    logger.info("API key found in JSON body as 'X__API__KEY'.")
                else:
                    api_key = None

        # If still not found, check form data and query parameters
        if not api_key:
            api_key = (
                request.form.get('X-API-KEY') or
                request.form.get('X__API__KEY') or
                request.args.get('X-API-KEY') or
                request.args.get('X__API__KEY')
            )
            if api_key:
                logger.info("API key found in form data or query parameters.")

        if not api_key:
            logger.warning("API request missing API key.")
            return jsonify({"error": "Missing API key"}), 401

        # Verify API key matches environment variable
        VKB_API_KEY = os.environ.get("VKB_API_KEY")
        if api_key != VKB_API_KEY:
            logger.warning("Invalid API key provided.")
            return jsonify({"error": "Invalid API key"}), 401

        # API key is valid, proceed with request
        return f(*args, **kwargs)
    return decorated