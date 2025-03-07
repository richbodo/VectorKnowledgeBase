import os
import uuid
import logging
import traceback
from datetime import datetime
from flask import Blueprint, request, jsonify, make_response
from services.pdf_processor import PDFProcessor
from services.vector_store import VectorStore
from models import Document
from config import MAX_FILE_SIZE, ALLOWED_FILE_TYPES

logger = logging.getLogger(__name__)
bp = Blueprint('api', __name__)

def json_response(data, status_code=200):
    """Helper function to create consistent JSON responses"""
    response = make_response(jsonify(data), status_code)
    response.headers['Content-Type'] = 'application/json'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

# Blueprint error handlers
@bp.errorhandler(404)
def not_found_error(error):
    return json_response({"error": "Resource not found"}, 404)

@bp.errorhandler(405)
def method_not_allowed_error(error):
    return json_response({
        "error": f"Method {request.method} not allowed",
        "allowed_methods": error.valid_methods
    }, 405)

@bp.errorhandler(500)
def internal_error(error):
    return json_response({"error": "Internal server error"}, 500)

@bp.route('/upload', methods=['POST', 'OPTIONS'])
def upload_document():
    """Upload and process a PDF document"""
    try:
        logger.info(f"API: Received {request.method} request to /upload")
        logger.info(f"Request headers: {dict(request.headers)}")

        # Handle OPTIONS request
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            response.headers['Content-Type'] = 'application/json'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            return response

        # Validate file presence
        if 'file' not in request.files:
            return json_response({"error": "No file provided"}, 400)

        file = request.files['file']
        if not file.filename:
            return json_response({"error": "No file selected"}, 400)

        logger.info(f"Processing file: {file.filename}, content type: {file.content_type}")

        # Read and validate file content
        content = file.read()
        file_size = len(content)

        if file_size > MAX_FILE_SIZE:
            return json_response({
                "error": f"File size ({file_size} bytes) exceeds maximum limit ({MAX_FILE_SIZE} bytes)"
            }, 400)

        # Extract text from PDF
        text_content, error = PDFProcessor.extract_text(content)
        if error:
            return json_response({"error": error}, 400)
        if not text_content:
            return json_response({"error": "No text content could be extracted from the PDF"}, 400)

        # Create document
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

        # Add to vector store
        vector_store = VectorStore.get_instance()
        success, error_msg = vector_store.add_document(document)

        if not success:
            return json_response({"error": error_msg}, 500)

        logger.info(f"Successfully processed document: {doc_id}")
        response_data = {
            "success": True,
            "message": "Document processed successfully",
            "document_id": doc_id,
            "metadata": {
                "filename": file.filename,
                "size": file_size,
                "content_type": file.content_type
            }
        }
        logger.info(f"Sending JSON response: {response_data}")
        return json_response(response_data)

    except Exception as e:
        error_msg = f"Error processing upload: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return json_response({"error": error_msg}, 500)

@bp.route('/query', methods=['POST'])
def query_documents():
    """Query endpoint for semantic search"""
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
            k=3,
            similarity_threshold=0.1
        )

        if error_msg:
            return json_response({"error": error_msg}, 500)

        return json_response({
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
        })

    except Exception as e:
        error_msg = f"Error processing query: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return json_response({"error": error_msg}, 500)