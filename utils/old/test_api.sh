#!/bin/bash

# Colors for better output readability
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Testing PDF Upload API${NC}"
echo "========================================"

# Get query from command line argument
TEST_FILE="$1"

if [ -z "$TEST_FILE" ]; then
  echo -e "${RED}Error: No test file specified${NC}"
  echo "Usage:"
  echo "First, set your API key:"
  echo "  export VKB_API_KEY=your_api_key"
  echo "Then run the script:"
  echo "  ./test_api.sh <path_to_pdf_file>"
  exit 1
fi

if [ ! -f "$TEST_FILE" ]; then
  echo -e "${RED}Error: File '$TEST_FILE' not found${NC}"
  exit 1
fi

# Get API key from environment
VKB_API_KEY="${VKB_API_KEY:-}"
if [ -z "$VKB_API_KEY" ]; then
  echo -e "${RED}Error: VKB_API_KEY environment variable is not set${NC}"
  echo "Please set it using: export VKB_API_KEY=your_api_key"
  echo "Note: This is different from the API key stored in Replit secrets"
  exit 1
fi

echo "Testing file upload with: $TEST_FILE"
echo ""

# Make the API request to the local server
echo "Making request to http://localhost:8080/api/upload..."
curl -v -X POST -F "file=@$TEST_FILE" \
     -H "Accept: application/json" \
     -H "X-API-KEY: $VKB_API_KEY" \
     http://localhost:8080/api/upload

echo ""
echo "========================================"
echo -e "${GREEN}Test complete${NC}"