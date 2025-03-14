
#!/usr/bin/env python3
import chromadb
import logging
import sys
import os
import json
from datetime import datetime

# Adjust the path to import from project directories
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.embedding_service import EmbeddingService
from services.vector_store import CustomEmbeddingFunction
from config import CHROMA_DB_PATH
from models import Document

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)
logger = logging.getLogger("reset-verify-chroma")

def reset_and_verify_collection():
    """Reset the ChromaDB collection and verify it works properly"""
    print("\n===== ChromaDB Reset and Verification Tool =====")
    
    # 1. Create backup first
    backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"{CHROMA_DB_PATH}_backup_{backup_timestamp}"
    
    if os.path.exists(CHROMA_DB_PATH):
        try:
            import shutil
            shutil.copytree(CHROMA_DB_PATH, backup_dir)
            print(f"✅ Created backup at: {backup_dir}")
        except Exception as e:
            print(f"⚠️ Failed to create backup: {str(e)}")
    
    try:
        # 2. Initialize ChromaDB client
        logger.info("Initializing ChromaDB client...")
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        print("✅ ChromaDB client initialized")

        # 3. Initialize embedding service and embedding function
        logger.info("Initializing embedding service...")
        embedding_service = EmbeddingService()
        embedding_func = CustomEmbeddingFunction(embedding_service)
        print("✅ Embedding service and function initialized")

        # 4. Delete existing collection if it exists
        existing_collections = client.list_collections()
        logger.info(f"Existing collections before deletion: {[c.name for c in existing_collections]}")
        collection_exists = False
        
        for collection in existing_collections:
            if collection.name == "pdf_documents":
                collection_exists = True
                break
                
        if collection_exists:
            logger.info("Deleting existing 'pdf_documents' collection...")
            client.delete_collection("pdf_documents")
            logger.info("Deleted existing 'pdf_documents' collection.")
            print("✅ Deleted existing collection")
        else:
            logger.info("'pdf_documents' collection does not exist. No deletion needed.")
            print("ℹ️ No existing collection to delete")

        # 5. Recreate collection explicitly with embedding function
        logger.info("Recreating 'pdf_documents' collection with correct embedding function...")
        collection = client.create_collection(
            name="pdf_documents",
            embedding_function=embedding_func,
            metadata={"hnsw:space": "cosine"}
        )
        print("✅ Created fresh collection with embedding function")
        
        # 6. Verify collection creation
        collections_after_creation = client.list_collections()
        logger.info(f"Collections after creation: {[c.name for c in collections_after_creation]}")
        
        # 7. Test adding a document
        test_doc_id = f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        test_content = "This is a test document to verify ChromaDB is working correctly."
        
        print("\n[Testing document addition]")
        collection.add(
            ids=[test_doc_id],
            documents=[test_content],
            metadatas=[{
                "document_id": test_doc_id,
                "filename": "test.txt",
                "content_type": "text/plain"
            }]
        )
        print("✅ Added test document")
        
        # 8. Verify document was added
        count = collection.count()
        print(f"Collection count: {count}")
        
        if count > 0:
            # Try to retrieve the document
            results = collection.get(ids=[test_doc_id])
            if results and results.get("ids") and len(results["ids"]) > 0:
                print("✅ Successfully retrieved test document")
            else:
                print("❌ Failed to retrieve test document")
        else:
            print("❌ Document count is still 0 after adding test document")
        
        # 9. Test vector search
        if count > 0:
            results = collection.query(
                query_texts=["test document verify"],
                n_results=1
            )
            
            if results and results.get("ids") and len(results["ids"][0]) > 0:
                print("✅ Vector search successful!")
                print(f"Search result ID: {results['ids'][0][0]}")
                print(f"Search result distance: {results['distances'][0][0]}")
            else:
                print("❌ Vector search failed")
        
        print("\n===== Reset and Verification Complete =====")
        print(f"ChromaDB is now reset and verified with a test document.")
        print(f"You can now upload your actual documents through the API.")
        
    except Exception as e:
        logger.error(f"Error during reset/verification: {str(e)}", exc_info=True)
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    reset_and_verify_collection()
