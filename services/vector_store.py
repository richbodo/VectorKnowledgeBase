import logging
import os
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from models import Document, VectorSearchResult
from services.embedding_service import EmbeddingService
from config import EMBEDDING_MODEL

logger = logging.getLogger(__name__)

def chunk_text(text: str, max_chunk_size: int = 4000) -> List[str]:
    """Split text into smaller chunks, trying to break at sentence boundaries."""
    sentences = text.replace('\n', ' ').split('.')
    chunks = []
    current_chunk = []
    current_size = 0

    for sentence in sentences:
        sentence = sentence.strip() + '.'  # Restore the period
        sentence_size = len(sentence) // 4  # Rough estimate: 1 token ≈ 4 characters

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
    CHROMA_PERSIST_DIR = "chroma_db"

    def __init__(self):
        try:
            logger.info("Initializing ChromaDB vector store...")

            # Initialize ChromaDB client with persistence
            self.client = chromadb.PersistentClient(path=self.CHROMA_PERSIST_DIR)

            # Create or get collection
            openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=os.environ["OPENAI_API_KEY"],
                model_name=EMBEDDING_MODEL
            )

            self.collection = self.client.get_or_create_collection(
                name="pdf_documents",
                embedding_function=openai_ef,
                metadata={"hnsw:space": "cosine"}
            )

            self.documents: Dict[str, Document] = {}
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
            logger.info(f"Starting document processing: {document.id}")
            logger.info(f"Document content length: {len(document.content)} chars")

            # Split document into chunks
            chunks = chunk_text(document.content)
            logger.info(f"Split document into {len(chunks)} chunks")

            # Create unique IDs for each chunk
            chunk_ids = [f"{document.id}_chunk_{i}" for i in range(len(chunks))]

            # Add chunks to ChromaDB
            self.collection.add(
                ids=chunk_ids,
                documents=chunks,
                metadatas=[{
                    "document_id": document.id,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    **document.metadata
                } for i in range(len(chunks))]
            )

            # Store document
            self.documents[document.id] = document
            logger.info(f"Added document with {len(chunks)} chunks")

            return True, None

        except Exception as e:
            error_msg = f"Error adding document to vector store: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def search(self, query: str, k: int = 3, similarity_threshold: float = 0.3) -> Tuple[List[VectorSearchResult], Optional[str]]:
        """Search for similar document chunks"""
        try:
            if not self.documents:
                logger.warning("No documents in vector store")
                return [], "No documents available for search"

            # Query ChromaDB
            results = self.collection.query(
                query_texts=[query],
                n_results=k * 2,  # Request more results to account for filtering
                include=["documents", "metadatas", "distances"]
            )

            if not results["ids"][0]:
                return [], None

            search_results = []
            seen_docs = set()

            for i, (chunk_text, metadata, distance) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )):
                # Convert distance to similarity score (ChromaDB uses cosine distance)
                similarity = 1 - distance

                # Filter out low similarity matches
                if similarity < similarity_threshold:
                    continue

                doc_id = metadata["document_id"]
                doc = self.documents[doc_id]

                # Add context about which part of the document this is
                chunk_context = f"(Part {metadata['chunk_index'] + 1} of {metadata['total_chunks']})"

                result = VectorSearchResult(
                    document_id=doc.id,
                    content=f"{chunk_text}\n{chunk_context}",
                    similarity_score=similarity,
                    metadata={
                        **doc.metadata,
                        "chunk_index": metadata["chunk_index"],
                        "total_chunks": metadata["total_chunks"]
                    }
                )

                search_results.append(result)

                if len(search_results) >= k:
                    break

            # Sort by similarity score
            search_results.sort(key=lambda x: x.similarity_score, reverse=True)

            if not search_results:
                logger.info("No results met the similarity threshold")
                return [], "No relevant matches found"

            return search_results, None

        except Exception as e:
            error_msg = f"Error searching vector store: {str(e)}"
            logger.error(error_msg)
            return [], error_msg

    def get_debug_info(self) -> Dict:
        """Get debug information about vector store state"""
        return {
            "document_count": len(self.documents),
            "index_size": self.collection.count(),
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

    def _load_state(self):
        """Load document metadata from ChromaDB"""
        try:
            # Get all documents from ChromaDB
            all_results = self.collection.get()
            if not all_results["ids"]:
                return

            # Reconstruct documents from chunks
            for metadata in all_results["metadatas"]:
                doc_id = metadata["document_id"]
                if doc_id not in self.documents:
                    self.documents[doc_id] = Document(
                        id=doc_id,
                        content="",  # Will be populated from chunks
                        metadata={k: v for k, v in metadata.items() 
                                 if k not in ["document_id", "chunk_index", "total_chunks"]},
                        created_at=datetime.now()  # Default to now if not stored
                    )

            logger.info(f"Loaded {len(self.documents)} documents from ChromaDB")

        except Exception as e:
            logger.warning(f"Could not load existing vector store state: {str(e)}")
            # Continue with empty state

def init_vector_store():
    """Initialize vector store singleton"""
    return VectorStore.get_instance()