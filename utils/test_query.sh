#!/bin/bash

# Colors for better output readability
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Testing Document Query API${NC}"
echo "========================================"

# Get query from command line argument
QUERY="$1"

if [ -z "$QUERY" ]; then
  echo -e "${RED}Error: No query specified${NC}"
  echo "Usage:"
  echo "First, set your API key:"
  echo "  export VKB_API_KEY=your_api_key"
  echo "Then run the script:"
  echo "  ./test_query.sh \"your search query\""
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

echo "Searching for: \"$QUERY\""
echo ""

# Make the API request to the local server
echo "Making request to http://localhost:8080/api/query..."
curl -v -X POST \
     -H "Content-Type: application/json" \
     -H "Accept: application/json" \
     -H "X-API-KEY: $VKB_API_KEY" \
     -d "{\"query\": \"$QUERY\"}" \
     http://localhost:8080/api/query

echo ""
echo "========================================"
echo -e "${GREEN}Test complete${NC}"