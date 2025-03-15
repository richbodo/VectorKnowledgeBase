#!/usr/bin/env python3
"""
Test script to check if we can access the Replit Object Storage
"""
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from replit.object_storage import Client
    
    logger.info("Testing Replit Object Storage access")
    
    # Try with the default bucket
    client = Client()
    
    # List objects
    logger.info("Attempting to list objects in bucket")
    objects = list(client.list())
    logger.info(f"Found {len(objects)} objects in bucket")
    
    # Print first few objects if any exist
    for obj in objects[:5]:
        logger.info(f"Object: {obj.object_name}, Size: {obj.size} bytes")
    
    # Try to write a test object
    test_content = "This is a test object for ChromaDB persistence"
    test_object_name = "test/chromadb_test.txt"
    
    logger.info(f"Creating test object: {test_object_name}")
    client.upload_from_string(test_content, test_object_name)
    
    # Verify the object was created
    if client.exists(test_object_name):
        logger.info(f"Successfully created test object: {test_object_name}")
        # Read it back
        content = client.download_as_text(test_object_name)
        logger.info(f"Retrieved content: {content}")
    else:
        logger.error(f"Failed to create test object: {test_object_name}")
    
    logger.info("Object Storage test completed successfully")
    
except Exception as e:
    logger.error(f"Error testing Object Storage: {str(e)}", exc_info=True)