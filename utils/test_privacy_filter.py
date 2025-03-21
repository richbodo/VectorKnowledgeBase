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
    
    # Clear any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add a console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # Add the privacy filter using the utility function
    add_privacy_filter_to_logger(logger)
    
    # Add the handler after the filter
    logger.addHandler(console_handler)
    
    print("\n==== Privacy Filter Test ====\n")
    print("The following logs should have sensitive information redacted:")
    
    # Test with a comprehensive set of sensitive data patterns
    sensitive_data = [
        # Email addresses
        "Please contact john.doe@example.com for more information",
        
        # API keys
        'api_key: "sk-1234567890abcdefghijklmnopqrstuvwxyz1234"',
        'OPENAI_API_KEY="sk-openai-8371jdlfjsdfjkasdfjkl3487432894723"',
        
        # Bearer tokens
        'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ',
        
        # Query content
        'query: "What are the key benefits of machine learning in healthcare?"',
        '{"query": "How do I implement OAuth in Flask?"}',
        
        # PDF content
        '%PDF-1.3 12345 0 obj << /Type /Page endobj trailer << /Root',
        
        # Newer style OpenAI keys
        'API key: sk-p-123456-abcdef-ghijklmnopqrstuvwxyz123456789',
        
        # Environment variable assignments
        'OPENAI_API_KEY=sk-8371jdlfjsdfjkasdfjkl3487432894723',
        
        # Header-based API keys
        'X-API-Key: 1234567890abcdefghijklmnopqrstuvwxyz1234'
    ]
    
    print("Original sensitive data that should be filtered:")
    for i, data in enumerate(sensitive_data, 1):
        print(f"{i}. {data}")
    
    print("\nFiltered log output:")
    for i, data in enumerate(sensitive_data, 1):
        logger.info(f"Example {i}: {data}")
    
    # Test string formatting
    logger.info("User %s sent email to %s", "admin", "user@example.com")
    logger.info("API request with key: %s", "sk-1234567890abcdefghijklmnopqrstuvwxyz1234")
    
    # Test dict-based formatting
    logger.info("Query from %(user)s: %(query)s", {
        "user": "john@example.com",
        "query": "How to implement OAuth securely?"
    })
    
    # Format 2: JSON format
    query_json = {"query": "This is very sensitive private information", "metadata": {"user": "test_user"}}
    logger.info(f"Processing request: {json.dumps(query_json)}")
    
    # Format 3: URL parameter format
    logger.info(f"Received request: /api/query?q=This is very sensitive private information")
    
    # Format 7: Query in exception
    try:
        # Simulate an exception with sensitive data
        raise ValueError(f"Error processing query: This is very sensitive private information")
    except Exception as e:
        logger.error(f"Exception occurred: {str(e)}")
    
    print("\n==== Test Completed ====")
    print("Check the output above. All sensitive data should be redacted.")
    print("The privacy filter is working if sensitive information is redacted above.")

if __name__ == "__main__":
    test_privacy_filter()
