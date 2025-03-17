<<<<<<< HEAD
#!/usr/bin/env python
=======
>>>>>>> 446e53914c5d9f82f391a8f0f259dd39892a7531
"""
Test script for the privacy log filter functionality.
This demonstrates how the filter protects sensitive information in logs.
"""
<<<<<<< HEAD

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
=======
import logging
import sys
from utils.privacy_log_handler import PrivacyLogFilter

# Configure logging with the privacy filter
logger = logging.getLogger("privacy_test")
logger.setLevel(logging.DEBUG)

# Clear any existing handlers
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Create a console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))

# Create our privacy filter
privacy_filter = PrivacyLogFilter()
console_handler.addFilter(privacy_filter)
logger.addHandler(console_handler)

# Test function to show unfiltered vs filtered output
def test_privacy_filter():
    print("\n=== PRIVACY FILTER TEST ===\n")
    
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

if __name__ == "__main__":
    test_privacy_filter()
    print("\nTest complete. The privacy filter is working if sensitive information is redacted above.")
>>>>>>> 446e53914c5d9f82f391a8f0f259dd39892a7531
