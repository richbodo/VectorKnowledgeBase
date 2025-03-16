import os
import uuid
import logging
import traceback
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, make_response
from services.pdf_processor import PDFProcessor
from services.vector_store import VectorStore
from models import Document
from config import MAX_FILE_SIZE, ALLOWED_FILE_TYPES
from api.auth import require_api_key
from utils.privacy_log_handler import PrivacyLogFilter
from contextlib import contextmanager

logger = logging.getLogger(__name__)
bp = Blueprint('api', __name__, url_prefix='/api')  # Add explicit URL prefix

# Add privacy filter to logger
privacy_filter = PrivacyLogFilter()
logger.addFilter(privacy_filter)

def json_response(payload, status=200):
    """Helper function to create consistent JSON responses.
    Uses a simplified approach to ensure reliable response handling."""
    logger.debug(f"Creating JSON response with status {status}")
    logger.debug(f"Response payload: {payload}")

    response = make_response(json.dumps(payload), status)
    response.mimetype = 'application/json'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-API-KEY'
    response.headers.pop('Location', None)  # Prevent any redirects
    response.autocorrect_location_header = False

    logger.debug(f"Response headers: {dict(response.headers)}")
    return response

@bp.route('upload', methods=['POST', 'OPTIONS'])  # Remove leading slash since url_prefix adds it
@require_api_key
def upload_document():
    """Upload and process a PDF document"""
    logger.info(f"API: Received {request.method} request to /api/upload")
    logger.info(f"Request headers: {dict(request.headers)}")
    logger.info(f"Request form data keys: {list(request.form.keys())}")
    logger.info(f"Request files keys: {list(request.files.keys())}")

    # Extra detailed logging for upload endpoint
    if request.method == 'POST':
        logger.info("Processing POST request to upload endpoint")
        if request.files:
            for file_key in request.files:
                file = request.files[file_key]
                logger.info(f"Processing file upload: {file.filename} ({file.content_type})")

    # Handle OPTIONS request with explicit 204 response
    if request.method == 'OPTIONS':
        logger.debug("Handling OPTIONS request")
        response = make_response('', 204)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-API-KEY'
        return response

    try:
        logger.info(f"Request files: {request.files}")
        if 'file' not in request.files:
            logger.error("No file provided in request")
            return json_response({"error": "No file provided"}, 400)

        file = request.files['file']
        if not file.filename:
            logger.error("No file selected")
            return json_response({"error": "No file selected"}, 400)

        logger.info(f"Processing file: {file.filename}, content type: {file.content_type}")

        # Read and validate file content
        content = file.read()
        file_size = len(content)

        if file_size > MAX_FILE_SIZE:
            logger.error(f"File size ({file_size} bytes) exceeds maximum limit ({MAX_FILE_SIZE} bytes)")
            return json_response({
                "error": f"File size ({file_size} bytes) exceeds maximum limit ({MAX_FILE_SIZE} bytes)"
            }, 400)

        # Extract text from PDF
        logger.debug("Starting PDF text extraction...")
        text_content, error = PDFProcessor.extract_text(content)
        if error:
            logger.error(f"Error extracting text: {error}")
            return json_response({"error": f"PDF extraction error: {error}"}, 400)
        if not text_content:
            logger.error("No text content could be extracted from the PDF")
            return json_response({"error": "No text content could be extracted from the PDF"}, 400)
        logger.debug(f"Successfully extracted {len(text_content)} characters of text")

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
        logger.debug("Adding document to vector store...")
        vector_store = VectorStore.get_instance()
        success, error_msg = vector_store.add_document(document)

        if not success:
            logger.error(f"Failed to add document to vector store: {error_msg}")
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
        logger.error("Full exception details:", exc_info=True)
        return json_response({"error": error_msg}, 500)

@bp.route('/query', methods=['POST'])
@require_api_key
def query_documents():
    """Query endpoint for semantic search"""
    try:
        # Check if request is JSON or form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict() or request.args.to_dict()
        
        # Get query parameter from different possible sources
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