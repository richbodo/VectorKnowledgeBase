#!/usr/bin/env python3
"""
Utility script to delete all backup history files from Replit Object Storage.

This script will:
1. Connect to Replit Object Storage
2. Identify and list all historical backup files (files with backup_ prefix)
3. Delete them while keeping the current database files
4. Provide a summary of deleted files and saved storage space

Usage:
    python utils/delete_backup_history.py [--force]

Options:
    --force    Skip confirmation prompt and delete all history files
"""

import os
import sys
import logging
import argparse
from typing import List, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.object_storage import get_chroma_storage
except ImportError:
    logger.error("Failed to import required modules. Make sure you're running from the project root.")
    sys.exit(1)


def delete_backup_history(force: bool = False) -> Tuple[List[str], int]:
    """
    Delete all backup history files from Replit Object Storage.
    
    Args:
        force: If True, skip confirmation and delete all files
        
    Returns:
        Tuple containing list of deleted files and total bytes saved
    """
    storage = get_chroma_storage()
    
    # List all files in storage
    all_files = storage.list_files()
    logger.info(f"Found {len(all_files)} total files in object storage")
    
    # Identify backup history files (files with backup_ prefix)
    history_files = [f for f in all_files if '/backup_' in f]
    current_files = [f for f in all_files if '/backup_' not in f]
    
    logger.info(f"Found {len(history_files)} backup history files")
    logger.info(f"Found {len(current_files)} current database files")
    
    if not history_files:
        logger.info("No backup history files to delete.")
        return [], 0
    
    # Calculate size information if available
    try:
        # Access client safely
        client = getattr(storage, '_client', None)
        if client and hasattr(client, 'get_object_size'):
            size_before = sum(client.get_object_size(f) for f in all_files)
            logger.info(f"Current storage usage: {size_before / (1024*1024):.2f} MB")
        else:
            logger.warning("Object storage client not properly initialized")
            size_before = 0
    except Exception as e:
        logger.warning(f"Unable to calculate storage size: {str(e)}")
        size_before = 0
    
    # Ask for confirmation if not forced
    if not force:
        print(f"\nWARNING: About to delete {len(history_files)} backup history files.")
        print("This operation cannot be undone.")
        print("Current database files will be preserved.")
        
        # Show sample of files to be deleted (first 5)
        if history_files:
            print("\nSample files to be deleted:")
            for f in history_files[:5]:
                print(f"  - {f}")
            if len(history_files) > 5:
                print(f"  - ... and {len(history_files) - 5} more")
        
        confirmation = input("\nType 'yes' to confirm deletion: ")
        if confirmation.lower() != 'yes':
            logger.info("Operation cancelled by user.")
            return [], 0
    
    # Delete all history files
    deleted_files = []
    saved_bytes = 0
    
    for file_path in history_files:
        try:
            # Get file size before deletion if possible
            try:
                file_size = storage._client.get_object_size(file_path)
                saved_bytes += file_size
            except:
                file_size = 0
            
            # Delete the file
            storage._client.delete(file_path)
            deleted_files.append(file_path)
            
            logger.info(f"Deleted {file_path} ({file_size / (1024):.2f} KB)")
        except Exception as e:
            logger.error(f"Failed to delete {file_path}: {str(e)}")
    
    # Calculate space saved
    if size_before > 0:
        try:
            size_after = sum(storage._client.get_object_size(f) for f in current_files)
            logger.info(f"New storage usage: {size_after / (1024*1024):.2f} MB")
            logger.info(f"Saved approximately {(size_before - size_after) / (1024*1024):.2f} MB")
        except Exception as e:
            logger.warning(f"Unable to calculate final storage size: {str(e)}")
    
    logger.info(f"Successfully deleted {len(deleted_files)} backup history files")
    return deleted_files, saved_bytes


def main():
    parser = argparse.ArgumentParser(
        description="Delete all backup history files from Replit Object Storage"
    )
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Skip confirmation prompt and delete all history files"
    )
    
    args = parser.parse_args()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n=== ChromaDB Backup History Cleanup ({timestamp}) ===\n")
    
    try:
        print("*" * 80)
        print("STARTING DELETE BACKUP HISTORY OPERATION")
        print("*" * 80)
        deleted_files, saved_bytes = delete_backup_history(force=args.force)
        
        print("*" * 80)
        if deleted_files:
            print(f"\nSUCCESS: Deleted {len(deleted_files)} backup history files")
            print(f"STORAGE: Freed approximately {saved_bytes / (1024*1024):.2f} MB of storage space")
            print("\nCurrent database files were preserved and remain accessible.")
            for f in deleted_files[:5]:
                print(f"  - {f}")
            if len(deleted_files) > 5:
                print(f"  - ... and {len(deleted_files) - 5} more")
        else:
            print("\nINFO: No backup history files were deleted.")
        print("*" * 80)
            
    except Exception as e:
        logger.error(f"Error during backup history deletion: {str(e)}", exc_info=True)
        print(f"\nFailed to delete backup history: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())