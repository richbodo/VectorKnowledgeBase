"""
Test script for the privacy log filter functionality.
This demonstrates how the filter protects sensitive information in logs.
"""
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