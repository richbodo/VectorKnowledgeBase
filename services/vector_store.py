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

def chunk_text(text: str, max_chunk_size: int = 4000) -> List[str]:
    """Split text into smaller chunks, trying to break at sentence boundaries."""
    # Split into sentences (rough approximation)
    sentences = text.replace('\n', ' ').split('.')
    chunks = []
    current_chunk = []
    current_size = 0

    for sentence in sentences:
        sentence = sentence.strip() + '.'  # Restore the period
        # Rough estimate: 1 token ≈ 4 characters
        sentence_size = len(sentence) // 4

        if current_size + sentence_size > max_chunk_size:
            if current_chunk:  # Save current chunk if it exists
                chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_size = sentence_size
        else:
            current_chunk.append(sentence)
            current_size += sentence_size

    if current_chunk:  # Add the last chunk
        chunks.append(' '.join(current_chunk))

    return chunks

class VectorStore:
    _instance = None

    def __init__(self):
        try:
            logger.info("Initializing vector store...")
            self.index = faiss.IndexFlatL2(VECTOR_DIMENSION)
            self.documents: Dict[str, Document] = {}
            self.embedding_service = EmbeddingService()
            self.last_api_error = None
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
        """Add document to vector store with chunking"""
        try:
            start_time = time.time()
            logger.info(f"Starting document processing: {document.id}")
            logger.info(f"Document content length: {len(document.content)} chars")

            # Split document into chunks
            chunks = chunk_text(document.content)
            logger.info(f"Split document into {len(chunks)} chunks")

            embeddings = []
            for i, chunk in enumerate(chunks):
                logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                embedding = self.embedding_service.generate_embedding(chunk)
                if embedding is None:
                    error_msg = f"Failed to generate embedding for chunk {i+1}"
                    logger.error(error_msg)
                    return False, error_msg
                embeddings.append(embedding)

            # Add all embeddings to FAISS index
            embeddings_array = np.array(embeddings, dtype=np.float32)
            self.index.add(embeddings_array)

            # Store document
            self.documents[document.id] = document
            logger.info(f"Added document with {len(embeddings)} embeddings")

            # Save state
            self._save_state()

            total_time = time.time() - start_time
            logger.info(f"Document successfully added in {total_time:.2f}s")
            return True, None

        except Exception as e:
            error_msg = f"Error adding document to vector store: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def search(self, query: str, k: int = 3) -> Tuple[List[VectorSearchResult], Optional[str]]:
        """Search for similar documents"""
        try:
            if not self.documents:
                logger.warning("No documents in vector store")
                return [], "No documents available for search"

            query_embedding = self.embedding_service.generate_embedding(query)
            if query_embedding is None:
                error_msg = "Failed to generate query embedding"
                logger.error(error_msg)
                return [], error_msg

            distances, indices = self.index.search(
                np.array([query_embedding], dtype=np.float32),
                min(k, self.index.ntotal)
            )

            results = []
            seen_docs = set()  # Track unique documents

            for i, idx in enumerate(indices[0]):
                if idx < 0 or idx >= self.index.ntotal:
                    continue

                # Get document ID and content
                doc_id = list(self.documents.keys())[idx // len(chunk_text(list(self.documents.values())[0].content))]
                if doc_id in seen_docs:
                    continue

                doc = self.documents[doc_id]
                similarity = float(1 / (1 + distances[0][i]))

                results.append(
                    VectorSearchResult(
                        document_id=doc.id,
                        content=doc.content,
                        similarity_score=similarity,
                        metadata=doc.metadata
                    )
                )
                seen_docs.add(doc_id)

                if len(results) >= k:
                    break

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
            "last_api_error": self.last_api_error,
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