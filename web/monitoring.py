import logging
import os
import traceback
from flask import Blueprint, render_template, jsonify
from services.vector_store import VectorStore
from services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)
bp = Blueprint('monitoring', __name__, url_prefix='/web/monitoring')

@bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint with resource monitoring"""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()

        health_data = {
            'status': 'healthy',
            'memory': {
                'rss': f"{memory_info.rss / 1024 / 1024:.2f}MB",
                'vms': f"{memory_info.vms / 1024 / 1024:.2f}MB",
            },
            'cpu_percent': process.cpu_percent(),
            'worker_pid': os.getpid(),
            'vector_store': {
                'document_count': len(VectorStore.get_instance().documents),
                'index_size': VectorStore.get_instance().collection.count()
            }
        }
        return render_template('monitoring/health.html', health_data=health_data)
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return render_template('error.html', error="Health check failed"), 500

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
