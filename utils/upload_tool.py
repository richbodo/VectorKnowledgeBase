#!/usr/bin/env python3
import os
import sys
import requests
from pathlib import Path

def upload_pdf(file_path):
    """Upload a PDF file to the API"""
    # Get API key from environment
    api_key = os.environ.get('VKB_API_KEY')
    if not api_key:
        print("Error: VKB_API_KEY environment variable is not set")
        print("Please set it using: export VKB_API_KEY=your_api_key")
        print("Note: This is different from the API key stored in Replit secrets")
        return False

    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found")
        return False

    try:
        # Open and prepare the file
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'application/pdf')}
            headers = {
                'Accept': 'application/json',
                'X-API-KEY': api_key
            }

            # Make the request to the API
            print(f"\nSending POST request to upload {file_path}...")
            response = requests.post(
                'http://localhost:8080/api/upload',
                files=files,
                headers=headers
            )

            # Handle the response
            if response.status_code == 200:
                result = response.json()
                print("\nUpload successful!")
                print(f"Document ID: {result['document_id']}")
                print(f"File: {result['metadata']['filename']}")
                print(f"Size: {result['metadata']['size']} bytes")
                return True
            else:
                print(f"\nError: Upload failed with status code {response.status_code}")
                print(f"Response: {response.text}")
                return False

    except Exception as e:
        print(f"\nError uploading file: {str(e)}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python upload_tool.py <pdf_file>")
        print("Before running, set your API key:")
        print("  export VKB_API_KEY=your_api_key")
        print("Then run the script:")
        print("  python upload_tool.py document.pdf")
        sys.exit(1)

    file_path = sys.argv[1]
    success = upload_pdf(file_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()