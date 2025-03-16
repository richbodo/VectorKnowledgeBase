#!/usr/bin/env python3
"""
Utility script to clear the history backups in object storage.
This is a one-time operation to clean up excessive historical backups.
"""
import os
import sys
import logging
from typing import List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path to import config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.object_storage import ChromaObjectStorage

def clear_history_backups() -> List[str]:
    """
    Clear all history backups from object storage while preserving the current database files.
    
    Returns:
        List of deleted files
    """
    try:
        storage = ChromaObjectStorage()
        
        # First list all files
        all_files = storage.list_files()
        logger.info(f"Found {len(all_files)} total files in object storage")
        
        # Filter only history files
        history_pattern = "chromadb/history/"
        history_files = [f for f in all_files if history_pattern in f]
        logger.info(f"Found {len(history_files)} history files to delete")
        
        if not history_files:
            logger.info("No history files found to delete")
            return []
            
        # Confirm before deletion
        confirmation = input(f"Are you sure you want to delete {len(history_files)} history files? (y/n): ")
        if confirmation.lower() != 'y':
            logger.info("Operation cancelled by user")
            return []
            
        # Delete files
        deleted_files = []
        for file_path in history_files:
            try:
                storage.client.delete(file_path)
                deleted_files.append(file_path)
                logger.info(f"Deleted {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete {file_path}: {str(e)}")
                
        logger.info(f"Successfully deleted {len(deleted_files)} of {len(history_files)} files")
        return deleted_files
        
    except Exception as e:
        logger.error(f"Error clearing history backups: {str(e)}")
        return []

if __name__ == "__main__":
    print("==== Clearing ChromaDB History Backups ====")
    
    # Add a special flag for non-interactive execution
    force = "--force" in sys.argv
    
    if force:
        # For non-interactive runs with --force
        storage = ChromaObjectStorage()
        all_files = storage.list_files()
        history_pattern = "chromadb/history/"
        history_files = [f for f in all_files if history_pattern in f]
        
        logger.info(f"Force mode: Deleting {len(history_files)} history files without confirmation")
        
        deleted_files = []
        for file_path in history_files:
            try:
                storage.client.delete(file_path)
                deleted_files.append(file_path)
                logger.info(f"Deleted {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete {file_path}: {str(e)}")
                
        logger.info(f"Successfully deleted {len(deleted_files)} of {len(history_files)} files")
        print(f"✅ Cleared {len(deleted_files)} history files")
    else:
        # Interactive mode
        deleted = clear_history_backups()
        if deleted:
            print(f"✅ Cleared {len(deleted)} history files")
        else:
            print("❌ No files were deleted")