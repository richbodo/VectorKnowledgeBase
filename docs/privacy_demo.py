#!/usr/bin/env python
"""
Privacy Controls Demonstration Script

This script demonstrates how to use the privacy features in your application
to protect sensitive information in logs and error handling.

Usage:
    python docs/privacy_demo.py
"""

import sys
import os
import logging
import json

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import privacy controls
from utils.privacy_log_handler import add_privacy_filter_to_logger

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("privacy_demo")

# Apply privacy filter to the logger
add_privacy_filter_to_logger(logger)

def demonstrate_privacy_features():
    """Demonstrate how the privacy features work"""
    print("\n==== Privacy Controls Demonstration ====\n")
    
    # Example 1: Basic query protection
    print("\n=== Example 1: Basic Query Protection ===")
    sensitive_query = "Find information about John Doe's medical history"
    
    print("Original query: " + sensitive_query)
    print("Now logging the same query (it should be redacted in logs)...")
    logger.info(f"Processing query: {sensitive_query}")
    
    # Example 2: API key protection
    print("\n=== Example 2: API Key Protection ===")
    api_key = "sk-1234567890abcdefghijklmnopqrstuvwxyz"
    
    print("API Key (for demonstration only): " + api_key)
    print("Now logging a message with the API key (it should be redacted)...")
    logger.info(f"Using API key: {api_key}")
    
    # Example 3: JSON data protection
    print("\n=== Example 3: JSON Data Protection ===")
    json_data = {"query": "Find John's personal information", "limit": 10}
    
    print("Original JSON data: " + json.dumps(json_data))
    print("Now logging the JSON data (sensitive parts should be redacted)...")
    logger.info(f"Query payload: {json.dumps(json_data)}")
    
    # Example 4: Error handling with privacy
    print("\n=== Example 4: Error Handling with Privacy ===")
    sensitive_data = "My password is SuperSecret123"
    
    print("Original sensitive data: " + sensitive_data)
    print("Now raising and logging an error with this data (it should be redacted)...")
    try:
        raise ValueError(f"Error processing data: {sensitive_data}")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
    
    # Example 5: Email protection
    print("\n=== Example 5: Email Protection ===")
    email = "john.doe@example.com"
    
    print("Original email: " + email)
    print("Now logging the email (it should be redacted)...")
    logger.info(f"User email: {email}")
    
    print("\n==== Demonstration Complete ====")
    print("Check your application logs to verify that sensitive information was redacted.")
    print("The log messages above should show '[QUERY CONTENT REDACTED]', '[API KEY REDACTED]',")
    print("'[EMAIL REDACTED]', etc. instead of the actual sensitive values.")

if __name__ == "__main__":
    demonstrate_privacy_features()