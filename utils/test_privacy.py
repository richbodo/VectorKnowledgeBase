#!/usr/bin/env python
"""
Privacy Controls Test Script

This script tests the privacy controls implemented in the system
by making API requests with sensitive query content and verifying
that the content is properly redacted in logs.

Usage:
    python utils/test_privacy.py

This will:
1. Make a request to the /api/query endpoint with sample sensitive data
2. Intentionally trigger an error to test error handling privacy
3. Display a summary of privacy check results
"""

import os
import sys
import json
import logging
import requests
import time
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("privacy_test")

# Test configuration
TEST_HOST = "http://localhost:8080"  # Change as needed for your local setup
API_ENDPOINT = "/api/query"
TEST_QUERIES = [
    "This is a test query with sensitive information like SSN 123-45-6789",
    "Please find information about John Doe's medical history",
    "Here is my password: SuperSecret123!",
    "My credit card number is 4111 1111 1111 1111"
]

# Error-inducing query designed to potentially leak content in errors
ERROR_QUERY = "A" * 10000  # Very long query that might trigger an error


def get_api_key():
    """Get API key from environment variable"""
    api_key = os.environ.get("VKB_API_KEY")
    if not api_key:
        # For testing, provide a default if not set
        logger.warning("VKB_API_KEY not found in environment. Using default test key.")
        api_key = "test_api_key_for_privacy_validation"
    return api_key


def check_logs_for_leakage(query, log_file="app.log"):
    """
    Check logs for any signs of query content leakage
    Returns True if privacy control working (no leakage), False otherwise
    """
    try:
        leaked = False
        # Check last 50 lines of log file for the query
        with open(log_file, "r") as f:
            # Read last 50 lines
            lines = f.readlines()[-50:]
            for line in lines:
                if query in line and "[QUERY CONTENT REDACTED]" not in line:
                    leaked = True
                    logger.error(f"Privacy leak detected in logs: {line.strip()}")
                    return False
        return True
    except Exception as e:
        logger.error(f"Error checking logs: {str(e)}")
        return False


def make_test_request(query, api_key):
    """Make a test request to the API with the given query"""
    url = f"{TEST_HOST}{API_ENDPOINT}"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    data = {"query": query}
    
    try:
        logger.info(f"Making request with privacy-sensitive content (length: {len(query)})")
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        # Get status and basic info without logging content
        status_code = response.status_code
        logger.info(f"Response status code: {status_code}")
        
        # Wait a moment for logs to be written
        time.sleep(0.5)
        
        # Check logs for leakage
        privacy_check = check_logs_for_leakage(query)
        if privacy_check:
            logger.info("✅ Privacy check passed: No query content leaked in logs")
        else:
            logger.error("❌ Privacy check failed: Query content found in logs")
            
        return {
            "status_code": status_code,
            "privacy_check": privacy_check
        }
    except Exception as e:
        logger.error(f"Error making request: {str(e)}")
        return {
            "status_code": 0,
            "privacy_check": False,
            "error": str(e)
        }


def run_privacy_tests():
    """Run a series of privacy tests"""
    api_key = get_api_key()
    results = []
    
    logger.info("=" * 60)
    logger.info("Starting Privacy Controls Test")
    logger.info("=" * 60)
    
    # Test with normal queries
    for i, query in enumerate(TEST_QUERIES):
        logger.info(f"\nTest #{i+1}: Regular query with sensitive data")
        result = make_test_request(query, api_key)
        results.append({
            "test_type": "regular_query",
            "query_length": len(query),
            "result": result
        })
    
    # Test with error-inducing query
    logger.info("\nTest #5: Error-inducing query")
    result = make_test_request(ERROR_QUERY, api_key)
    results.append({
        "test_type": "error_query",
        "query_length": len(ERROR_QUERY),
        "result": result
    })
    
    # Display summary
    logger.info("\n" + "=" * 60)
    logger.info("Privacy Test Results Summary")
    logger.info("=" * 60)
    
    passed = sum(1 for r in results if r["result"]["privacy_check"])
    total = len(results)
    
    logger.info(f"Tests passed: {passed}/{total}")
    for i, result in enumerate(results):
        test_type = result["test_type"]
        privacy_check = result["result"]["privacy_check"]
        status = "✅ PASSED" if privacy_check else "❌ FAILED"
        logger.info(f"Test #{i+1} ({test_type}): {status}")
    
    logger.info("\nPrivacy implementation effectiveness: {:.1f}%".format(100 * passed / total))
    logger.info("=" * 60)
    
    return results


if __name__ == "__main__":
    run_privacy_tests()