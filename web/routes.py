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
    
    # Fix for template compatibility - move document_details to documents
    if 'document_details' in debug_info and 'documents' not in debug_info:
        debug_info['documents'] = debug_info['document_details']
    
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
    
    # Use existing document details if available
    if 'document_details' in debug_info and 'documents' not in debug_info:
        debug_info['documents'] = debug_info['document_details']
    else:
        # Otherwise format documents for JSON output manually
        documents = []
        for doc_id, doc in vector_store.documents.items():
            doc_info = {
                'id': doc_id,
                'document_id': doc_id,  # For compatibility
                'filename': doc.metadata.get('filename', 'Unknown'),
                'content_type': doc.metadata.get('content_type', 'Unknown'),
                'size': doc.metadata.get('size', 0),
                'total_chunks': doc.metadata.get('total_chunks', 0),
                'created_at': doc.created_at.isoformat() if hasattr(doc, 'created_at') and doc.created_at else "",
                'metadata': doc.metadata  # Full metadata
            }
            documents.append(doc_info)
        
        # Add formatted documents list to debug info
        debug_info['documents'] = documents
    
    return jsonify(debug_info)

def error_handler(error):
    """Custom error handler for web routes"""
    return render_template('error.html', error=error), error.code