#!/usr/bin/env python3
"""
Simplified test script to check basic Replit Object Storage functionality
"""
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from replit.object_storage import Client

    logger.info("Testing Replit Object Storage basic functionality")
    
    # Initialize the Object Storage client
    client = Client()
    
    # Define a test file name
    db_filename = "test_chromadb.txt"
    
    # Create a test file locally
    with open(db_filename, "wb") as test_file:
        test_file.write(b"This is a test for ChromaDB persistence using Replit Object Storage")
    
    logger.info(f"Created local test file: {db_filename}")
    
    # Function to upload the database file to Object Storage
    def upload_db():
        client.upload_from_filename(db_filename, db_filename)
        logger.info(f"Uploaded file to Object Storage: {db_filename}")
    
    # Function to download the database file from Object Storage
    def download_db():
        if client.exists(db_filename):
            download_filename = f"downloaded_{db_filename}"
            client.download_to_filename(db_filename, download_filename)
            logger.info(f"Downloaded file from Object Storage to: {download_filename}")
            return True
        else:
            logger.error(f"File not found in Object Storage: {db_filename}")
            return False
    
    # Test upload
    upload_db()
    
    # List objects after upload
    objects = list(client.list())
    logger.info(f"Found {len(objects)} objects in bucket after upload")
    
    # Test download
    download_success = download_db()
    
    # Verify download
    if download_success and os.path.exists(f"downloaded_{db_filename}"):
        with open(f"downloaded_{db_filename}", "rb") as f:
            content = f.read()
        logger.info(f"Downloaded file content: {content.decode('utf-8')}")
    
    logger.info("Object Storage test completed successfully")
    
except Exception as e:
    logger.error(f"Error testing Object Storage: {str(e)}", exc_info=True)