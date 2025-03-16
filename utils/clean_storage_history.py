#!/usr/bin/env python3
"""
Utility script to list and clean all history files in object storage.
This script identifies and removes all historical backup files in the history directory.

Usage:
    python utils/clean_storage_history.py [--list-only] [--force]

Options:
    --list-only    Only list the files without deleting them
    --force        Skip confirmation and delete all history files
"""

import argparse
import logging
import os
import sys
import time
from typing import List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("clean_storage_history")

try:
    from utils.object_storage import ChromaObjectStorage
except ImportError:
    # Handle relative import when run directly
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.object_storage import ChromaObjectStorage

def format_size(size_bytes):
    """Format size in bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024 or unit == 'GB':
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024

def list_history_files() -> List[str]:
    """
    List all history files in object storage
    
    Returns:
        List of file paths in the history directory
    """
    storage = ChromaObjectStorage()
    
    # Get all files
    all_files = storage.list_files()
    
    # Filter for history files only - these are in the chromadb/history/ directory
    history_files = [f for f in all_files if '/history/' in f]
    
    return history_files

def delete_history_files(history_files: List[str], force: bool = False) -> Tuple[int, int]:
    """
    Delete history files from object storage
    
    Args:
        history_files: List of file paths to delete
        force: If True, skip confirmation
        
    Returns:
        Tuple of (number of files deleted, total bytes saved)
    """
    if not history_files:
        logger.info("No history files to delete")
        return 0, 0
    
    storage = ChromaObjectStorage()
    deleted_count = 0
    total_size = 0
    
    # Get client directly for file size checks
    client = storage._get_client()
    
    # Check with the user unless force is specified
    if not force:
        print(f"\nFound {len(history_files)} files in history directory")
        print("Example files:")
        for i, file in enumerate(history_files[:5]):
            print(f"  - {file}")
        if len(history_files) > 5:
            print(f"  - ... and {len(history_files) - 5} more")
        
        confirmation = input("\nDelete all these files? (y/N): ")
        if confirmation.lower() != 'y':
            logger.info("Operation cancelled by user")
            return 0, 0
    
    # Delete the files
    start_time = time.time()
    print(f"\nDeleting {len(history_files)} files...")
    
    for i, file_path in enumerate(history_files, 1):
        try:
            # Get file size before deletion if possible
            try:
                blob = client.bucket.blob(file_path)
                blob.reload()
                size = blob.size
            except Exception:
                size = 0
            
            # Delete the file
            client.delete(file_path)
            
            deleted_count += 1
            total_size += size
            
            # Progress update
            if i % 10 == 0 or i == len(history_files):
                print(f"Deleted {i}/{len(history_files)} files... ({format_size(total_size)} freed)")
        
        except Exception as e:
            logger.error(f"Failed to delete {file_path}: {e}")
    
    # Summary
    duration = time.time() - start_time
    logger.info(f"Deleted {deleted_count} files in {duration:.1f} seconds")
    logger.info(f"Freed approximately {format_size(total_size)}")
    
    return deleted_count, total_size

def list_all_files() -> List[Tuple[str, int]]:
    """
    List all files in object storage with sizes
    
    Returns:
        List of tuples (file_path, size_in_bytes)
    """
    storage = ChromaObjectStorage()
    
    # Get all files
    all_files = storage.list_files()
    
    # Get client for size info
    client = storage._get_client()
    
    results = []
    for file_path in all_files:
        try:
            # Access blob directly from client storage
            blob = client.bucket.blob(file_path)
            size = 0
            try:
                blob.reload()
                size = blob.size
            except Exception:
                # If size can't be determined, use 0
                pass
            results.append((file_path, size))
        except Exception as e:
            print(f"Error accessing {file_path}: {e}")
            results.append((file_path, 0))
    
    # Sort by size (largest first)
    results.sort(key=lambda x: x[1], reverse=True)
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Clean history files from object storage")
    parser.add_argument("--list-only", action="store_true", help="Only list files without deleting")
    parser.add_argument("--force", action="store_true", help="Skip confirmation and delete all files")
    parser.add_argument("--all", action="store_true", help="List all files in object storage, not just history")
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print(f"ChromaDB Storage History Management ({time.strftime('%Y-%m-%d %H:%M:%S')})")
    print("="*80 + "\n")
    
    # List all files if requested
    if args.all:
        print("\n--- All Files in Object Storage ---\n")
        all_files = list_all_files()
        total_size = sum(size for _, size in all_files)
        
        for file_path, size in all_files:
            print(f"{format_size(size):>10} - {file_path}")
        
        print(f"\nTotal: {len(all_files)} files, {format_size(total_size)}")
        return 0
    
    # List history files
    history_files = list_history_files()
    
    if not history_files:
        print("\n" + "#"*80)
        print("#" + " "*78 + "#")
        print("#" + "  INFO: No history files found in object storage.".center(78) + "#")
        print("#" + " "*78 + "#")
        print("#"*80)
        return 0
    
    print(f"Found {len(history_files)} files in history directory:")
    for i, file in enumerate(history_files[:10]):
        print(f"  {i+1}. {file}")
    
    if len(history_files) > 10:
        print(f"  ... and {len(history_files) - 10} more")
    
    # Delete if not list-only
    if not args.list_only:
        deleted, size_saved = delete_history_files(history_files, force=args.force)
        
        print("\n" + "#"*80)
        print("#" + " "*78 + "#")
        if deleted > 0:
            print(f"#  SUCCESS: Deleted {deleted} history files ({format_size(size_saved)} freed)".center(78) + "#")
        else:
            print("#  INFO: No files were deleted.".center(78) + "#")
        print("#" + " "*78 + "#")
        print("#"*80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())