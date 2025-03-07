import logging
from flask import Blueprint, render_template, request, flash
from services.vector_store import VectorStore

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
    
    return render_template('index.html', debug_info=debug_info, query=query, results=results)
