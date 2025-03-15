import logging
import os
import sqlite3
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
            
            # Ensure we use the absolute path for ChromaDB persistence
            abs_db_path = os.path.abspath(CHROMA_DB_PATH)
            logger.info(f"Using absolute ChromaDB path: {abs_db_path}")
            
            # Create client with proper persistence settings
            self.client = chromadb.PersistentClient(
                path=abs_db_path,
                settings=chromadb.Settings(
                    anonymized_telemetry=False,
                    allow_reset=False  # Prevent accidental resets
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

            # CRITICAL FIX: Explicitly specify embedding function here
            logger.info("Creating/getting collection with embedding function...")
            self.collection = self.client.get_or_create_collection(
                name="pdf_documents",
                embedding_function=embedding_func,  # <-- CRITICAL FIX HERE
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
        """Load document state from ChromaDB"""
        try:
            logger.info(f"Loading state from ChromaDB at {CHROMA_DB_PATH}...")
            
            # Check if the ChromaDB directory exists
            if os.path.exists(CHROMA_DB_PATH):
                logger.info(f"ChromaDB directory exists at: {CHROMA_DB_PATH}")
                try:
                    contents = os.listdir(CHROMA_DB_PATH)
                    logger.info(f"Directory contents: {contents}")
                    
                    # Check if SQLite file exists and log its size
                    sqlite_path = os.path.join(CHROMA_DB_PATH, "chroma.sqlite3")
                    if os.path.exists(sqlite_path):
                        size_mb = os.path.getsize(sqlite_path) / (1024 * 1024)
                        logger.info(f"SQLite file exists with size: {size_mb:.2f} MB")
                        
                        # Check SQLite data using direct access
                        try:
                            conn = sqlite3.connect(sqlite_path)
                            cursor = conn.cursor()
                            
                            # Check for embeddings
                            cursor.execute("SELECT COUNT(*) FROM embeddings")
                            embeddings_count = cursor.fetchone()[0]
                            logger.info(f"SQLite embeddings count: {embeddings_count}")
                            
                            # Check collections
                            cursor.execute("SELECT * FROM collections LIMIT 5")
                            collections = cursor.fetchall()
                            logger.info(f"Collections in SQLite: {collections}")
                            
                            # Check if any embeddings have metadata
                            cursor.execute("SELECT COUNT(*) FROM embeddings WHERE metadata IS NOT NULL")
                            metadata_count = cursor.fetchone()[0]
                            logger.info(f"Embeddings with metadata: {metadata_count}")
                            
                            # Check for tables
                            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                            tables = cursor.fetchall()
                            logger.info(f"Tables in SQLite: {tables}")
                            
                            conn.close()
                        except Exception as sql_e:
                            logger.error(f"Error checking SQLite data: {str(sql_e)}")
                except Exception as dir_e:
                    logger.error(f"Error checking directory: {str(dir_e)}")
            else:
                logger.warning(f"ChromaDB directory does not exist: {CHROMA_DB_PATH}")
            
            # Get document count from ChromaDB
            count = self.collection.count()
            logger.info(f"ChromaDB collection count: {count}")
            
            # If there are no documents, we're done
            if count == 0:
                logger.warning("No documents found in ChromaDB")
                return
                
            # Load document IDs from ChromaDB
            try:
                # Try to get all document IDs from the collection
                logger.info("Loading document data from ChromaDB...")
                all_docs = {}
                
                # Get all data from the collection
                try:
                    # Get all data without filters
                    raw_data = self.collection.get()
                    
                    if raw_data and 'metadatas' in raw_data and raw_data['metadatas']:
                        logger.info(f"Found {len(raw_data['metadatas'])} chunks with metadata")
                        
                        # Extract unique document IDs from metadata
                        for i, metadata in enumerate(raw_data['metadatas']):
                            if not metadata or 'document_id' not in metadata:
                                continue
                                
                            doc_id = metadata['document_id']
                            if doc_id not in all_docs:
                                logger.info(f"Found document ID in metadata: {doc_id}")
                                all_docs[doc_id] = {
                                    "filename": metadata.get("filename", "Unknown"),
                                    "content_type": metadata.get("content_type", "Unknown"),
                                    "size": metadata.get("size", 0),
                                    "total_chunks": metadata.get("total_chunks", 0)
                                }
                    
                    logger.info(f"Found {len(all_docs)} unique document IDs in ChromaDB metadata")
                    
                    # If we couldn't find any document IDs in metadata, try to extract them from chunk IDs
                    if not all_docs and 'ids' in raw_data and raw_data['ids']:
                        logger.info("No document IDs found in metadata, trying to extract from chunk IDs...")
                        for chunk_id in raw_data['ids']:
                            if '_chunk_' in chunk_id:
                                doc_id = chunk_id.split('_chunk_')[0]
                                if doc_id not in all_docs:
                                    logger.info(f"Extracted document ID from chunk ID: {doc_id}")
                                    all_docs[doc_id] = {"recovered": True}
                        
                        logger.info(f"Found {len(all_docs)} document IDs from chunk IDs")
                        
                except Exception as raw_e:
                    logger.error(f"Error getting raw data: {str(raw_e)}", exc_info=True)
                
                # Create document objects for each unique document ID
                for doc_id, doc_info in all_docs.items():
                    self.documents[doc_id] = Document(
                        id=doc_id,
                        content="",  # We don't store full content in memory
                        metadata=doc_info
                    )
                
                logger.info(f"Loaded {len(self.documents)} unique documents from ChromaDB")
                if self.documents:
                    logger.info(f"Document IDs: {list(self.documents.keys())[:5]}...")
                
            except Exception as e:
                logger.error(f"Error loading documents from ChromaDB: {str(e)}")
                logger.error("Full error details:", exc_info=True)
            
        except Exception as e:
            logger.error(f"Error loading state: {str(e)}")
            logger.error("Full error details:", exc_info=True)

    def get_debug_info(self) -> Dict:
        """Get debug information about vector store state"""
        try:
            # Get document count
            doc_count = len(self.documents)
            
            # Get collection count from ChromaDB
            collection_count = self.collection.count()
            
            # Document IDs
            doc_ids = list(self.documents.keys())[:5]  # First 5 for brevity
            
            # Check if database exists
            db_exists = os.path.exists(CHROMA_DB_PATH)
            db_contents = None
            db_size_mb = 0
            
            if db_exists and os.path.isdir(CHROMA_DB_PATH):
                try:
                    db_contents = os.listdir(CHROMA_DB_PATH)
                    sqlite_path = os.path.join(CHROMA_DB_PATH, "chroma.sqlite3")
                    if os.path.exists(sqlite_path):
                        db_size_mb = os.path.getsize(sqlite_path) / (1024 * 1024)
                except Exception:
                    pass
            
            return {
                "document_count": doc_count,
                "collection_count": collection_count,
                "document_ids_sample": doc_ids,
                "db_path": CHROMA_DB_PATH,
                "db_exists": db_exists,
                "db_contents": db_contents,
                "db_size_mb": round(db_size_mb, 2) if db_size_mb else 0
            }
        except Exception as e:
            logger.error(f"Error getting debug info: {str(e)}")
            return {
                "error": str(e)
            }

def init_vector_store():
    """Initialize vector store singleton"""
    try:
        logger.info("Initializing vector store...")
        instance = VectorStore.get_instance()
        logger.info("Vector store initialized successfully")
        return instance
    except Exception as e:
        logger.error(f"Error initializing vector store: {str(e)}")
        logger.error("Full error details:", exc_info=True)
        raise