#!/usr/bin/env python3
"""
Script to check available methods in Replit Object Storage client
"""
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from replit.object_storage import Client
    
    client = Client()
    
    # Get all methods and attributes
    methods = [method for method in dir(client) if not method.startswith('_')]
    
    logger.info("Available methods in Client:")
    for method in methods:
        logger.info(f"- {method}")
    
except Exception as e:
    logger.error(f"Error checking Object Storage API: {str(e)}", exc_info=True)