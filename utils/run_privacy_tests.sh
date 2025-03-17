#!/bin/bash

# Run Privacy Tests Script
# This script runs the privacy tests and generates a report

echo "===================================================="
echo "Running Privacy Controls Test Suite"
echo "===================================================="

# Set API key for testing
export VKB_API_KEY="test_api_key_for_privacy_validation"

# Create test report directory if it doesn't exist
REPORT_DIR="./test_reports"
mkdir -p "$REPORT_DIR"

# Generate timestamp for report file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="$REPORT_DIR/privacy_test_report_$TIMESTAMP.txt"

echo "Running tests..."
echo "Results will be saved to $REPORT_FILE"

# Run the tests and capture output
python utils/test_privacy.py | tee "$REPORT_FILE"

# Append log snippets to the report
echo -e "\n\n===================================================" >> "$REPORT_FILE"
echo "Recent Log Entries (for verification)" >> "$REPORT_FILE"
echo "===================================================" >> "$REPORT_FILE"
tail -n 100 app.log >> "$REPORT_FILE"

echo -e "\nTest completed. Report saved to $REPORT_FILE"
echo "===================================================="