#!/bin/bash

# Colors for better output readability
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if test_files directory exists
if [ ! -d "test_files" ]; then
    echo -e "${RED}Error: test_files directory not found${NC}"
    exit 1
fi

# Get the first PDF file
pdf_files=(test_files/*.pdf)
if [ ! -e "${pdf_files[0]}" ]; then
    echo -e "${RED}Error: No PDF files found in test_files directory${NC}"
    exit 1
fi

# Use the first PDF file found
TEST_FILE="${pdf_files[0]}"
echo -e "${GREEN}Using test file: ${TEST_FILE}${NC}"

# If VKB_API_KEY is not set, ask for it
if [ -z "$VKB_API_KEY" ]; then
    echo -n "Please enter your API key: "
    read -r user_api_key
    export VKB_API_KEY="$user_api_key"
fi

# Run the upload tool
echo -e "\n${GREEN}Running upload tool...${NC}"
python upload_tool.py "$TEST_FILE"
RESULT=$?

# Clean up the API key from environment
unset VKB_API_KEY

# Exit with the same status as the upload tool
exit $RESULT