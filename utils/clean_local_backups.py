#!/usr/bin/env python3
"""
Utility script to clean up local ChromaDB backup directories.

This script will:
1. Find all local backup directories
2. Keep the most recent backup (if any)
3. Remove all other backup directories
4. Provide a summary of freed space

Usage:
    python utils/clean_local_backups.py [--keep N]

Options:
    --keep N    Number of recent backups to keep (default: 1)
"""

import argparse
import glob
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('clean_local_backups.log')
    ]
)
logger = logging.getLogger('clean_local_backups')

def get_backup_dirs():
    """Find all local ChromaDB backup directories"""
    data_dir = Path('/home/runner/data')
    backup_pattern = 'chromadb_local_backup_*'
    
    # Find all backup directories
    backup_dirs = sorted(data_dir.glob(backup_pattern))
    return backup_dirs

def get_dir_size(path):
    """Get the size of a directory in bytes"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if not os.path.islink(file_path):
                total_size += os.path.getsize(file_path)
    return total_size

def format_size(size_bytes):
    """Format size in bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024 or unit == 'GB':
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024

def clean_backups(keep=1):
    """
    Clean up local ChromaDB backup directories, keeping the N most recent
    
    Args:
        keep: Number of recent backups to keep
        
    Returns:
        Tuple(int, int): (number of directories removed, bytes freed)
    """
    backup_dirs = get_backup_dirs()
    
    if not backup_dirs:
        logger.info("No backup directories found")
        return 0, 0
    
    logger.info(f"Found {len(backup_dirs)} backup directories")
    
    # Keep the N most recent backups
    dirs_to_keep = backup_dirs[-keep:] if keep > 0 else []
    dirs_to_remove = [d for d in backup_dirs if d not in dirs_to_keep]
    
    if not dirs_to_remove:
        logger.info(f"No backup directories to remove (keeping {keep} most recent)")
        return 0, 0
    
    total_size = 0
    removed_count = 0
    
    # Remove the directories
    for backup_dir in dirs_to_remove:
        dir_size = get_dir_size(backup_dir)
        logger.info(f"Removing {backup_dir} ({format_size(dir_size)})")
        
        try:
            shutil.rmtree(backup_dir)
            total_size += dir_size
            removed_count += 1
            logger.info(f"Removed {backup_dir}")
        except Exception as e:
            logger.error(f"Failed to remove {backup_dir}: {e}")
    
    return removed_count, total_size

def main():
    parser = argparse.ArgumentParser(description='Clean up local ChromaDB backup directories')
    parser.add_argument('--keep', type=int, default=1, help='Number of recent backups to keep')
    args = parser.parse_args()
    
    logger.info("Starting local backup cleanup")
    logger.info(f"Will keep {args.keep} most recent backups")
    
    removed, bytes_freed = clean_backups(keep=args.keep)
    
    logger.info(f"Cleanup complete: Removed {removed} directories, freed {format_size(bytes_freed)}")
    
    print(f"\nSummary:")
    print(f"- Removed {removed} backup directories")
    print(f"- Freed {format_size(bytes_freed)} of disk space")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())