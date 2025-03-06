import uuid
import logging
import traceback
from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
from services.pdf_processor import PDFProcessor
from services.vector_store import VectorStore
from models import Document
from config import MAX_FILE_SIZE, ALLOWED_FILE_TYPES

logger = logging.getLogger(__name__)
bp = Blueprint('api', __name__)

@bp.route('/upload', methods=['POST'])
def upload_document():
    """Upload and process a PDF document"""
    try:
        if 'file' not in request.files:
            raise BadRequest("No file provided")

        file = request.files['file']
        if not file.filename:
            raise BadRequest("No file selected")

        # Read file content
        content = file.read()
        file_size = len(content)

        # Validate file size
        if file_size > MAX_FILE_SIZE:
            raise BadRequest(
                f"File size ({file_size} bytes) exceeds maximum limit ({MAX_FILE_SIZE} bytes)"
            )

        # Validate file type
        if file.content_type not in ALLOWED_FILE_TYPES:
            raise BadRequest(
                f"Invalid file type '{file.content_type}'. Only PDF files are allowed"
            )

        # Process PDF
        text_content, error = PDFProcessor.extract_text(content)

        if error:
            logger.error(f"PDF processing error: {error}")
            raise BadRequest(error)

        if not text_content:
            raise BadRequest("No text content could be extracted from the PDF")

        # Create document
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

        # Add to vector store
        vector_store = VectorStore.get_instance()
        success = vector_store.add_document(document)

        if not success:
            raise Exception("Failed to process document - vector store error")

        return jsonify({
            "success": True,
            "message": "Document processed successfully",
            "document_id": doc_id
        })

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error processing upload: {traceback.format_exc()}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@bp.route('/query', methods=['POST'])
def query_documents():
    """Query the vector database"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            raise BadRequest("Query parameter is required")

        query = data['query'].strip()
        if not query:
            raise BadRequest("Query cannot be empty")

        vector_store = VectorStore.get_instance()
        results = vector_store.search(query)

        if results is None:
            logger.error("Vector store search returned None")
            raise Exception("Failed to perform vector search")

        return jsonify({
            "results": [{
                "content": result.content,
                "similarity_score": result.similarity_score,
                "metadata": result.metadata
            } for result in results],
            "message": "Query processed successfully"
        })

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error processing query: {traceback.format_exc()}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500