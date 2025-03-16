#!/usr/bin/env python3
"""
Direct cleanup script for object storage history.

This script directly targets the history directory in object storage
and deletes all files without relying on complex operations.

Usage:
    python utils/direct_cleanup.py
"""

import os
import sys
import time
import logging
from google.cloud import storage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("direct_cleanup")

def format_size(size_bytes):
    """Format size in bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024 or unit == 'GB':
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024

def clean_history_storage():
    """Clean all history files from object storage"""
    try:
        # Get environment variables for object storage
        repl_id = os.environ.get("REPL_ID")
        if not repl_id:
            logger.error("REPL_ID environment variable not found")
            return False, "REPL_ID environment variable not found"

        bucket_name = f"replit-objstore-{repl_id}"
        prefix = "chromadb/history/"

        print(f"Connecting to bucket: {bucket_name}")
        print(f"Targeting prefix: {prefix}")

        # Initialize storage client
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        
        # List all blobs in the history directory
        blobs = bucket.list_blobs(prefix=prefix)
        
        # Count and collect blobs
        blob_list = list(blobs)  # Convert iterator to list for counting
        count = len(blob_list)
        
        if count == 0:
            print("No history files found to delete")
            return True, "No history files found to delete"
        
        print(f"Found {count} files to delete:")
        total_size = 0
        
        # Print first 10 files
        for i, blob in enumerate(blob_list[:10]):
            size = blob.size
            total_size += size
            print(f"  {i+1}. {blob.name} ({format_size(size)})")
        
        if count > 10:
            print(f"  ... and {count-10} more files")
        
        # Continue with deletion
        print(f"\nDeleting {count} files...")
        start_time = time.time()
        deleted = 0
        
        for i, blob in enumerate(blob_list, 1):
            try:
                blob.delete()
                deleted += 1
                if i % 10 == 0 or i == count:
                    print(f"  Deleted {i}/{count} files...")
            except Exception as e:
                print(f"Error deleting {blob.name}: {e}")
        
        duration = time.time() - start_time
        print(f"\nCompleted: Deleted {deleted}/{count} files in {duration:.1f} seconds")
        print(f"Saved approximately {format_size(total_size)} of storage space")
        
        return True, f"Deleted {deleted} files, freed {format_size(total_size)}"
    
    except Exception as e:
        logger.error(f"Error cleaning history storage: {e}")
        return False, f"Error: {e}"

def main():
    print("\n" + "="*80)
    print(" DIRECT OBJECT STORAGE HISTORY CLEANUP ".center(80, "="))
    print("="*80 + "\n")
    
    success, message = clean_history_storage()
    
    print("\n" + "#"*80)
    print("#" + " "*78 + "#")
    if success:
        print(f"#  SUCCESS: {message}".center(78) + "#")
    else:
        print(f"#  ERROR: {message}".center(78) + "#")
    print("#" + " "*78 + "#")
    print("#"*80 + "\n")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())