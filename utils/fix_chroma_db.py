
#!/usr/bin/env python3
import os
import sys
import logging
import chromadb
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import from parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import CHROMA_DB_PATH
from models import Document

# Backup the database first
def backup_db():
    """Create a backup of the current ChromaDB directory"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"{CHROMA_DB_PATH}_backup_{timestamp}"
    
    if os.path.exists(CHROMA_DB_PATH):
        # Create simple copy of the directory
        import shutil
        try:
            shutil.copytree(CHROMA_DB_PATH, backup_dir)
            logger.info(f"Created backup at: {backup_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to create backup: {str(e)}")
            return False
    else:
        logger.warning(f"ChromaDB directory not found at {CHROMA_DB_PATH}")
        return False

def fix_document_count():
    """Scan ChromaDB and rebuild the document list"""
    try:
        # Create client with same settings as the application
        client = chromadb.PersistentClient(
            path=CHROMA_DB_PATH,
            settings=chromadb.Settings(
                anonymized_telemetry=False,
                allow_reset=False
            )
        )
        
        # Get or create the collection
        collection = client.get_or_create_collection(
            name="pdf_documents",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Get total count
        count = collection.count()
        logger.info(f"ChromaDB collection contains {count} chunks")
        
        if count == 0:
            logger.error("No data found in the database. Nothing to fix.")
            return False
            
        # Create a dictionary to store document information
        document_dict = {}
        
        # Process in batches to handle large collections
        batch_size = 1000
        unique_doc_ids = set()
        
        for offset in range(0, count, batch_size):
            logger.info(f"Processing batch at offset {offset}")
            batch = collection.get(limit=batch_size, offset=offset)
            
            # Extract document IDs from metadatas
            if batch.get('metadatas'):
                for metadata in batch['metadatas']:
                    if metadata and 'document_id' in metadata:
                        doc_id = metadata['document_id']
                        unique_doc_ids.add(doc_id)
                        
                        # Store document metadata if not already present
                        if doc_id not in document_dict:
                            document_dict[doc_id] = {
                                "filename": metadata.get("filename", "Unknown"),
                                "content_type": metadata.get("content_type", "Unknown"),
                                "size": metadata.get("size", 0),
                                "total_chunks": metadata.get("total_chunks", 0)
                            }
        
        logger.info(f"Found {len(unique_doc_ids)} unique documents in the database")
        
        # Save document information to a recovery file
        recovery_file = "recovered_documents.json"
        import json
        with open(recovery_file, 'w') as f:
            json.dump({"documents": {doc_id: info for doc_id, info in document_dict.items()}}, f, indent=2)
        
        logger.info(f"Saved document information to {recovery_file}")
        logger.info("Your documents are still in the database, but might not be loading correctly.")
        logger.info("Restart the application and check if documents appear correctly.")
        
        return True
        
    except Exception as e:
        logger.error(f"Error fixing document count: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    print("===== ChromaDB Document Recovery Tool =====")
    print(f"This tool will attempt to fix your ChromaDB document count issue")
    print(f"Database path: {os.path.abspath(CHROMA_DB_PATH)}")
    
    # Create backup first
    if backup_db():
        print("✅ Database backup created successfully")
    else:
        print("⚠️ Failed to create database backup")
        response = input("Continue without backup? (y/n): ")
        if response.lower() != 'y':
            print("Operation cancelled.")
            sys.exit(1)
    
    # Fix document count
    if fix_document_count():
        print("\n✅ Document recovery process completed")
        print("Please restart your application and check if documents appear correctly")
    else:
        print("\n❌ Failed to recover documents")
        print("Manual intervention may be required")
