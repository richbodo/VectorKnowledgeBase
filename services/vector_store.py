import json
import logging
import faiss
import numpy as np
import os
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from models import Document, VectorSearchResult
from services.embedding_service import EmbeddingService
from config import VECTOR_DIMENSION, FAISS_INDEX_PATH, DOCUMENT_STORE_PATH

logger = logging.getLogger(__name__)

class VectorStore:
    _instance = None

    def __init__(self):
        try:
            logger.info("Initializing vector store...")
            self.index = faiss.IndexFlatL2(VECTOR_DIMENSION)
            self.documents: Dict[str, Document] = {}
            self.embedding_service = EmbeddingService()
            self.last_api_error = None  # Track last API error
            self._load_state()
            logger.info(f"Vector store initialized with {len(self.documents)} documents")
        except Exception as e:
            logger.error(f"Error initializing vector store: {str(e)}")
            raise

    @classmethod
    def get_instance(cls) -> 'VectorStore':
        if cls._instance is None:
            cls._instance = VectorStore()
        return cls._instance

    def add_document(self, document: Document) -> Tuple[bool, Optional[str]]:
        """Add document to vector store"""
        try:
            start_time = time.time()
            logger.info(f"Starting document processing: {document.id}")
            logger.info(f"Document content length: {len(document.content)} chars")
            logger.info(f"Document metadata: {document.metadata}")

            # Stage 1: Generate embedding
            logger.info("Generating embedding...")
            embedding_start = time.time()
            embedding = self.embedding_service.generate_embedding(document.content)
            if embedding is None:
                error_msg = "Failed to generate embedding for document"
                self.last_api_error = error_msg  # Store API error
                logger.error(error_msg)
                return False, error_msg

            embedding_time = time.time() - embedding_start
            logger.info(f"Embedding generation completed in {embedding_time:.2f}s")

            # Stage 2: Add to FAISS index
            logger.info(f"Adding embedding to FAISS index (current size: {self.index.ntotal})")
            index_start = time.time()
            self.index.add(np.array([embedding], dtype=np.float32))
            logger.info(f"New FAISS index size: {self.index.ntotal}")
            index_time = time.time() - index_start
            logger.info(f"FAISS index update completed in {index_time:.2f}s")

            # Stage 3: Add to document store
            self.documents[document.id] = document
            logger.info(f"Document added to in-memory store. Total documents: {len(self.documents)}")

            # Stage 4: Persist state
            logger.info("Persisting state to disk...")
            save_start = time.time()
            self._save_state()
            save_time = time.time() - save_start
            logger.info(f"State persistence completed in {save_time:.2f}s")

            total_time = time.time() - start_time
            logger.info(f"Document successfully added in {total_time:.2f}s")
            self.last_api_error = None  # Clear any previous error on success
            return True, None

        except Exception as e:
            error_msg = f"Error adding document to vector store: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg

    def search(self, query: str, k: int = 3) -> Tuple[List[VectorSearchResult], Optional[str]]:
        """Search for similar documents"""
        try:
            logger.info(f"Processing search query: {query}")
            if not self.documents:
                logger.warning("No documents in vector store")
                return [], "No documents available for search"

            logger.info("Generating query embedding")
            query_embedding = self.embedding_service.generate_embedding(query)
            if query_embedding is None:
                error_msg = "Failed to generate query embedding"
                logger.error(error_msg)
                return [], error_msg

            logger.info(f"Searching FAISS index with k={k}")
            distances, indices = self.index.search(
                np.array([query_embedding], dtype=np.float32), 
                min(k, len(self.documents))
            )

            results = []
            for i, idx in enumerate(indices[0]):
                if idx < 0 or idx >= len(self.documents):
                    continue

                doc_id = list(self.documents.keys())[idx]
                doc = self.documents[doc_id]
                similarity = float(1 / (1 + distances[0][i]))

                logger.info(f"Found match: doc_id={doc_id}, similarity={similarity:.4f}")
                results.append(
                    VectorSearchResult(
                        document_id=doc.id,
                        content=doc.content,
                        similarity_score=similarity,
                        metadata=doc.metadata
                    )
                )

            return results, None

        except Exception as e:
            error_msg = f"Error searching vector store: {str(e)}"
            logger.error(error_msg)
            return [], error_msg

    def get_debug_info(self) -> Dict:
        """Get debug information about vector store state"""
        return {
            "document_count": len(self.documents),
            "index_size": self.index.ntotal,
            "last_api_error": self.last_api_error,  # Include API error in debug info
            "documents": [
                {
                    "id": doc_id,
                    "filename": doc.metadata.get("filename"),
                    "size": doc.metadata.get("size"),
                    "created_at": doc.created_at.isoformat()
                }
                for doc_id, doc in self.documents.items()
            ]
        }

    def _save_state(self):
        """Save index and documents to disk"""
        try:
            logger.info(f"Saving FAISS index to {FAISS_INDEX_PATH}")
            faiss.write_index(self.index, FAISS_INDEX_PATH)
            logger.info("FAISS index saved successfully")

            logger.info(f"Saving document store to {DOCUMENT_STORE_PATH}")
            document_data = {
                doc_id: {
                    "content": doc.content,
                    "metadata": doc.metadata,
                    "created_at": doc.created_at.isoformat()
                }
                for doc_id, doc in self.documents.items()
            }

            with open(DOCUMENT_STORE_PATH, 'w') as f:
                json.dump(document_data, f)
            logger.info("Document store saved successfully")

        except Exception as e:
            logger.error(f"Error saving vector store state: {str(e)}", exc_info=True)
            raise

    def _load_state(self):
        """Load index and documents from disk"""
        try:
            if os.path.exists(FAISS_INDEX_PATH):
                self.index = faiss.read_index(FAISS_INDEX_PATH)
                logger.info(f"Loaded FAISS index from {FAISS_INDEX_PATH}")

            if os.path.exists(DOCUMENT_STORE_PATH):
                with open(DOCUMENT_STORE_PATH, 'r') as f:
                    document_data = json.load(f)

                for doc_id, data in document_data.items():
                    self.documents[doc_id] = Document(
                        id=doc_id,
                        content=data["content"],
                        metadata=data["metadata"],
                        created_at=datetime.fromisoformat(data["created_at"])
                    )
                logger.info(f"Loaded {len(self.documents)} documents from {DOCUMENT_STORE_PATH}")

        except Exception as e:
            logger.warning(f"Could not load existing vector store state: {str(e)}")
            # Continue with empty state

def init_vector_store():
    """Initialize vector store singleton"""
    return VectorStore.get_instance()