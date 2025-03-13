import logging
import os
from flask import Blueprint, jsonify
import openai

logger = logging.getLogger(__name__)

bp = Blueprint('monitoring', __name__, url_prefix='/monitoring')

@bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint that tests the OpenAI API connection."""
    try:
        # Check if OpenAI API key is set
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return jsonify({
                "status": "warning",
                "message": "OPENAI_API_KEY environment variable is not set."
            }), 200

        # Test API key validity by accessing a simple endpoint
        client = openai.OpenAI(api_key=api_key)
        models = client.models.list(limit=1)

        # If we get here, the connection is working
        return jsonify({
            "status": "ok",
            "message": "Successfully connected to OpenAI API",
            "models_accessible": True
        }), 200

    except Exception as e:
        logger.error(f"OpenAI API connection test failed: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to connect to OpenAI API: {str(e)}"
        }), 500

@bp.route('/test-openai', methods=['GET'])
def test_openai_connection():
    """Test OpenAI API connection and display diagnostic information"""
    try:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        key_info = {
            'starts_with': api_key[:4] if api_key else 'None',
            'ends_with': api_key[-4:] if api_key else 'None',
            'length': len(api_key),
            'format_valid': api_key.startswith('sk-') if api_key else False
        }

        test_text = "This is a test of the OpenAI API connection."
        error_details = None
        embedding = None

        try:
            embedding_service = EmbeddingService()
            embedding = embedding_service.generate_embedding(test_text)
        except Exception as e:
            error_details = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'traceback': traceback.format_exc()
            }

        diagnostic_info = {
            'api_key_info': key_info,
            'test_status': 'success' if embedding is not None else 'failed',
            'error_details': error_details,
            'embedding_generated': embedding is not None,
            'embedding_dimension': len(embedding) if embedding else None
        }

        return render_template('monitoring/openai_test.html', diagnostic_info=diagnostic_info)

    except Exception as e:
        logger.error(f"Error in OpenAI test endpoint: {str(e)}", exc_info=True)
        return render_template('error.html', error="OpenAI test failed"), 500