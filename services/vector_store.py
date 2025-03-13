import logging
import os
import chromadb
from chromadb.api.types import EmbeddingFunction
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from models import Document, VectorSearchResult
from services.embedding_service import EmbeddingService
from config import EMBEDDING_MODEL, CHROMA_DB_PATH

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

    def __init__(self):
        try:
            abs_path = os.path.abspath(CHROMA_DB_PATH)
            cwd = os.getcwd()
            logger.info(f"Current working directory: {cwd}")
            logger.info(f"Attempting to access ChromaDB at absolute path: {abs_path}")
            logger.info(f"Directory exists: {os.path.exists(abs_path)}")
            logger.info(f"Initializing ChromaDB vector store at {abs_path}...")
            logger.info(f"ChromaDB version: {chromadb.__version__}")
            # Simplified client creation with single path reference
            self.client = chromadb.PersistentClient(
                path=CHROMA_DB_PATH,
                settings=chromadb.Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
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

            # Use the custom embedding function
            logger.info("Creating/getting collection...")
            self.collection = self.client.get_or_create_collection(
                name="pdf_documents",
                metadata={"hnsw:space": "cosine"}
            )
            
            # Verify collection exists and is accessible
            collection_count = self.collection.count()
            logger.info(f"Collection initialized with {collection_count} existing documents")
            logger.info("Collection setup complete")

            logger.info(f"Embedding function used: {self.collection._embedding_function}")

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
                try:
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
                    
                    # ChromaDB PersistentClient automatically persists data to disk,
                    # no need to explicitly call persist() in newer versions
                    
                    # Immediately update in-memory state with the new document
                    self.documents[document.id] = document
                    logger.info(f"Added document {document.id} with {len(chunks)} chunks")
                    logger.info(f"Current document count: {len(self.documents)}")

                    # Verify document was added to ChromaDB
                    chroma_count = self.collection.count()
                    logger.info(f"ChromaDB collection count: {chroma_count}")
                    
                    # Additional verification
                    verify_results = self.collection.get(
                        where={"document_id": document.id},
                        limit=1
                    )
                    if verify_results["ids"]:
                        logger.info(f"Verified document {document.id} was properly added to ChromaDB")
                    else:
                        logger.warning(f"Document {document.id} may not have been properly added to ChromaDB")
                        
                    return True, None
                except Exception as add_error:
                    error_msg = f"ChromaDB add operation failed: {str(add_error)}"
                    logger.error(error_msg)
                    logger.error("Full error details:", exc_info=True)
                    return False, error_msg

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
                logger.info("No results met the similarity threshold")
                return [], "No relevant matches found"

            return search_results, None

        except Exception as e:
            error_msg = f"Error searching vector store: {str(e)}"
            logger.error(error_msg)
            return [], error_msg

    def _load_state(self):
        try:
            logger.info("Loading state from ChromaDB...")
            # Get all data from collection using get() method
            raw_data = self.collection.get()
            logger.info(f"Raw data from collection: {raw_data}")
            
            # Get count
            count = self.collection.count()
            
            # Process the data from raw_data instead of separate calls
            if raw_data and raw_data['ids']:
                for idx, doc_id in enumerate(raw_data['ids']):
                    self.documents[doc_id] = Document(
                        id=doc_id,
                        content=raw_data['documents'][idx] if raw_data['documents'] else None,
                        metadata=raw_data['metadatas'][idx] if raw_data['metadatas'] else {}
                    )
                logger.info(f"Loaded {len(self.documents)} documents from ChromaDB")
            else:
                logger.info("No documents found in ChromaDB based on get() response")
            
        except Exception as e:
            logger.error(f"Error during state loading: {str(e)}", exc_info=True)

    def get_debug_info(self) -> Dict:
        """Get debug information about vector store state"""
        try:
            # Force a state reload to ensure latest data
            self._load_state()
            
            # Get information about all collections
            collections_info = []
            try:
                all_collections = self.client.list_collections()
                for collection in all_collections:
                    try:
                        coll_instance = self.client.get_collection(name=collection.name)
                        count = coll_instance.count()
                        
                        # Get a sample document if available
                        sample_info = {}
                        if count > 0:
                            try:
                                sample = coll_instance.get(limit=1)
                                if sample and sample.get("ids"):
                                    sample_info = {
                                        "sample_id": sample["ids"][0],
                                        "has_metadata": bool(sample.get("metadatas") and sample["metadatas"][0]),
                                        "metadata_keys": list(sample["metadatas"][0].keys()) if sample.get("metadatas") and sample["metadatas"][0] else []
                                    }
                            except Exception as sample_err:
                                sample_info = {"error": str(sample_err)}
                                
                        collections_info.append({
                            "name": collection.name,
                            "count": count,
                            "sample": sample_info
                        })
                    except Exception as coll_err:
                        collections_info.append({
                            "name": collection.name,
                            "error": str(coll_err)
                        })
            except Exception as list_err:
                collections_info = [{"error": f"Failed to list collections: {str(list_err)}"}]

            return {
                "document_count": len(self.documents),
                "collection_info": {
                    "name": "pdf_documents",
                    "document_count": self.collection.count() if hasattr(self, 'collection') else 0
                },
                "all_collections": collections_info,
                "documents": [
                    {
                        "id": doc_id,
                        "filename": doc.metadata.get("filename", "Unknown"),
                        "size": doc.metadata.get("size", 0),
                        "source": doc.metadata.get("source", "pdf_documents"),
                        "created_at": doc.created_at.isoformat() if hasattr(doc, 'created_at') else None
                    }
                    for doc_id, doc in self.documents.items()
                ],
                "chroma_db_path": os.path.abspath(CHROMA_DB_PATH),
                "chroma_version": chromadb.__version__
            }
        except Exception as e:
            logger.error(f"Error getting debug info: {str(e)}")
            return {
                "error": f"Failed to retrieve debug information: {str(e)}",
                "document_count": 0,
                "documents": []
            }

def init_vector_store():
    """Initialize vector store singleton"""
    try:
        logger.info("Initializing vector store singleton...")
        instance = VectorStore.get_instance()
        logger.info("Vector store initialization complete")
        debug_info = instance.get_debug_info()
        logger.info(f"Vector store state: {debug_info}") #Removed json.dumps as it's not strictly needed and might cause issues.
        return instance
    except Exception as e:
        logger.error(f"Error initializing vector store: {str(e)}")
        logger.error("Full error details:", exc_info=True)
        # In deployment mode, return None instead of raising exception
        if os.environ.get("REPL_DEPLOYMENT"):
            logger.warning("Deployment mode - continuing without vector store")
            return None
        raise