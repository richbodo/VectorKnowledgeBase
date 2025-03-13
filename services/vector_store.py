import logging
import os
import chromadb
from chromadb.api.types import EmbeddingFunction
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from models import Document, VectorSearchResult
from services.embedding_service import EmbeddingService
from config import EMBEDDING_MODEL

logger = logging.getLogger(__name__)

def chunk_text(text: str, max_tokens: int = 500) -> List[str]:
    """Split text into smaller chunks to stay under token limits."""
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        current_chunk_size = len(current_chunk)
        if current_chunk_size >= max_tokens:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
        current_chunk.append(word)

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

class CustomEmbeddingFunction(EmbeddingFunction):
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service

    def __call__(self, input: List[str]) -> List[List[float]]:
        try:
            logger.info(f"Processing {len(input)} text chunks for embedding")
            embeddings = []
            for i, text in enumerate(input):
                try:
                    logger.info(f"Generating embedding for chunk {i+1}/{len(input)}")
                    embedding = self.embedding_service.generate_embedding(text)
                    embeddings.append(embedding)
                    logger.info(f"Successfully generated embedding for chunk {i+1}")
                except Exception as e:
                    logger.error(f"Error generating embedding for text chunk {i+1}: {str(e)}")
                    logger.error(f"Exception type: {type(e)}")
                    logger.error("Full exception details:", exc_info=True)
                    raise
            logger.info(f"Successfully generated {len(embeddings)} embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"Error in embedding function: {str(e)}")
            logger.error("Full exception details:", exc_info=True)
            raise

class VectorStore:
    _instance = None
    CHROMA_PERSIST_DIR = "chroma_db"

    def __init__(self):
        try:
            logger.info("Initializing ChromaDB vector store...")

            # Create ChromaDB client with telemetry disabled
            self.client = chromadb.PersistentClient(
                path=self.CHROMA_PERSIST_DIR,
                settings=chromadb.Settings(
                    anonymized_telemetry=False
                )
            )
            logger.info("ChromaDB client created successfully")

            # Initialize embedding service first
            logger.info("Initializing embedding service...")
            self.embedding_service = EmbeddingService()
            logger.info("Embedding service initialized successfully")

            # Create embedding function instance
            logger.info("Creating custom embedding function...")
            embedding_func = CustomEmbeddingFunction(self.embedding_service)
            logger.info("Custom embedding function created successfully")

            # Check if collection exists and create it if not
            collection_name = "pdf_documents"
            existing_collections = self.client.list_collections()
            collection_exists = collection_name in existing_collections
            
            if not collection_exists:
                logger.info(f"Collection '{collection_name}' not found, creating it...")
            else:
                logger.info(f"Collection '{collection_name}' found")
                
            # Always use get_or_create to ensure the collection exists
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=embedding_func,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Collection '{collection_name}' setup complete")

            self.documents: Dict[str, Document] = {}
            self._load_state()
            logger.info(f"Vector store initialized with {len(self.documents)} documents")
        except Exception as e:
            logger.error(f"Error initializing vector store: {str(e)}")
            logger.error("Full initialization error details:", exc_info=True)
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

            try:
                # Add chunks to ChromaDB
                self.collection.add(
                    ids=chunk_ids,
                    documents=chunks,
                    metadatas=[{
                        "document_id": document.id,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "filename": document.metadata.get("filename", "Unknown"),
                        "content_type": document.metadata.get("content_type", "Unknown"),
                        "size": document.metadata.get("size", 0)
                    } for i in range(len(chunks))]
                )

                # Immediately update in-memory state with the new document
                self.documents[document.id] = document
                logger.info(f"Added document {document.id} with {len(chunks)} chunks")
                logger.info(f"Current document count: {len(self.documents)}")

                # Verify document was added to ChromaDB
                chroma_count = self.collection.count()
                logger.info(f"ChromaDB collection count: {chroma_count}")
                return True, None

            except Exception as e:
                error_msg = f"Error adding document to vector store: {str(e)}"
                logger.error(error_msg)
                logger.error("Full error details:", exc_info=True)
                return False, error_msg

        except Exception as e:
            error_msg = f"Error adding document to vector store: {str(e)}"
            logger.error(error_msg)
            logger.error("Full error details:", exc_info=True)
            return False, error_msg

    def search(self, query: str, k: int = 3, similarity_threshold: float = 0.1) -> Tuple[List[VectorSearchResult], Optional[str]]:
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
            for i, (chunk_text, metadata, distance) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )):
                # Convert distance to similarity score (ChromaDB uses cosine distance)
                similarity = 1 - distance

                # Filter out very low similarity matches
                if similarity < similarity_threshold:
                    continue

                doc_id = metadata["document_id"]

                result = VectorSearchResult(
                    document_id=doc_id,
                    content=chunk_text,
                    similarity_score=similarity,
                    metadata={
                        "filename": metadata["filename"],
                        "chunk_index": metadata["chunk_index"],
                        "total_chunks": metadata["total_chunks"],
                        "content_type": metadata["content_type"]
                    }
                )

                search_results.append(result)

                if len(search_results) >= k:
                    break

            # Sort by similarity score
            search_results.sort(key=lambda x: x.similarity_score, reverse=True)

            if not search_results:


# Define a constant for ChromaDB persistence directory
CHROMA_PERSIST_DIR = "chroma_db"

def ensure_collection_exists():
    """Utility function to ensure the pdf_documents collection exists"""
    try:
        logger.info("Ensuring pdf_documents collection exists...")
        client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=chromadb.Settings(
                anonymized_telemetry=False
            )
        )
        
        collection_name = "pdf_documents"
        existing_collections = client.list_collections()
        
        if collection_name not in existing_collections:
            logger.info(f"Collection '{collection_name}' not found, creating it...")
            # Create a basic collection without embedding function
            # The full VectorStore will initialize properly later
            client.create_collection(name=collection_name)
            logger.info(f"Created collection '{collection_name}'")
            return True
        else:
            logger.info(f"Collection '{collection_name}' already exists")
            return True
    except Exception as e:
        logger.error(f"Error ensuring collection exists: {str(e)}")
        logger.error("Full error details:", exc_info=True)
        return False

                logger.info("No results met the similarity threshold")
                return [], "No relevant matches found"

            return search_results, None

        except Exception as e:
            error_msg = f"Error searching vector store: {str(e)}"
            logger.error(error_msg)
            return [], error_msg

    def _load_state(self):
        """Load document metadata from ChromaDB"""
        try:
            logger.info("Loading state from ChromaDB...")
            all_results = self.collection.get()
            if not all_results["ids"]:
                logger.info("No documents found in ChromaDB")
                return

            logger.info(f"Found {len(all_results['ids'])} entries in ChromaDB")

            # Track processed document IDs to avoid duplicates
            processed_doc_ids = set()

            for metadata in all_results["metadatas"]:
                doc_id = metadata["document_id"]
                if doc_id not in processed_doc_ids:
                    processed_doc_ids.add(doc_id)
                    if doc_id not in self.documents:
                        self.documents[doc_id] = Document(
                            id=doc_id,
                            content="",  # Only store metadata
                            metadata={k: v for k, v in metadata.items()
                                     if k not in ["document_id", "chunk_index", "total_chunks"]},
                            created_at=datetime.now()
                        )

            logger.info(f"Loaded {len(self.documents)} unique documents from ChromaDB")
            logger.info(f"Document IDs: {list(self.documents.keys())}")

        except Exception as e:
            logger.error(f"Could not load existing vector store state: {str(e)}")
            logger.error("Full error details:", exc_info=True)
            # Continue with empty state

    def get_debug_info(self) -> Dict:
        """Get debug information about vector store state"""
        try:
            # Force a state reload to ensure latest data
            self._load_state()

            return {
                "document_count": len(self.documents),
                "collection_info": {
                    "name": "pdf_documents",
                    "document_count": self.collection.count() if hasattr(self, 'collection') else 0
                },
                "documents": [
                    {
                        "id": doc_id,
                        "filename": doc.metadata.get("filename", "Unknown"),
                        "size": doc.metadata.get("size", 0),
                        "created_at": doc.created_at.isoformat() if hasattr(doc, 'created_at') else None
                    }
                    for doc_id, doc in self.documents.items()
                ]
            }
        except Exception as e:
            logger.error(f"Error getting debug info: {str(e)}")
            return {
                "error": "Failed to retrieve debug information",
                "document_count": 0,
                "documents": []
            }

def init_vector_store():
    """Initialize vector store singleton"""
    try:
        logger.info("Initializing vector store singleton...")
        instance = VectorStore.get_instance()
        
        # Explicitly verify collection exists after initialization
        collection_name = "pdf_documents"
        logger.info(f"Verifying collection '{collection_name}' exists...")
        
        # Force create collection if it doesn't exist
        if collection_name not in instance.client.list_collections():
            logger.warning(f"Collection '{collection_name}' not found after initialization, creating it now...")
            # This is just a fallback, the VectorStore.__init__ should have created it already
            embedding_func = CustomEmbeddingFunction(instance.embedding_service)
            instance.collection = instance.client.create_collection(
                name=collection_name,
                embedding_function=embedding_func,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Created collection '{collection_name}' as fallback")
        
        logger.info("Vector store initialization complete")
        debug_info = instance.get_debug_info()
        logger.info(f"Vector store state: {debug_info}")
        return instance
    except Exception as e:
        logger.error(f"Error initializing vector store: {str(e)}")
        logger.error("Full error details:", exc_info=True)
        # In deployment mode, return None instead of raising exception
        if os.environ.get("REPL_DEPLOYMENT"):
            logger.warning("Deployment mode - continuing without vector store")
            return None
        raise