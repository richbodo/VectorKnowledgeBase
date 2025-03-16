#!/usr/bin/env python3
"""
Simple script to delete a single file from the history folder as a sanity check.
"""

import os
import sys
import logging
from typing import Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path for imports if needed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from replit import object_storage
    HAS_OBJECT_STORAGE = True
except ImportError:
    logger.warning("Replit Object Storage not available")
    HAS_OBJECT_STORAGE = False

def list_history_files(limit=5) -> List[str]:
    """List a few history files"""
    if not HAS_OBJECT_STORAGE:
        print("Object Storage is not available")
        return []
        
    try:
        # Get environment variables for storage
        repl_id = os.environ.get("REPL_ID")
        if not repl_id:
            print("ERROR: REPL_ID environment variable not found")
            return []
            
        # Create client
        client = object_storage.Client()
        bucket_name = f"replit-objstore-{repl_id}"
        print(f"Checking bucket: {bucket_name}")
        
        # List objects with 'chromadb/history/' prefix
        prefix = "chromadb/history/"
        objects = list(client.list(prefix=prefix))
        
        # Return first few objects, store their names as strings
        files = []
        for obj in objects[:limit]:
            if hasattr(obj, 'key'):
                files.append(obj.key)
            elif hasattr(obj, 'name'):
                files.append(obj.name)
            else:
                # Just convert the object to string if all else fails
                files.append(str(obj))
                
        return files
        
    except Exception as e:
        print(f"ERROR: {e}")
        return []

def delete_file(file_path: str) -> bool:
    """Delete a single file from object storage"""
    if not HAS_OBJECT_STORAGE:
        print("Object Storage is not available")
        return False
        
    try:
        # Get environment variables for storage
        repl_id = os.environ.get("REPL_ID")
        if not repl_id:
            print("ERROR: REPL_ID environment variable not found")
            return False
            
        # Create client
        client = object_storage.Client()
        
        # Delete the file
        print(f"Deleting file: {file_path}")
        client.delete(file_path)
        print(f"Successfully deleted: {file_path}")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    print("\n=== Delete Single History File (Sanity Check) ===\n")
    
    # List a few history files
    print("Listing history files...")
    files = list_history_files(limit=5)
    
    if not files:
        print("No history files found")
        return 1
        
    print(f"\nFound {len(files)} history files:")
    for i, file in enumerate(files):
        print(f"{i+1}. {file}")
        
    # Delete the first file as a sanity check
    if files:
        print("\nAttempting to delete the first file...")
        success = delete_file(files[0])
        
        if success:
            print("\nSUCCESS: Sanity check passed - was able to delete a history file")
            print("You can now delete all history files using a similar approach")
        else:
            print("\nFAILED: Could not delete history file")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())