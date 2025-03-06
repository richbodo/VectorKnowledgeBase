import json
import logging
import faiss
import numpy as np
import os
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
            self.index = faiss.IndexFlatL2(VECTOR_DIMENSION)
            self.documents: Dict[str, Document] = {}
            self.embedding_service = EmbeddingService()
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
            logger.info(f"Generating embedding for document {document.id}")
            embedding = self.embedding_service.generate_embedding(document.content)
            if embedding is None:
                error_msg = "Failed to generate embedding for document"
                logger.error(error_msg)
                return False, error_msg

            logger.info("Adding document embedding to FAISS index")
            self.index.add(np.array([embedding], dtype=np.float32))
            self.documents[document.id] = document
            self._save_state()
            logger.info(f"Successfully added document {document.id} to vector store")
            return True, None

        except Exception as e:
            error_msg = f"Error adding document to vector store: {str(e)}"
            logger.error(error_msg)
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
            faiss.write_index(self.index, FAISS_INDEX_PATH)
            logger.info(f"Saved FAISS index to {FAISS_INDEX_PATH}")

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
            logger.info(f"Saved document store to {DOCUMENT_STORE_PATH}")

        except Exception as e:
            logger.error(f"Error saving vector store state: {str(e)}")

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