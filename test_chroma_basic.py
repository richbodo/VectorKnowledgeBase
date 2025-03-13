#!/usr/bin/env python3
import chromadb
import uuid
import logging
import sys
import os

# Set up basic logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)
logger = logging.getLogger("chroma-test")

# Use the same ChromaDB directory as the main application
CHROMA_PERSIST_DIR = "chroma_db"

def test_basic_chroma_operations():
    """Basic test for ChromaDB - insert and retrieve a simple document"""
    
    logger.info(f"Testing with ChromaDB version: {chromadb.__version__}")
    logger.info(f"Database directory: {CHROMA_PERSIST_DIR}")
    logger.info(f"Directory exists: {os.path.exists(CHROMA_PERSIST_DIR)}")
    logger.info(f"ChromaDB version: {chromadb.__version__}")
    
    # Create client with the same configuration as the application
    client = chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIR,
        settings=chromadb.Settings(
            anonymized_telemetry=False,
            allow_reset=True,
            persist_directory=CHROMA_PERSIST_DIR
        )
    )

    # Access the collection (create if doesn't exist)
    collection = client.get_or_create_collection(
        name="pdf_documents",
        metadata={"description": "Simple test collection"}
    )
    
    # Generate a test document with a unique ID
    test_doc_id = f"test-doc-{uuid.uuid4()}"
    test_content = "This is a simple test document for ChromaDB verification."
    
    # Embed the document (no actual embedding model needed for this test)
    logger.info(f"Adding document with ID: {test_doc_id}")
    collection.add(
        ids=[test_doc_id],
        documents=[test_content],
        metadatas=[{"test_id": test_doc_id, "source": "test_script"}]
    )
    
    # Retrieve and verify the document
    logger.info("Retrieving document...")
    result = collection.get(ids=[test_doc_id])
    
    if result and result["ids"]:
        logger.info("✅ Document successfully retrieved!")
        logger.info(f"Document ID: {result['ids'][0]}")
        logger.info(f"Content: {result['documents'][0]}")
        logger.info(f"Metadata: {result['metadatas'][0]}")
    else:
        logger.error("❌ Failed to retrieve document!")
    
    # Test querying (not using embeddings but just to test the API)
    logger.info("\nTesting get with where clause...")
    where_result = collection.get(where={"test_id": test_doc_id})
    
    if where_result and where_result["ids"]:
        logger.info("✅ Query with 'where' successful!")
        logger.info(f"Found {len(where_result['ids'])} documents")
    else:
        logger.error("❌ Query with 'where' failed!")
    
    # Check overall collection count
    count = collection.count()
    logger.info(f"\nTotal documents in collection: {count}")
    
    # Clean up - delete our test document
    #logger.info(f"Cleaning up - deleting test document {test_doc_id}")
    #collection.delete(ids=[test_doc_id])
    
    # Verify deletion
    #post_delete_count = collection.count()
    #logger.info(f"Collection count after deletion: {post_delete_count}")
    #logger.info(f"Document successfully deleted: {count - post_delete_count == 1}")
    
    # Add this to your test script
    collections = client.list_collections()
    logger.info(f"Available collections: {collections}")
    for collection_name in collections:
        coll = client.get_collection(collection_name)
        count = coll.count()
        logger.info(f"Collection '{collection_name}' has {count} documents")
    
    return True

if __name__ == "__main__":
    logger.info("Starting basic ChromaDB test")
    try:
        success = test_basic_chroma_operations()
        if success:
            logger.info("✅ All tests completed successfully!")
        else:
            logger.error("❌ Test failed!")
    except Exception as e:
        logger.error(f"❌ Error during test: {str(e)}")
        logger.exception("Full exception details:")
    logger.info("Test complete")
