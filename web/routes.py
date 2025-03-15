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
    doc_count = len(vector_store.documents)
    
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

    # Get the debug info for consistent rendering between pages
    debug_info = vector_store.get_debug_info()
    debug_info['document_count'] = doc_count  # Ensure document_count is available
    
    return render_template('index.html', 
                         document_count=doc_count,  # Keep for backward compatibility
                         debug_info=debug_info,
                         query=query, 
                         results=results,
                         api_key=VKB_API_KEY)  # Pass API key to template

@bp.route('/diagnostics', methods=['GET'])
def diagnostics():
    """Render the unified diagnostics page"""
    vector_store = VectorStore.get_instance()
    debug_info = vector_store.get_debug_info()
    
    # Log the structure of debug_info for debugging
    import logging
    import json
    logger = logging.getLogger(__name__)
    logger.info(f"DEBUG INFO STRUCTURE: {json.dumps(debug_info, default=str)}")
    
    # Fix for template compatibility - move document_details to documents
    if 'document_details' in debug_info and 'documents' not in debug_info:
        debug_info['documents'] = debug_info['document_details']
        
    # Add API stats information to fix template references
    if 'api_stats' not in debug_info:
        debug_info['api_stats'] = {
            'successful_calls': 0,
            'failed_calls': 0,
            'last_call': 'Never'
        }
        
    # Add OpenAI key info for template references
    if 'openai_key_info' not in debug_info:
        # Check if OPENAI_API_KEY environment variable exists
        import os
        api_key = os.environ.get('OPENAI_API_KEY', '')
        
        if api_key:
            # Only show minimal info for security
            prefix = api_key[:4] if len(api_key) >= 4 else "****"
            debug_info['openai_key_info'] = {
                'status': 'Available',
                'type': 'API Key',
                'prefix': prefix
            }
        else:
            debug_info['openai_key_info'] = {
                'status': 'Missing',
                'type': 'Unknown',
                'prefix': 'None'
            }
    
    # Get more detailed database info
    db_path = debug_info.get('db_path', '')
    db_exists = debug_info.get('db_exists', False)
    db_contents = debug_info.get('db_contents', [])
    db_size_mb = debug_info.get('db_size_mb', 0)
    embeddings_count = debug_info.get('sqlite_embeddings_count', 0)
    unique_doc_count = debug_info.get('sqlite_unique_doc_count', 0)
    
    # Get ChromaDB version info
    chromadb_version = debug_info.get('chromadb_version', 'Unknown')
    
    return render_template('diagnostics.html', 
                         debug_info=debug_info, 
                         db_path=db_path,
                         db_exists=db_exists,
                         db_contents=db_contents,
                         db_size_mb=db_size_mb,
                         embeddings_count=embeddings_count,
                         unique_doc_count=unique_doc_count,
                         chromadb_version=chromadb_version)

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
    
    # Add API stats information to fix template references
    if 'api_stats' not in debug_info:
        debug_info['api_stats'] = {
            'successful_calls': 0,
            'failed_calls': 0,
            'last_call': 'Never'
        }
    
    return jsonify(debug_info)

def error_handler(error):
    """Custom error handler for web routes"""
    return render_template('error.html', error=error), error.code