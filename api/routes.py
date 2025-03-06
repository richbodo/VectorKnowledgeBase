import uuid
import logging
import traceback
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from schemas.requests import QueryRequest
from schemas.responses import UploadResponse, QueryResponse, ErrorResponse
from services.pdf_processor import PDFProcessor
from services.vector_store import VectorStore
from models import Document
from config import MAX_FILE_SIZE, ALLOWED_FILE_TYPES

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/upload", 
    response_model=UploadResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    """Upload and process a PDF document"""
    try:
        # Validate file size
        content = await file.read()
        file_size = len(content)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size ({file_size} bytes) exceeds maximum limit ({MAX_FILE_SIZE} bytes)"
            )

        # Validate file type
        if file.content_type not in ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type '{file.content_type}'. Only PDF files are allowed"
            )

        # Process PDF
        text_content, error = PDFProcessor.extract_text(content)

        if error:
            logger.error(f"PDF processing error: {error}")
            raise HTTPException(status_code=400, detail=error)

        if not text_content:
            raise HTTPException(
                status_code=400,
                detail="No text content could be extracted from the PDF"
            )

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
            raise HTTPException(
                status_code=500,
                detail="Failed to process document - vector store error"
            )

        return UploadResponse(
            success=True,
            message="Document processed successfully",
            document_id=doc_id
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error processing upload: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/query",
    response_model=QueryResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def query_documents(request: QueryRequest) -> QueryResponse:
    """Query the vector database"""
    try:
        query = request.query.strip()
        if not query:
            raise HTTPException(
                status_code=400,
                detail="Query cannot be empty"
            )

        vector_store = VectorStore.get_instance()
        results = vector_store.search(query)

        if results is None:
            logger.error("Vector store search returned None")
            raise HTTPException(
                status_code=500,
                detail="Failed to perform vector search"
            )

        return QueryResponse(
            results=[{
                "content": result.content,
                "similarity_score": result.similarity_score,
                "metadata": result.metadata
            } for result in results],
            message="Query processed successfully"
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error processing query: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )