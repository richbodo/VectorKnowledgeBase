import logging
import os
import json
import chromadb
from chromadb.api.types import EmbeddingFunction
from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime
from models import Document, VectorSearchResult
from services.embedding_service import EmbeddingService
from config import EMBEDDING_MODEL, CHROMA_DB_PATH, DOCUMENT_REGISTRY_PATH

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

    def _save_document_registry(self):
        """Save document registry to a persistent file"""
        try:
            # Create a serializable version of the documents dictionary
            registry_data = {
                "timestamp": datetime.now().isoformat(),
                "document_count": len(self.documents),
                "documents": [
                    {
                        "id": doc_id,
                        "filename": doc.metadata.get("filename", "Unknown"),
                        "content_type": doc.metadata.get("content_type", "Unknown"),
                        "size": doc.metadata.get("size", 0),
                        "created_at": doc.created_at.isoformat() if hasattr(doc, 'created_at') and doc.created_at else datetime.now().isoformat()
                    }
                    for doc_id, doc in self.documents.items()
                ]
            }
            
            # Save to persistent file
            with open(DOCUMENT_REGISTRY_PATH, 'w') as f:
                json.dump(registry_data, f, indent=2)
                
            logger.info(f"Saved document registry with {len(self.documents)} documents to {DOCUMENT_REGISTRY_PATH}")
            return True
        except Exception as e:
            logger.error(f"Error saving document registry: {str(e)}")
            logger.error("Full error details:", exc_info=True)
            return False
    
    def _load_document_registry(self) -> Set[str]:
        """Load document IDs from registry file and return the set of document IDs"""
        document_ids = set()
        try:
            if os.path.exists(DOCUMENT_REGISTRY_PATH):
                logger.info(f"Loading document registry from {DOCUMENT_REGISTRY_PATH}")
                with open(DOCUMENT_REGISTRY_PATH, 'r') as f:
                    registry_data = json.load(f)
                    
                logger.info(f"Document registry contains {registry_data.get('document_count', 0)} documents")
                
                # Extract document info and IDs
                for doc_info in registry_data.get('documents', []):
                    doc_id = doc_info.get('id')
                    if doc_id:
                        document_ids.add(doc_id)
                        
                        # Create document objects from registry data
                        if doc_id not in self.documents:
                            self.documents[doc_id] = Document(
                                id=doc_id,
                                content="",  # We don't need to load full content
                                metadata={
                                    "filename": doc_info.get("filename", "Unknown"),
                                    "content_type": doc_info.get("content_type", "Unknown"),
                                    "size": doc_info.get("size", 0),
                                    "source": "registry"
                                }
                            )
                
                logger.info(f"Loaded {len(document_ids)} document IDs from registry")
                
                # Additional registry validation
                if len(document_ids) != registry_data.get('document_count', 0):
                    logger.warning(f"Document count mismatch in registry: {len(document_ids)} vs {registry_data.get('document_count', 0)}")
            else:
                logger.info(f"Document registry file does not exist at {DOCUMENT_REGISTRY_PATH}")
        except Exception as e:
            logger.error(f"Error loading document registry: {str(e)}")
            logger.error("Full error details:", exc_info=True)
        
        return document_ids
            
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
                        
                        # Save document registry to ensure persistence across deployments
                        self._save_document_registry()
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
            logger.info(f"Loading state from ChromaDB at {CHROMA_DB_PATH}...")
            
            # Step 1: Check the document registry first as it's more reliable
            logger.info("Checking document registry first...")
            registry_doc_ids = self._load_document_registry()
            registry_doc_count = len(registry_doc_ids)
            logger.info(f"Document registry contains {registry_doc_count} documents")
            
            # Step 2: Try to load from ChromaDB itself as a backup
            # Get total document count first
            count = self.collection.count()
            logger.info(f"ChromaDB collection count: {count}")
            
            # Log storage information to help diagnose persistence issues
            if os.path.exists(CHROMA_DB_PATH):
                logger.info(f"ChromaDB directory exists at: {CHROMA_DB_PATH}")
                try:
                    contents = os.listdir(CHROMA_DB_PATH)
                    logger.info(f"Directory contents: {contents}")
                    
                    # Check if SQLite file exists
                    sqlite_path = os.path.join(CHROMA_DB_PATH, "chroma.sqlite3")
                    if os.path.exists(sqlite_path):
                        size_mb = os.path.getsize(sqlite_path) / (1024 * 1024)
                        logger.info(f"SQLite file exists with size: {size_mb:.2f} MB")
                        
                        # Check SQLite data
                        try:
                            import sqlite3
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
                            
                            conn.close()
                        except Exception as sql_e:
                            logger.error(f"Error checking SQLite data: {str(sql_e)}")
                except Exception as dir_e:
                    logger.error(f"Error checking directory: {str(dir_e)}")
            else:
                logger.warning(f"ChromaDB directory does not exist: {CHROMA_DB_PATH}")
            
            # If we already have documents from the registry and nothing in ChromaDB,
            # we might need to re-add the documents to ChromaDB
            if registry_doc_count > 0 and count == 0:
                logger.warning("Documents exist in registry but ChromaDB is empty!")
                # We would handle re-adding documents here if we had the content,
                # but since we don't store content in the registry, we just keep the metadata
                
            # If we don't have documents from registry or ChromaDB is empty, nothing more to do
            if registry_doc_count == 0 and count == 0:
                logger.warning("No documents found in registry or ChromaDB")
                return
                
            # Step 3: If there are documents in ChromaDB, try to extract them as a fallback
            if count > 0 and registry_doc_count == 0:
                # CRITICAL: We need to extract unique document IDs from the metadata
                # Document IDs are stored in each chunk's metadata as 'document_id'
                try:
                    # Direct approach - query for any chunks and use the document_id field
                    logger.info("Querying for all documents from ChromaDB...")
                    all_docs = {}
                    
                    # Collect all data without filters first
                    try:
                        raw_data = self.collection.get()
                        logger.info(f"Raw data keys: {raw_data.keys() if raw_data else 'None'}")
                        logger.info(f"Raw data ids count: {len(raw_data['ids']) if raw_data and 'ids' in raw_data else 0}")
                        
                        if raw_data and 'metadatas' in raw_data and raw_data['metadatas']:
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
                        
                        logger.info(f"Found {len(all_docs)} document IDs in metadata")
                        
                        # Check IDs for document info if metadata approach didn't work
                        if not all_docs and 'ids' in raw_data and raw_data['ids']:
                            logger.info("No document IDs found in metadata, checking chunk IDs...")
                            for chunk_id in raw_data['ids']:
                                if '_chunk_' in chunk_id:
                                    doc_id = chunk_id.split('_chunk_')[0]
                                    if doc_id not in all_docs:
                                        logger.info(f"Extracted document ID from chunk ID: {doc_id}")
                                        all_docs[doc_id] = {"recovered": True}
                            
                            logger.info(f"Found {len(all_docs)} document IDs from chunk IDs")
                            
                    except Exception as raw_e:
                        logger.error(f"Error getting raw data: {str(raw_e)}", exc_info=True)
                    
                    # If we still don't have documents, try direct query with limit/offset
                    if not all_docs:
                        logger.info("Using pagination to find documents...")
                        batch_size = 10
                        for offset in range(0, max(count, 100), batch_size):
                            try:
                                logger.info(f"Querying batch with offset {offset}, limit {batch_size}")
                                batch_data = self.collection.get(limit=batch_size, offset=offset)
                                
                                if not batch_data or 'metadatas' not in batch_data or not batch_data['metadatas']:
                                    logger.info(f"No valid data in batch at offset {offset}")
                                    continue
                                
                                # Process this batch
                                for i, metadata in enumerate(batch_data['metadatas']):
                                    if metadata and 'document_id' in metadata:
                                        doc_id = metadata['document_id']
                                        if doc_id not in all_docs:
                                            logger.info(f"Found document ID in batch: {doc_id}")
                                            all_docs[doc_id] = {
                                                "filename": metadata.get("filename", "Unknown"),
                                                "content_type": metadata.get("content_type", "Unknown")
                                            }
                            except Exception as batch_e:
                                logger.error(f"Error processing batch at offset {offset}: {str(batch_e)}")
                    
                    # Now populate the documents dictionary with reconstructed documents
                    for doc_id, doc_info in all_docs.items():
                        if doc_id not in self.documents:  # Don't overwrite registry docs
                            self.documents[doc_id] = Document(
                                id=doc_id,
                                content="",  # We don't need to load full content into memory
                                metadata=doc_info
                            )
                    
                    logger.info(f"Loaded {len(self.documents)} unique documents from ChromaDB")
                    if self.documents:
                        logger.info(f"Document IDs: {list(self.documents.keys())[:5]}...")
                    
                    # If we found documents in ChromaDB but they weren't in the registry,
                    # save them to the registry for future runs
                    if all_docs and os.path.exists(CHROMA_DB_PATH):
                        logger.info("Updating document registry with ChromaDB documents...")
                        self._save_document_registry()
                    
                except Exception as inner_e:
                    logger.error(f"Error retrieving document IDs: {str(inner_e)}", exc_info=True)
                    logger.info("Using alternative direct access to find documents...")
                    
                    # Try a complete alternative approach - get embeddings directly from sqlite
                    try:
                        if os.path.exists(os.path.join(CHROMA_DB_PATH, "chroma.sqlite3")):
                            import sqlite3
                            conn = sqlite3.connect(os.path.join(CHROMA_DB_PATH, "chroma.sqlite3"))
                            cursor = conn.cursor()
                            
                            # Get document IDs from sqlite directly
                            cursor.execute("""
                                SELECT DISTINCT json_extract(m.metadata, '$.document_id') 
                                FROM embedding_metadata m
                                WHERE json_extract(m.metadata, '$.document_id') IS NOT NULL
                            """)
                            
                            doc_ids = [row[0] for row in cursor.fetchall()]
                            logger.info(f"Found {len(doc_ids)} document IDs directly from SQLite")
                            
                            # Create documents from these IDs
                            for doc_id in doc_ids:
                                if doc_id and doc_id not in self.documents:
                                    self.documents[doc_id] = Document(
                                        id=doc_id,
                                        content="",
                                        metadata={"recovered_from_sqlite": True}
                                    )
                            
                            conn.close()
                            logger.info(f"Recovered {len(self.documents)} documents from SQLite")
                            
                            # If we found documents in SQLite directly, save to registry
                            if doc_ids:
                                logger.info("Updating document registry with SQLite documents...")
                                self._save_document_registry()
                    except Exception as sql_e:
                        logger.error(f"SQLite direct access failed: {str(sql_e)}", exc_info=True)
                
            # Final count of documents
            logger.info(f"Final document count: {len(self.documents)}")
            if self.documents:
                logger.info(f"Final document IDs: {list(self.documents.keys())[:5]}...")
                
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
        logger.info("======= VECTOR STORE INITIALIZATION =======")
        logger.info(f"ChromaDB path: {os.path.abspath(CHROMA_DB_PATH)}")
        logger.info(f"ChromaDB directory exists: {os.path.exists(CHROMA_DB_PATH)}")
        
        # If directory exists, check its contents before initialization
        if os.path.exists(CHROMA_DB_PATH):
            try:
                contents = os.listdir(CHROMA_DB_PATH)
                logger.info(f"ChromaDB directory contents before init: {contents}")
                
                # Check if SQLite file exists and its size
                sqlite_path = os.path.join(CHROMA_DB_PATH, "chroma.sqlite3")
                if os.path.exists(sqlite_path):
                    size_mb = os.path.getsize(sqlite_path) / (1024 * 1024)
                    logger.info(f"SQLite file exists with size: {size_mb:.2f} MB")
            except Exception as dir_e:
                logger.error(f"Error checking directory contents: {str(dir_e)}")
        
        logger.info("Initializing vector store singleton...")
        instance = VectorStore.get_instance()
        logger.info("Vector store initialization complete")
        
        # Get and log debug info
        debug_info = instance.get_debug_info()
        logger.info(f"Vector store state: {debug_info}")
        
        # Verify ChromaDB state after initialization
        logger.info("Verifying ChromaDB state after initialization...")
        if os.path.exists(CHROMA_DB_PATH):
            try:
                contents = os.listdir(CHROMA_DB_PATH)
                logger.info(f"ChromaDB directory contents after init: {contents}")
                
                # Check if SQLite file exists and its size
                sqlite_path = os.path.join(CHROMA_DB_PATH, "chroma.sqlite3")
                if os.path.exists(sqlite_path):
                    size_mb = os.path.getsize(sqlite_path) / (1024 * 1024)
                    logger.info(f"SQLite file exists with size: {size_mb:.2f} MB")
                    
                    # Optional: Add direct SQLite validation
                    try:
                        import sqlite3
                        conn = sqlite3.connect(sqlite_path)
                        cursor = conn.cursor()
                        
                        # Check tables
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                        tables = cursor.fetchall()
                        logger.info(f"SQLite tables: {[t[0] for t in tables]}")
                        
                        # Check embeddings count if table exists
                        try:
                            cursor.execute("SELECT COUNT(*) FROM embeddings;")
                            embedding_count = cursor.fetchone()[0]
                            logger.info(f"Embeddings table count: {embedding_count}")
                        except sqlite3.OperationalError:
                            logger.info("No 'embeddings' table found")
                            
                        conn.close()
                    except Exception as sql_e:
                        logger.error(f"Error checking SQLite: {str(sql_e)}")
            except Exception as dir_e:
                logger.error(f"Error checking directory contents: {str(dir_e)}")
        
        return instance
    except Exception as e:
        logger.error(f"Error initializing vector store: {str(e)}")
        logger.error("Full error details:", exc_info=True)
        # In deployment mode, return None instead of raising exception
        if os.environ.get("REPL_DEPLOYMENT"):
            logger.warning("Deployment mode - continuing without vector store")
            return None
        raise