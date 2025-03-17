import logging
<<<<<<< HEAD
from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, session
from services.vector_store import VectorStore
from config import VKB_API_KEY
from web.auth import auth_required, is_authenticated, get_user_info, get_login_url, handle_logout
from web.http_auth import http_auth_required, session_authenticated
=======
from flask import Blueprint, render_template, request, flash, jsonify
from services.vector_store import VectorStore
from config import VKB_API_KEY
>>>>>>> 446e53914c5d9f82f391a8f0f259dd39892a7531

logger = logging.getLogger(__name__)
bp = Blueprint('web', __name__)

@bp.route('/', methods=['GET'])
<<<<<<< HEAD
@http_auth_required
=======
>>>>>>> 446e53914c5d9f82f391a8f0f259dd39892a7531
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
    
<<<<<<< HEAD
    # Get authentication info for the template
    is_auth = is_authenticated()
    user_info = get_user_info() if is_auth else None

=======
>>>>>>> 446e53914c5d9f82f391a8f0f259dd39892a7531
    return render_template('index.html', 
                         document_count=doc_count,  # Keep for backward compatibility
                         debug_info=debug_info,
                         query=query, 
                         results=results,
<<<<<<< HEAD
                         api_key=VKB_API_KEY,  # Pass API key to template
                         is_authenticated=is_auth,
                         user_info=user_info)

@bp.route('/diagnostics', methods=['GET'])
@http_auth_required
=======
                         api_key=VKB_API_KEY)  # Pass API key to template

@bp.route('/diagnostics', methods=['GET'])
>>>>>>> 446e53914c5d9f82f391a8f0f259dd39892a7531
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
    
    # Add additional fields for template compatibility
    if 'collection_name' not in debug_info:
        debug_info['collection_name'] = 'pdf_documents'
        
    if 'embedding_count' not in debug_info:
        debug_info['embedding_count'] = debug_info.get('sqlite_embeddings_count', 0)
        
    if 'embedding_dimension' not in debug_info:
        debug_info['embedding_dimension'] = 1536  # Default for text-embedding-3-small
        
    if 'index_size' not in debug_info:
        # If we have db_size_mb, use that, otherwise 0
        debug_info['index_size'] = f"{debug_info.get('db_size_mb', 0)} MB"
        
    if 'sqlite_tables' not in debug_info:
        debug_info['sqlite_tables'] = []
        
    if 'sqlite_issues' not in debug_info:
        debug_info['sqlite_issues'] = []
        
    # Add embedding model information
    if 'embedding_model' not in debug_info:
        debug_info['embedding_model'] = 'text-embedding-3-small'
        
    if 'model_dimension' not in debug_info:
        debug_info['model_dimension'] = 1536
        
    # Add default document count type information
    if 'document_id_count' not in debug_info:
        debug_info['document_id_count'] = 0
        
    if 'test_id_count' not in debug_info:
        debug_info['test_id_count'] = 0
    
    # Get more detailed database info
    db_path = debug_info.get('db_path', '')
    db_exists = debug_info.get('db_exists', False)
    db_contents = debug_info.get('db_contents', [])
    db_size_mb = debug_info.get('db_size_mb', 0)
    embeddings_count = debug_info.get('sqlite_embeddings_count', 0)
    unique_doc_count = debug_info.get('sqlite_unique_doc_count', 0)
    
    # Get ChromaDB version info
    chromadb_version = debug_info.get('chromadb_version', 'Unknown')
    
<<<<<<< HEAD
    # Get authentication info for the template
    is_auth = is_authenticated()
    user_info = get_user_info() if is_auth else None
    
=======
>>>>>>> 446e53914c5d9f82f391a8f0f259dd39892a7531
    return render_template('diagnostics.html', 
                         debug_info=debug_info, 
                         db_path=db_path,
                         db_exists=db_exists,
                         db_contents=db_contents,
                         db_size_mb=db_size_mb,
                         embeddings_count=embeddings_count,
                         unique_doc_count=unique_doc_count,
<<<<<<< HEAD
                         chromadb_version=chromadb_version,
                         is_authenticated=is_auth,
                         user_info=user_info)

@bp.route('/debug-info', methods=['GET'])
@http_auth_required
=======
                         chromadb_version=chromadb_version)

@bp.route('/debug-info', methods=['GET'])
>>>>>>> 446e53914c5d9f82f391a8f0f259dd39892a7531
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
    
    # Add additional fields for template compatibility
    if 'collection_name' not in debug_info:
        debug_info['collection_name'] = 'pdf_documents'
        
    if 'embedding_count' not in debug_info:
        debug_info['embedding_count'] = debug_info.get('sqlite_embeddings_count', 0)
        
    if 'embedding_dimension' not in debug_info:
        debug_info['embedding_dimension'] = 1536  # Default for text-embedding-3-small
        
    if 'index_size' not in debug_info:
        # If we have db_size_mb, use that, otherwise 0
        debug_info['index_size'] = f"{debug_info.get('db_size_mb', 0)} MB"
        
    if 'sqlite_tables' not in debug_info:
        debug_info['sqlite_tables'] = []
        
    if 'sqlite_issues' not in debug_info:
        debug_info['sqlite_issues'] = []
        
    # Add embedding model information
    if 'embedding_model' not in debug_info:
        debug_info['embedding_model'] = 'text-embedding-3-small'
        
    if 'model_dimension' not in debug_info:
        debug_info['model_dimension'] = 1536
        
    # Add default document count type information
    if 'document_id_count' not in debug_info:
        debug_info['document_id_count'] = 0
        
    if 'test_id_count' not in debug_info:
        debug_info['test_id_count'] = 0
    
    return jsonify(debug_info)

<<<<<<< HEAD
@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login through HTTP Basic Auth"""
    # Check if authentication through session
    from web.http_auth import session_authenticated, check_auth, set_session_auth
    
    # If already authenticated through HTTP Auth, redirect to index
    if session_authenticated():
        return redirect(url_for('web.index'))
    
    error = None
    
    # Handle POST request for form-based login
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        if check_auth(username, password):
            # Set session as authenticated
            set_session_auth(True)
            flash("Login successful", "success")
            return redirect(url_for('web.index'))
        else:
            error = "Invalid username or password"
    
    # Render login form
    return render_template('login.html', 
                          error=error,
                          is_authenticated=False,
                          user_info=None)

@bp.route('/logout', methods=['GET'])
@http_auth_required
def logout():
    """Handle logout for both Replit Auth and HTTP Auth"""
    # Clear Replit Auth if it was being used
    handle_logout()
    
    # Clear HTTP Auth session
    from web.http_auth import set_session_auth
    set_session_auth(False)
    
    flash("You have been logged out successfully", "success")
    return redirect(url_for('web.index'))

=======
>>>>>>> 446e53914c5d9f82f391a8f0f259dd39892a7531
def error_handler(error):
    """Custom error handler for web routes"""
    return render_template('error.html', error=error), error.code