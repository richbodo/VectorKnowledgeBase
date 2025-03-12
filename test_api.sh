#!/bin/bash

# Colors for better output readability
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Testing PDF Upload API${NC}"
echo "========================================"

# Test the upload endpoint with a PDF file
# Change the path to your test PDF file
TEST_FILE="$1"

if [ -z "$TEST_FILE" ]; then
  echo -e "${RED}Error: No test file specified${NC}"
  echo "Usage: ./test_api.sh <path_to_pdf_file>"
  exit 1
fi

if [ ! -f "$TEST_FILE" ]; then
  echo -e "${RED}Error: File '$TEST_FILE' not found${NC}"
  exit 1
fi

# Get API key from environment
API_KEY="${API_KEY:-}"
if [ -z "$API_KEY" ]; then
  echo -e "${RED}Error: API_KEY environment variable is not set${NC}"
  exit 1
fi

echo "Testing file upload with: $TEST_FILE"
echo ""

# Make the API request to the local server
echo "Making request to http://localhost:8080/api/upload..."
curl -v -X POST -F "file=@$TEST_FILE" \
     -H "Accept: application/json" \
     -H "X-API-KEY: $API_KEY" \
     http://localhost:8080/api/upload

echo ""
echo "========================================"
echo -e "${GREEN}Test complete${NC}"