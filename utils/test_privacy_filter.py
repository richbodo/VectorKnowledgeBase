#!/usr/bin/env python
"""
Test script for the privacy log filter functionality.
This demonstrates how the filter protects sensitive information in logs.
"""

import logging
import sys
import os
import json

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.privacy_log_handler import PrivacyLogFilter, add_privacy_filter_to_logger

def test_privacy_filter():
    """Test the privacy log filter with various sensitive data formats"""
    # Set up a test logger
    logger = logging.getLogger("privacy_test")
    logger.setLevel(logging.DEBUG)
    
    # Add a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add the privacy filter
    add_privacy_filter_to_logger(logger)
    
    print("\n==== Privacy Filter Test ====\n")
    print("The following logs should have sensitive information redacted:")
    
    # Test with various formats of sensitive information
    sensitive_data = "This is very sensitive private information"
    
    # Format 1: Simple string with sensitive data
    logger.info(f"User query: {sensitive_data}")
    
    # Format 2: JSON format
    query_json = {"query": sensitive_data, "metadata": {"user": "test_user"}}
    logger.info(f"Processing request: {json.dumps(query_json)}")
    
    # Format 3: URL parameter format
    logger.info(f"Received request: /api/query?q={sensitive_data}")
    
    # Format 4: Dictionary format
    logger.info(f"Query params: {{'query': '{sensitive_data}', 'limit': 10}}")
    
    # Format 5: API Key format
    api_key = "sk-1234567890abcdefghijklmnopqrstuvwxyz"
    logger.info(f"Using API key: {api_key}")
    
    # Format 6: Email address
    email = "user@example.com"
    logger.info(f"User email: {email}")
    
    # Format 7: Query in exception
    try:
        # Simulate an exception with sensitive data
        raise ValueError(f"Error processing query: {sensitive_data}")
    except Exception as e:
        logger.error(f"Exception occurred: {str(e)}")
    
    print("\n==== Test Completed ====")
    print("Check the output above. All sensitive data should be redacted.")
    print("Formats tested:")
    print("1. Simple string with query data")
    print("2. JSON format")
    print("3. URL parameter format")
    print("4. Dictionary format")
    print("5. API key format")
    print("6. Email address")
    print("7. Exception message format")
    
if __name__ == "__main__":
    test_privacy_filter()