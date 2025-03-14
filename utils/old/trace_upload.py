
#!/usr/bin/env python3
import sys
import os
import logging
import chromadb
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import CHROMA_DB_PATH
from services.vector_store import CustomEmbeddingFunction
from services.embedding_service import EmbeddingService
from models import Document

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])

logger = logging.getLogger("upload-tracer")

def trace_document_upload():
    """Trace the document upload process step by step"""
    print("\n===== ChromaDB Upload Tracer =====")
    print(f"ChromaDB path: {os.path.abspath(CHROMA_DB_PATH)}")
    
    # 1. Initialize ChromaDB client directly
    try:
        print("\n[Step 1] Initializing ChromaDB client...")
        client = chromadb.PersistentClient(
            path=CHROMA_DB_PATH,
            settings=chromadb.Settings(
                anonymized_telemetry=False,
                allow_reset=False
            )
        )
        print("✅ ChromaDB client initialized successfully")
        
        # Check for collections
        collections = client.list_collections()
        print(f"Found {len(collections)} collections: {[c.name for c in collections]}")
    except Exception as e:
        print(f"❌ Failed to initialize ChromaDB client: {str(e)}")
        return
    
    # 2. Setup embedding function
    try:
        print("\n[Step 2] Setting up embedding service and function...")
        embedding_service = EmbeddingService()
        embedding_function = CustomEmbeddingFunction(embedding_service)
        print("✅ Embedding function created successfully")
    except Exception as e:
        print(f"❌ Failed to create embedding function: {str(e)}")
        return
    
    # 3. Get or create collection with explicit embedding function
    try:
        print("\n[Step 3] Creating collection with embedding function...")
        collection = client.get_or_create_collection(
            name="pdf_documents",
            embedding_function=embedding_function,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"✅ Collection created/accessed successfully")
        print(f"Collection document count: {collection.count()}")
        
        # Verify embedding function is attached
        print(f"Embedding function attached: {collection._embedding_function is not None}")
    except Exception as e:
        print(f"❌ Failed to create/access collection: {str(e)}")
        return
    
    # 4. Create a test document
    try:
        print("\n[Step 4] Creating test document...")
        test_doc_id = f"test_doc_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        test_doc = Document(
            id=test_doc_id,
            content="This is a test document created by the trace_upload.py script.",
            metadata={
                "filename": "test_document.txt",
                "content_type": "text/plain",
                "size": 100,
                "source": "trace_upload_script"
            }
        )
        print(f"✅ Test document created with ID: {test_doc_id}")
    except Exception as e:
        print(f"❌ Failed to create test document: {str(e)}")
        return
    
    # 5. Add document to collection
    try:
        print("\n[Step 5] Adding document to collection...")
        # Split into chunks like vector_store.py does
        chunks = [test_doc.content]  # Single chunk for simplicity
        chunk_ids = [f"{test_doc_id}_chunk_0"]
        
        # Add to collection with all the same fields as in vector_store.py
        collection.add(
            ids=chunk_ids,
            documents=chunks,
            metadatas=[{
                "document_id": test_doc_id,
                "chunk_index": 0,
                "total_chunks": 1,
                "filename": test_doc.metadata.get("filename", "Unknown"),
                "content_type": test_doc.metadata.get("content_type", "Unknown"),
                "size": test_doc.metadata.get("size", 0)
            }]
        )
        print("✅ Document added to collection")
        
        # Verify document count
        count_after = collection.count()
        print(f"Collection count after adding: {count_after}")
        
        # Try to retrieve the document
        results = collection.get(
            where={"document_id": test_doc_id},
            limit=1
        )
        
        if results and results.get("ids") and len(results["ids"]) > 0:
            print(f"✅ Successfully retrieved document from collection")
            print(f"Document metadata: {json.dumps(results['metadatas'][0], indent=2) if results['metadatas'] else 'None'}")
        else:
            print("❌ Failed to retrieve document after adding")
        
    except Exception as e:
        print(f"❌ Failed to add document to collection: {str(e)}")
        print(f"Exception type: {type(e)}")
        import traceback
        print(traceback.format_exc())
        return
    
    print("\n===== Tracing Complete =====")
    
if __name__ == "__main__":
    trace_document_upload()
