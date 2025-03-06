import uuid
import logging
import traceback
import time
import os
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from services.pdf_processor import PDFProcessor
from services.vector_store import VectorStore
from models import Document
from config import MAX_FILE_SIZE, ALLOWED_FILE_TYPES

logger = logging.getLogger(__name__)
bp = Blueprint('api', __name__)

@bp.route('/', methods=['GET'])
def index():
    """Render the main page"""
    vector_store = VectorStore.get_instance()
    debug_info = vector_store.get_debug_info()
    return render_template('index.html', debug_info=debug_info)

@bp.route('/upload', methods=['POST'])
def upload_document():
    """Upload and process a PDF document"""
    try:
        start_time = time.time()
        logger.info("=== Starting document upload process ===")

        # Stage 1: File Validation
        if 'file' not in request.files:
            logger.error("No file provided in request")
            if request.is_json:
                return jsonify({"error": "No file provided"}), 400
            flash("No file provided", "error")
            return redirect(url_for('api.index'))

        file = request.files['file']
        if not file.filename:
            logger.error("Empty filename provided")
            if request.is_json:
                return jsonify({"error": "No file selected"}), 400
            flash("No file selected", "error")
            return redirect(url_for('api.index'))

        # Read file content
        content = file.read()
        file_size = len(content)
        logger.info(f"Received file: {file.filename}, size: {file_size} bytes")

        # Validate file size
        if file_size > MAX_FILE_SIZE:
            error_msg = f"File size ({file_size} bytes) exceeds maximum limit ({MAX_FILE_SIZE} bytes)"
            logger.error(error_msg)
            if request.is_json:
                return jsonify({"error": error_msg}), 400
            flash(error_msg, "error")
            return redirect(url_for('api.index'))

        # Validate file type
        if file.content_type not in ALLOWED_FILE_TYPES:
            error_msg = f"Invalid file type '{file.content_type}'. Only PDF files are allowed"
            logger.error(error_msg)
            if request.is_json:
                return jsonify({"error": error_msg}), 400
            flash(error_msg, "error")
            return redirect(url_for('api.index'))

        stage1_time = time.time() - start_time
        logger.info(f"Stage 1 (Validation) completed in {stage1_time:.2f}s")

        # Stage 2: PDF Text Extraction
        logger.info("Starting PDF text extraction...")
        stage2_start = time.time()
        text_content, error = PDFProcessor.extract_text(content)

        if error:
            logger.error(f"PDF processing error: {error}")
            if request.is_json:
                return jsonify({"error": error}), 400
            flash(f"Error processing PDF: {error}", "error")
            return redirect(url_for('api.index'))

        if not text_content:
            error_msg = "No text content could be extracted from the PDF"
            logger.error(error_msg)
            if request.is_json:
                return jsonify({"error": error_msg}), 400
            flash(error_msg, "error")
            return redirect(url_for('api.index'))

        stage2_time = time.time() - stage2_start
        logger.info(f"Stage 2 (Text Extraction) completed in {stage2_time:.2f}s")
        logger.info(f"Extracted text length: {len(text_content)} chars")

        # Stage 3: Create document and prepare for vector store
        logger.info("Starting document creation and vector store preparation...")
        stage3_start = time.time()

        doc_id = str(uuid.uuid4())
        document = Document(
            id=doc_id,
            content=text_content,
            metadata={
                "filename": file.filename,
                "content_type": file.content_type,
                "size": file_size
            }
        )

        stage3_time = time.time() - stage3_start
        logger.info(f"Stage 3 (Document Creation) completed in {stage3_time:.2f}s")

        # Stage 4: Add to vector store
        logger.info("Starting vector store operations...")
        stage4_start = time.time()

        vector_store = VectorStore.get_instance()
        success, error_msg = vector_store.add_document(document)

        if not success:
            logger.error(f"Vector store error: {error_msg}")
            if request.is_json:
                return jsonify({"error": error_msg}), 500
            flash(error_msg, "error")
            return redirect(url_for('api.index'))

        stage4_time = time.time() - stage4_start
        total_time = time.time() - start_time

        logger.info(f"Stage 4 (Vector Store) completed in {stage4_time:.2f}s")
        logger.info(f"=== Document processing complete in {total_time:.2f}s ===")

        success_msg = "Document processed successfully"
        if request.is_json:
            return jsonify({
                "success": True,
                "message": success_msg,
                "document_id": doc_id
            })

        flash(success_msg, "success")
        return redirect(url_for('api.index'))

    except Exception as e:
        error_msg = f"Error processing upload: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        if request.is_json:
            return jsonify({"error": f"Internal server error: {str(e)}"}), 500
        flash(f"Internal server error: {str(e)}", "error")
        return redirect(url_for('api.index'))

@bp.route('/query', methods=['GET', 'POST'])
def query_documents():
    """Query the vector database"""
    try:
        vector_store = VectorStore.get_instance()
        debug_info = vector_store.get_debug_info()

        # Only process query if it's a POST request
        if request.method == 'POST':
            if request.is_json:
                data = request.get_json()
                query = data.get('query', '').strip() if data else ''
            else:
                query = request.form.get('query', '').strip()

            if not query:
                error_msg = "Query cannot be empty"
                if request.is_json:
                    return jsonify({"error": error_msg}), 400
                flash(error_msg, "error")
                return redirect(url_for('api.index'))

            results, error_msg = vector_store.search(query)

            if error_msg:
                if request.is_json:
                    return jsonify({"error": error_msg}), 500
                flash(error_msg, "error")
                return redirect(url_for('api.index'))

            if request.is_json:
                return jsonify({
                    "results": [{
                        "content": result.content,
                        "similarity_score": result.similarity_score,
                        "metadata": result.metadata
                    } for result in results],
                    "message": "Query processed successfully"
                })

            if not results:
                flash("No matching results found", "warning")
            else:
                flash("Query processed successfully", "success")

            # Pass the results, query, and debug info back to the template
            return render_template('index.html', 
                                   results=results, 
                                   query=query, 
                                   debug_info=debug_info)

        # If it's a GET request, just show the form
        return render_template('index.html', debug_info=debug_info)

    except Exception as e:
        logger.error(f"Error processing query: {traceback.format_exc()}")
        if request.is_json:
            return jsonify({"error": f"Internal server error: {str(e)}"}), 500
        flash(f"Internal server error: {str(e)}", "error")
        return redirect(url_for('api.index'))


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
                'index_size': VectorStore.get_instance().index.ntotal
            }
        }
        return jsonify(health_data)
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@bp.route('/test-openai', methods=['GET'])
def test_openai_connection():
    """Test OpenAI API connection and display diagnostic information"""
    try:
        from services.embedding_service import EmbeddingService

        # Initialize embedding service
        embedding_service = EmbeddingService()

        # Get API key info (safely)
        api_key = os.environ.get("OPENAI_API_KEY", "")
        key_info = {
            'starts_with': api_key[:4] if api_key else 'None',
            'ends_with': api_key[-4:] if api_key else 'None',
            'length': len(api_key),
            'format_valid': api_key.startswith('sk-') if api_key else False
        }

        # Test embedding generation
        test_text = "This is a test of the OpenAI API connection."
        try:
            embedding = embedding_service.generate_embedding(test_text)
            success = embedding is not None
        except Exception as e:
            success = False
            error_details = str(e)
            if hasattr(e, 'response'):
                error_details = {
                    'status_code': e.response.status_code if hasattr(e.response, 'status_code') else 'unknown',
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'response_text': e.response.text if hasattr(e.response, 'text') else 'no response text'
                }

        # Prepare diagnostic info
        diagnostic_info = {
            'api_key_info': key_info,
            'test_status': 'success' if success else 'failed',
            'error_details': error_details if not success else None,
            'embedding_service_initialized': True,
            'model': embedding_service.client.models if hasattr(embedding_service, 'client') else None
        }

        return jsonify(diagnostic_info)

    except Exception as e:
        logger.error(f"Error in OpenAI test endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500