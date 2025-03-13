import logging
from flask import Blueprint, render_template, request, flash, jsonify
from services.vector_store import VectorStore
from config import VKB_API_KEY

logger = logging.getLogger(__name__)
bp = Blueprint('web', __name__)

@bp.route('/', methods=['GET'])
def index():
    """Render the main page"""
    vector_store = VectorStore.get_instance()
    debug_info = vector_store.get_debug_info()

    # Get query parameter if it exists
    query = request.args.get('query', '')
    results = []

    # If query is provided, perform search
    if query:
        results, error_msg = vector_store.search(
            query=query,
            k=3,
            similarity_threshold=0.1
        )
        if error_msg:
            flash(error_msg, "error")

    return render_template('index.html', 
                         debug_info=debug_info, 
                         query=query, 
                         results=results,
                         api_key=VKB_API_KEY)  # Pass API key to template

@bp.route('/debug-info', methods=['GET'])
def get_debug_info():
    """Return debug information as JSON for AJAX updates"""
    vector_store = VectorStore.get_instance()
    debug_info = vector_store.get_debug_info()
    return jsonify(debug_info)

def error_handler(error):
    """Custom error handler for web routes"""
    return render_template('error.html', error=error), error.code