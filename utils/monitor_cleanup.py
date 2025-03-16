#!/usr/bin/env python3
"""
Monitoring script for ChromaDB history cleanup.
This script checks the current state of storage and shows progress.
"""

import os
import sys
import time
import logging
from typing import List, Dict, Tuple, Optional
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
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
    """List all history files in object storage"""
    if not HAS_OBJECT_STORAGE:
        logger.error("Object Storage is not available")
        return []
        
    try:
        client = object_storage.Client()
        prefix = "chromadb/history/"
        objects = list(client.list(prefix=prefix))
        
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
        logger.error(f"Error listing history files: {str(e)}")
        return []

def get_cleanup_progress() -> Dict:
    """
    Get current cleanup progress and statistics
    
    Returns:
        Dictionary with progress statistics
    """
    history_files = list_history_files()
    
    # Group files by timestamp directory
    backup_dirs = {}
    for path in history_files:
        parts = path.split('/')
        if len(parts) >= 3:
            # Format: chromadb/history/YYYYMMDD_HHMMSS/
            timestamp_dir = parts[2]  # YYYYMMDD_HHMMSS
            if timestamp_dir not in backup_dirs:
                backup_dirs[timestamp_dir] = []
            backup_dirs[timestamp_dir].append(path)
    
    # Sort directories by timestamp (newest first)
    sorted_dirs = sorted(backup_dirs.keys(), reverse=True)
    
    # Estimate storage usage (each backup is approximately 152MB)
    estimated_size_mb = len(sorted_dirs) * 152
    
    # Get dates of oldest and newest backups
    oldest_date = None
    newest_date = None
    
    if sorted_dirs:
        try:
            # Convert timestamp format YYYYMMDD_HHMMSS to datetime
            newest_str = sorted_dirs[0]
            oldest_str = sorted_dirs[-1]
            
            newest_date = datetime.strptime(newest_str, "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
            oldest_date = datetime.strptime(oldest_str, "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.warning(f"Error parsing dates: {e}")
    
    # Return progress statistics
    return {
        "total_backups": len(sorted_dirs),
        "total_files": len(history_files),
        "estimated_size_mb": estimated_size_mb,
        "estimated_size_formatted": format_size(estimated_size_mb * 1024 * 1024),
        "newest_backup": newest_date,
        "oldest_backup": oldest_date,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def save_progress_history(progress: Dict):
    """Save progress history to a file"""
    history_file = "cleanup_progress.json"
    
    # Load existing history
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
        except Exception as e:
            logger.warning(f"Error loading history file: {e}")
    
    # Add current progress
    history.append(progress)
    
    # Save updated history
    try:
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving history file: {e}")

def main():
    """Main function"""
    progress = get_cleanup_progress()
    
    # Print current progress
    print(f"\n===== ChromaDB History Cleanup Progress =====")
    print(f"Time: {progress['timestamp']}")
    print(f"Total backup directories: {progress['total_backups']}")
    print(f"Total files: {progress['total_files']}")
    print(f"Estimated storage usage: {progress['estimated_size_formatted']}")
    
    if progress['newest_backup']:
        print(f"Newest backup: {progress['newest_backup']}")
    if progress['oldest_backup']:
        print(f"Oldest backup: {progress['oldest_backup']}")
    
    # Save progress for historical tracking
    save_progress_history(progress)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())