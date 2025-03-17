#!/usr/bin/env python
"""
Privacy Controls Demonstration Script

This script demonstrates how to use the privacy features in your application
to protect sensitive information in logs and error handling.

Usage:
    python docs/privacy_demo.py
"""

import os
import sys
import logging
import json
import traceback

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.privacy_log_handler import PrivacyLogFilter, add_privacy_filter_to_logger

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("privacy_demo")
add_privacy_filter_to_logger(logger)

def demonstrate_privacy_features():
    """Demonstrate how the privacy features work"""
    print("\n==== Privacy Controls Demonstration ====\n")
    print("This demo shows how the privacy filter protects sensitive information.")
    print("Notice how different types of sensitive data are automatically redacted.")
    
    # Demo 1: Basic logging with sensitive data
    print("\n--- Demo 1: Basic Logging with Sensitive Data ---")
    sensitive_query = "Find information about John Doe with SSN 123-45-6789"
    email = "johndoe@example.com"
    api_key = "sk-1234567890abcdefghijklmnopqrstuvwxyz"
    
    print("Original sensitive data:")
    print(f"  Query: {sensitive_query}")
    print(f"  Email: {email}")
    print(f"  API Key: {api_key}")
    
    print("\nNow logging the same data (notice the redaction):")
    logger.info(f"Processing query: {sensitive_query}")
    logger.info(f"User contact: {email}")
    logger.info(f"Using API key: {api_key}")
    
    # Demo 2: JSON data with sensitive information
    print("\n--- Demo 2: JSON Data with Sensitive Information ---")
    sensitive_json = {
        "query": "Find information about credit card 4111-1111-1111-1111",
        "user": {
            "email": "jane@example.com",
            "apiKey": "sk-p-abcdefghijklmnopqrstuvwxyz123456789"
        },
        "options": {
            "limit": 10
        }
    }
    
    print("Original JSON data:")
    print(json.dumps(sensitive_json, indent=2))
    
    print("\nNow logging the JSON data:")
    logger.info(f"Processing request: {json.dumps(sensitive_json)}")
    
    # Demo 3: Exception handling with sensitive data
    print("\n--- Demo 3: Exception Handling with Sensitive Data ---")
    sensitive_error_data = "Password is incorrect: SuperSecretP@ssw0rd"
    
    print("Original error message:")
    print(f"  {sensitive_error_data}")
    
    print("\nNow logging an exception with this data:")
    try:
        # Simulate an error with sensitive data in the message
        raise ValueError(sensitive_error_data)
    except Exception as e:
        # Bad approach (would leak sensitive data)
        print("Without privacy protection, you might log the raw error:")
        print(f"  ERROR: {str(e)}")
        
        # Good approach (with privacy protection)
        print("\nWith privacy protection, we sanitize before logging:")
        # Get the traceback as a string
        tb_str = traceback.format_exc()
        
        # Apply the privacy filter to the traceback string
        privacy_filter = PrivacyLogFilter()
        # Manually apply the filter to sanitize the error message
        sanitized_error = str(e)
        for pattern_name, pattern in privacy_filter.patterns.items():
            if 'password' in pattern_name.lower() or pattern_name == 'api_key':
                sanitized_error = pattern.sub('[SENSITIVE DATA REDACTED]', sanitized_error)
        
        logger.error(f"Error processing request: {sanitized_error}")
    
    # Demo 4: Privacy-aware function context
    print("\n--- Demo 4: Privacy-Aware Function Context ---")
    
    def privacy_context(func):
        """Decorator to create a privacy-aware context for function execution"""
        def wrapper(*args, **kwargs):
            logger.info("Entering privacy-protected context")
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Sanitize the error message
                original_error = str(e)
                sanitized_error = "Error in operation"
                logger.error(f"Error in privacy context: {sanitized_error}")
                # Re-raise with sanitized message
                raise type(e)(sanitized_error) from None
            finally:
                logger.info("Exiting privacy-protected context")
        return wrapper
    
    @privacy_context
    def process_sensitive_data(query, api_key):
        """Example function that processes sensitive data"""
        logger.info(f"Processing with query: {query}")
        if "invalid" in query.lower():
            raise ValueError(f"Invalid query contains sensitive data: {query}")
        return {"result": "Processed successfully"}
    
    print("Calling function with sensitive data:")
    try:
        result = process_sensitive_data("Find information about John", "sk-1234")
        print(f"  Result: {result}")
    except Exception as e:
        print(f"  Caught error: {e}")
    
    print("\nNow calling function with data that will cause an error:")
    try:
        result = process_sensitive_data("This is an invalid query with SSN 123-45-6789", "sk-1234")
        print(f"  Result: {result}")
    except Exception as e:
        print(f"  Caught error: {e} (notice sensitive data is not included)")
    
    # Summary
    print("\n--- Summary ---")
    print("The privacy filter provides protection for:")
    print("1. Direct logging of sensitive data")
    print("2. JSON and structured data logging")
    print("3. Exception messages and stack traces")
    print("4. Function execution contexts")
    print("\nRemember to use add_privacy_filter_to_logger() for all loggers in your application!")

if __name__ == "__main__":
    demonstrate_privacy_features()