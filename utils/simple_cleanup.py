#!/usr/bin/env python3
"""
Simple and direct cleanup script for Replit Object Storage history files.

This script takes a straightforward approach to delete ChromaDB history files,
using direct Replit object_storage access rather than complex wrapper functions.

Usage:
    python utils/simple_cleanup.py [--force]

Options:
    --force    Skip confirmation and delete all history files
"""

import os
import sys
import time
import logging
import argparse
from typing import List, Tuple, Optional

# Configure logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("simple_cleanup.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Try to import Replit object_storage
try:
    from replit import object_storage
    HAS_OBJECT_STORAGE = True
except ImportError:
    logger.warning("Replit Object Storage not available")
    HAS_OBJECT_STORAGE = False

def format_size(size_bytes):
    """Format size in bytes to human-readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ("B", "KB", "MB", "GB", "TB")
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"

def list_history_files() -> List[str]:
    """
    List all history files in object storage
    
    Returns:
        List of file paths in the history directory
    """
    if not HAS_OBJECT_STORAGE:
        logger.error("Object Storage is not available")
        return []
        
    try:
        client = object_storage.Client()
        
        # List objects with 'chromadb/history/' prefix
        prefix = "chromadb/history/"
        objects = list(client.list(prefix=prefix))
        
        # Extract file paths
        files = []
        for obj in objects:
            if hasattr(obj, 'key'):
                files.append(obj.key)
            elif hasattr(obj, 'name'):
                files.append(obj.name)
            else:
                files.append(str(obj))
                
        return files
        
    except Exception as e:
        logger.error(f"Error listing history files: {str(e)}", exc_info=True)
        return []

def delete_history_files(history_files: List[str], force: bool = False, dry_run: bool = False) -> Tuple[int, int]:
    """
    Delete history files from object storage
    
    Args:
        history_files: List of file paths to delete
        force: If True, skip confirmation
        dry_run: If True, only simulate deletion (don't actually delete files)
        
    Returns:
        Tuple of (number of files deleted, total bytes saved)
    """
    if not HAS_OBJECT_STORAGE:
        logger.error("Object Storage is not available")
        return 0, 0
        
    if not history_files:
        logger.info("No history files to delete")
        return 0, 0
    
    # In dry-run mode, just report what would be deleted
    if dry_run:
        logger.info(f"DRY RUN: Would delete {len(history_files)} history files")
        return 0, 0
    
    # When not in force mode, we'll save this for interactive use
    # But we won't try to get input in non-interactive environments
    if not force:
        logger.info("Non-force mode selected, but running in non-interactive environment.")
        logger.info("Run with --force to perform actual deletion, or --dry-run to simulate.")
        return 0, 0
    
    try:
        client = object_storage.Client()
        
        # Count bytes saved for reporting
        bytes_saved = 0
        deleted_count = 0
        
        # Delete each file
        start_time = time.time()
        for i, file_path in enumerate(history_files):
            try:
                # Print progress every 10 files
                if i % 10 == 0 or i == len(history_files) - 1:
                    logger.info(f"Deleting file {i+1}/{len(history_files)}: {file_path}")
                
                # Delete the file
                client.delete(file_path)
                deleted_count += 1
                
            except Exception as e:
                logger.error(f"Error deleting file {file_path}: {str(e)}")
        
        elapsed_time = time.time() - start_time
        logger.info(f"Successfully deleted {deleted_count}/{len(history_files)} files in {elapsed_time:.2f} seconds")
        
        return deleted_count, bytes_saved
        
    except Exception as e:
        logger.error(f"Error during deletion: {str(e)}", exc_info=True)
        return 0, 0

def main():
    """Main function for direct cleanup"""
    parser = argparse.ArgumentParser(description='Simple history cleanup for Replit Object Storage')
    parser.add_argument('--force', action='store_true', help='Skip confirmation and delete all history files')
    parser.add_argument('--dry-run', action='store_true', help='Only simulate deletion, don\'t actually delete files')
    parser.add_argument('--limit', type=int, default=0, help='Limit number of files to delete (0 for no limit)')
    parser.add_argument('--keep-recent', type=int, default=5, help='Number of most recent backups to keep')
    args = parser.parse_args()
    
    logger.info("=== Simple History Cleanup ===")
    
    # List all history files
    logger.info("Listing history files...")
    all_history_files = list_history_files()
    
    if not all_history_files:
        logger.info("No history files found")
        return 0
    
    # Group files by timestamp directory
    backup_dirs = {}
    for path in all_history_files:
        parts = path.split('/')
        if len(parts) >= 3:
            # Format: chromadb/history/YYYYMMDD_HHMMSS/
            timestamp_dir = parts[2]  # YYYYMMDD_HHMMSS
            if timestamp_dir not in backup_dirs:
                backup_dirs[timestamp_dir] = []
            backup_dirs[timestamp_dir].append(path)
    
    # Sort directories by timestamp (newest first)
    sorted_dirs = sorted(backup_dirs.keys(), reverse=True)
    logger.info(f"Found {len(sorted_dirs)} backup directories with {len(all_history_files)} total files")
    
    # Keep most recent backups based on keep_recent parameter
    to_keep = sorted_dirs[:args.keep_recent] if args.keep_recent > 0 else []
    to_delete_dirs = sorted_dirs[args.keep_recent:] if args.keep_recent > 0 else sorted_dirs
    
    # Collect all files to delete
    history_files = []
    for dir_name in to_delete_dirs:
        history_files.extend(backup_dirs[dir_name])
    
    # Apply file limit if specified
    if args.limit > 0 and len(history_files) > args.limit:
        logger.info(f"Limiting to {args.limit} files (out of {len(history_files)} total)")
        history_files = history_files[:args.limit]
    
    if not history_files:
        logger.info("No files to delete after applying filters")
        return 0
        
    logger.info(f"Found {len(history_files)} files to process")
    
    # Show a sample of files for verification
    sample_size = min(5, len(history_files))
    logger.info(f"Sample of files to be deleted (showing {sample_size}):")
    for i, file in enumerate(history_files[:sample_size]):
        logger.info(f"  {i+1}. {file}")
    
    if len(history_files) > sample_size:
        logger.info(f"  ... and {len(history_files) - sample_size} more files")
    
    # Inform about preserved backups if any
    if to_keep:
        logger.info(f"Keeping {len(to_keep)} most recent backup directories:")
        for dir_name in to_keep[:3]:  # Show first 3
            logger.info(f"  - {dir_name}")
        if len(to_keep) > 3:
            logger.info(f"  ... and {len(to_keep) - 3} more")
    
    # Delete history files
    deleted_count, bytes_saved = delete_history_files(history_files, force=args.force, dry_run=args.dry_run)
    
    if deleted_count > 0:
        logger.info(f"Successfully deleted {deleted_count} history files")
        # Report bytes saved if available
        if bytes_saved > 0:
            logger.info(f"Saved approximately {format_size(bytes_saved)} of storage space")
    else:
        logger.info("No files were deleted")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())