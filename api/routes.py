import os
import uuid
import logging
import traceback
import time
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, make_response
from services.pdf_processor import PDFProcessor
from services.vector_store import VectorStore
from services.embedding_service import EmbeddingService
from models import Document
from config import MAX_FILE_SIZE, ALLOWED_FILE_TYPES
import httpx

logger = logging.getLogger(__name__)
bp = Blueprint('api', __name__)

def json_response(data, status_code=200):
    """Helper function to create consistent JSON responses"""
    response = make_response(jsonify(data), status_code)
    response.headers['Content-Type'] = 'application/json'
    return response

@bp.route('/query', methods=['POST'])
def query_documents():
    """Query endpoint optimized for GPT Actions"""
    try:
        if not request.is_json:
            return json_response({"error": "Request must be JSON"}, 400)

        data = request.get_json()
        query = data.get('query', '').strip() if data else ''

        if not query:
            return json_response({"error": "Query cannot be empty"}, 400)

        vector_store = VectorStore.get_instance()
        results, error_msg = vector_store.search(
            query=query,
            k=3,  # Return top 3 most relevant results
            similarity_threshold=0.1  # Lower threshold to get more potential matches
        )

        if error_msg:
            return json_response({"error": error_msg}, 500)

        response = {
            "results": [{
                "title": result.metadata.get("filename", "Unknown"),
                "content": result.content,
                "score": result.similarity_score,
                "metadata": {
                    "source": f"Part {result.metadata.get('chunk_index', 0) + 1} of {result.metadata.get('total_chunks', 1)}",
                    "file_type": result.metadata.get("content_type", "application/pdf"),
                    "uploaded_at": result.metadata.get("created_at", datetime.utcnow().isoformat()),
                    "file_size": f"{result.metadata.get('size', 0) / 1024 / 1024:.1f}MB"
                }
            } for result in results]
        }

        return json_response(response)

    except Exception as e:
        logger.error(f"Error processing query: {traceback.format_exc()}")
        return json_response({"error": f"Internal server error: {str(e)}"}, 500)

@bp.route('/upload', methods=['POST', 'OPTIONS'])
def upload_document():
    """Upload and process a PDF document"""
    try:
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            return response

        # Log request details for debugging
        logger.info("=== Starting document upload process ===")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Request files: {request.files}")
        logger.info(f"Request form: {request.form}")
        logger.info(f"Request data: {request.get_data()}")

        if request.method != 'POST':
            return json_response({"error": "Only POST method is allowed"}, 405)

        # Stage 1: File Validation
        if 'file' not in request.files:
            return json_response({"error": "No file provided"}, 400)

        file = request.files['file']
        if not file.filename:
            return json_response({"error": "No file selected"}, 400)

        # Check file extension
        allowed_extensions = {'.pdf'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            error_msg = f"Invalid file extension '{file_ext}'. Only PDF files are allowed"
            return json_response({"error": error_msg}, 400)

        # Read file content
        content = file.read()
        file_size = len(content)
        logger.info(f"Received file: {file.filename}, size: {file_size} bytes, content type: {file.content_type}")

        # Validate file size
        if file_size > MAX_FILE_SIZE:
            error_msg = f"File size ({file_size} bytes) exceeds maximum limit ({MAX_FILE_SIZE} bytes)"
            return json_response({"error": error_msg}, 400)

        # Validate file type - accept both explicit PDF mime type and octet-stream with .pdf extension
        valid_content_types = ALLOWED_FILE_TYPES + ['application/octet-stream']
        if file.content_type not in valid_content_types and file_ext != '.pdf':
            error_msg = f"Invalid file type '{file.content_type}'. Only PDF files are allowed"
            return json_response({"error": error_msg}, 400)

        # If content type is octet-stream, we've already validated the .pdf extension above

        # Stage 2: PDF Text Extraction
        logger.info("Starting PDF text extraction...")
        text_content, error = PDFProcessor.extract_text(content)

        if error:
            return json_response({"error": error}, 400)

        if not text_content:
            error_msg = "No text content could be extracted from the PDF"
            return json_response({"error": error_msg}, 400)

        # Stage 3: Create document and prepare for vector store
        logger.info("Starting document creation and vector store preparation...")
        doc_id = str(uuid.uuid4())
        document = Document(
            id=doc_id,
            content=text_content,
            metadata={
                "filename": file.filename,
                "content_type": file.content_type,
                "size": file_size,
                "created_at": datetime.utcnow().isoformat()
            }
        )

        # Stage 4: Add to vector store
        logger.info("Starting vector store operations...")
        vector_store = VectorStore.get_instance()
        success, error_msg = vector_store.add_document(document)

        if not success:
            return json_response({"error": error_msg}, 500)

        logger.info("=== Document processing complete ===")
        return json_response({
            "success": True,
            "message": "Document processed successfully",
            "document_id": doc_id
        })

    except Exception as e:
        error_msg = f"Error processing upload: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return json_response({"error": f"Internal server error: {str(e)}"}, 500)

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
        return json_response(health_data)
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return json_response({'status': 'unhealthy', 'error': str(e)}, 500)

@bp.route('/test-openai', methods=['GET'])
def test_openai_connection():
    """Test OpenAI API connection and display diagnostic information"""
    try:
        # Get API key info (safely)
        api_key = os.environ.get("OPENAI_API_KEY", "")
        key_info = {
            'starts_with': api_key[:4] if api_key else 'None',
            'ends_with': api_key[-4:] if api_key else 'None',
            'length': len(api_key),
            'format_valid': api_key.startswith('sk-') if api_key else False
        }

        # Initialize embedding service and try a test call
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

        # Prepare diagnostic info
        diagnostic_info = {
            'api_key_info': key_info,
            'test_status': 'success' if embedding is not None else 'failed',
            'error_details': error_details,
            'embedding_generated': embedding is not None,
            'embedding_dimension': len(embedding) if embedding else None
        }

        return json_response(diagnostic_info)

    except Exception as e:
        logger.error(f"Error in OpenAI test endpoint: {str(e)}", exc_info=True)
        return json_response({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }, 500)

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