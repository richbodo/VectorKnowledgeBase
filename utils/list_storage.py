#!/usr/bin/env python3
"""
Utility script to list history files in object storage with counts and timestamps.
"""

import os
import sys
import logging
import collections
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.object_storage import ChromaObjectStorage
except ImportError:
    logger.error("Failed to import required modules. Make sure you're running from the project root.")
    sys.exit(1)

def format_size(size_bytes):
    """Format size in bytes to human-readable format"""
    if size_bytes < 0:
        return "Unknown"
        
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024 or unit == 'GB':
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024

def list_history_files():
    """List history files in object storage with improved organization"""
    storage = ChromaObjectStorage()
    
    # Get all files
    all_files = storage.list_files()
    logger.info(f"Found {len(all_files)} total files in object storage")
    
    # Filter for history files
    history_files = [f for f in all_files if '/history/' in f]
    logger.info(f"Found {len(history_files)} history files in object storage")
    
    # Group files by timestamp
    backup_dirs = {}
    # Format: chromadb/history/YYYYMMDD_HHMMSS/filename
    for file_path in history_files:
        parts = file_path.split('/')
        if len(parts) >= 3:
            timestamp_dir = parts[2]  # YYYYMMDD_HHMMSS
            if timestamp_dir not in backup_dirs:
                backup_dirs[timestamp_dir] = []
            backup_dirs[timestamp_dir].append(file_path)
    
    # Count files by timestamp and sort by timestamp (newest first)
    timestamps = sorted(backup_dirs.keys(), reverse=True)
    
    # Print statistics and summary
    print(f"\n=== ChromaDB History Files Summary ===")
    print(f"Total number of history files: {len(history_files)}")
    print(f"Number of backup timestamps: {len(timestamps)}")
    
    # Print backup timestamps and file counts
    print(f"\n=== Backup Timestamps ===")
    for i, timestamp in enumerate(timestamps):
        file_count = len(backup_dirs[timestamp])
        try:
            # Try to parse the timestamp
            dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
            formatted_dt = dt.strftime("%Y-%m-%d %H:%M:%S")
            print(f"{i+1}. {timestamp} ({formatted_dt}) - {file_count} files")
        except ValueError:
            # If timestamp format is not as expected
            print(f"{i+1}. {timestamp} - {file_count} files")
    
    # List the most recent backup files
    if timestamps:
        most_recent = timestamps[0]
        print(f"\n=== Most Recent Backup ({most_recent}) ===")
        for file_path in sorted(backup_dirs[most_recent]):
            print(f"  - {file_path}")
            
    if not history_files:
        print("\n=== No History Files Found ===")
    
def main():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n=== ChromaDB Object Storage Contents ({timestamp}) ===\n")
    
    try:
        list_history_files()
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}", exc_info=True)
        print(f"\nFailed to list files: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())