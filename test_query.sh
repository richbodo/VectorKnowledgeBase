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
  echo "Usage: ./test_query.sh \"your search query\""
  exit 1
fi

# Get API key from environment
API_KEY="${API_KEY:-}"
if [ -z "$API_KEY" ]; then
  echo -e "${RED}Error: API_KEY environment variable is not set${NC}"
  exit 1
fi

echo "Searching for: \"$QUERY\""
echo ""

# Make the API request to the local server
echo "Making request to http://localhost:8080/api/query..."
curl -v -X POST \
     -H "Content-Type: application/json" \
     -H "Accept: application/json" \
     -H "X-API-KEY: $API_KEY" \
     -d "{\"query\": \"$QUERY\"}" \
     http://localhost:8080/api/query

echo ""
echo "========================================"
echo -e "${GREEN}Test complete${NC}"