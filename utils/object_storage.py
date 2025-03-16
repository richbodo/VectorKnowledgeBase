#!/usr/bin/env python3
"""
Utility for syncing ChromaDB data with Replit Object Storage.
This ensures data persistence across Replit restarts and deployments.
"""
import os
import sys
import logging
import shutil
import tempfile
from datetime import datetime
from typing import Tuple, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path to import config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import CHROMA_DB_PATH

# Import Replit Object Storage
try:
    from replit.object_storage import Client
    HAS_OBJECT_STORAGE = True
except ImportError:
    logger.warning("Replit Object Storage not available, running in local mode")
    HAS_OBJECT_STORAGE = False


class ChromaObjectStorage:
    """Handles syncing ChromaDB with Replit Object Storage"""
    
    def __init__(self):
        """Initialize the storage handler"""
        self.client = Client() if HAS_OBJECT_STORAGE else None
        self.storage_prefix = "chromadb/"
        
    def _get_storage_path(self, filename: str) -> str:
        """Get the storage path for a file"""
        return f"{self.storage_prefix}{filename}"
    
    def list_files(self) -> List[str]:
        """List all ChromaDB files in Object Storage"""
        if not HAS_OBJECT_STORAGE:
            logger.warning("Object Storage not available")
            return []
            
        try:
            # List objects with the ChromaDB prefix
            objects = list(self.client.list(prefix=self.storage_prefix))
            
            # Handle different response formats from Replit Object Storage
            file_list = []
            for obj in objects:
                try:
                    if hasattr(obj, 'key'):
                        file_list.append(obj.key)
                    elif isinstance(obj, str):
                        file_list.append(obj)
                    elif hasattr(obj, 'name'):
                        file_list.append(obj.name)
                    elif isinstance(obj, dict) and 'key' in obj:
                        file_list.append(obj['key'])
                    else:
                        # Last resort - convert object to string
                        file_list.append(str(obj))
                except Exception as obj_error:
                    logger.warning(f"Error processing object in list: {str(obj_error)}")
                    continue
                    
            return file_list
        except Exception as e:
            logger.error(f"Error listing files in Object Storage: {str(e)}")
            return []
    
    def backup_to_object_storage(self) -> Tuple[bool, Optional[str]]:
        """
        Backup ChromaDB to Replit Object Storage
        Returns: (success, message)
        """
        if not HAS_OBJECT_STORAGE:
            logger.warning("Object Storage not available, skipping backup")
            return False, "Object Storage not available"
            
        if not os.path.exists(CHROMA_DB_PATH):
            logger.error(f"ChromaDB directory not found at {CHROMA_DB_PATH}")
            return False, f"Database directory not found at {CHROMA_DB_PATH}"
        
        try:
            # Create a timestamp for the backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Check ChromaDB files
            chroma_files = os.listdir(CHROMA_DB_PATH)
            logger.info(f"Found {len(chroma_files)} files in ChromaDB directory")
            
            # Check for SQLite file - essential for persistence
            sqlite_path = os.path.join(CHROMA_DB_PATH, "chroma.sqlite3")
            if not os.path.exists(sqlite_path):
                logger.warning("SQLite file not found in ChromaDB directory")
                
            # Upload each file in the ChromaDB directory
            for filename in chroma_files:
                file_path = os.path.join(CHROMA_DB_PATH, filename)
                if os.path.isfile(file_path):
                    # Store with timestamp to keep versioning
                    storage_key = self._get_storage_path(filename)
                    
                    # Upload the file with full absolute path
                    logger.info(f"Uploading file {file_path} to {storage_key}")
                    self.client.upload_from_filename(storage_key, os.path.abspath(file_path))
                    logger.info(f"Uploaded {filename} to Object Storage")
                    
                    # Also store a timestamped version for historical tracking
                    history_key = f"{self.storage_prefix}history/{timestamp}/{filename}"
                    logger.info(f"Creating history version at {history_key}")
                    self.client.upload_from_filename(history_key, os.path.abspath(file_path))
            
            # After successful backup, rotate to maintain max backups
            kept, deleted = self._rotate_backups(max_backups=24)
            logger.info(f"Backup rotation: kept {kept} backups, deleted {deleted} old files")
            
            # Create a manifest file with timestamp and file list
            manifest = {
                "timestamp": timestamp,
                "files": chroma_files,
                "db_path": CHROMA_DB_PATH
            }
            
            # Convert manifest to string
            import json
            manifest_content = json.dumps(manifest, indent=2).encode('utf-8')
            
            # Upload manifest
            manifest_key = self._get_storage_path("manifest.json")
            self.client.upload_from_bytes(manifest_key, manifest_content)
            logger.info(f"Created backup manifest in Object Storage")
            
            return True, f"Backup completed at {timestamp}"
        
        except Exception as e:
            logger.error(f"Failed to backup to Object Storage: {str(e)}", exc_info=True)
            return False, str(e)
    
    def restore_from_object_storage(self) -> Tuple[bool, Optional[str]]:
        """
        Restore ChromaDB from Replit Object Storage
        Returns: (success, message)
        """
        if not HAS_OBJECT_STORAGE:
            logger.warning("Object Storage not available, skipping restore")
            return False, "Object Storage not available"
        
        try:
            # Check if manifest exists
            manifest_key = self._get_storage_path("manifest.json")
            if not self.client.exists(manifest_key):
                logger.warning("No backup manifest found in Object Storage")
                return False, "No backup manifest found"
                
            # Download and parse manifest
            manifest_content = self.client.download_as_bytes(manifest_key)
            import json
            manifest = json.loads(manifest_content.decode('utf-8'))
            
            logger.info(f"Found backup from {manifest['timestamp']}")
            
            # Create a backup of current ChromaDB directory if it exists
            if os.path.exists(CHROMA_DB_PATH):
                backup_dir = f"{CHROMA_DB_PATH}_local_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copytree(CHROMA_DB_PATH, backup_dir)
                logger.info(f"Created local backup at {backup_dir}")
                
            # Create ChromaDB directory if it doesn't exist
            os.makedirs(CHROMA_DB_PATH, exist_ok=True)
            
            # Download each file listed in the manifest
            for filename in manifest['files']:
                storage_key = self._get_storage_path(filename)
                if self.client.exists(storage_key):
                    file_path = os.path.join(CHROMA_DB_PATH, filename)
                    logger.info(f"Downloading {storage_key} to {file_path}")
                    self.client.download_to_filename(storage_key, os.path.abspath(file_path))
                    logger.info(f"Restored {filename} from Object Storage")
                else:
                    logger.warning(f"File {filename} not found in Object Storage")
            
            return True, f"Restore completed from backup {manifest['timestamp']}"
            
        except Exception as e:
            logger.error(f"Failed to restore from Object Storage: {str(e)}", exc_info=True)
            return False, str(e)
    
    def _rotate_backups(self, max_backups=24) -> Tuple[int, int]:
        """
        Limit the number of historical backups by removing older ones.
        
        Args:
            max_backups: Maximum number of historical backups to keep
        
        Returns:
            Tuple[int, int]: (kept_count, deleted_count)
        """
        if not HAS_OBJECT_STORAGE:
            logger.warning("Object Storage not available, skipping backup rotation")
            return 0, 0
            
        try:
            # List all history backups
            history_pattern = f"{self.storage_prefix}history/"
            history_objects = list(self.client.list(prefix=history_pattern))
            
            # Group objects by timestamp directory
            backup_dirs = {}
            for obj in history_objects:
                # Extract the timestamp directory from the path
                # Format: chromadb/history/YYYYMMDD_HHMMSS/filename
                path = obj.key if hasattr(obj, 'key') else str(obj)
                parts = path.split('/')
                if len(parts) >= 3:
                    # Get the timestamp directory
                    timestamp_dir = parts[2]  # YYYYMMDD_HHMMSS
                    if timestamp_dir not in backup_dirs:
                        backup_dirs[timestamp_dir] = []
                    backup_dirs[timestamp_dir].append(path)
            
            # Sort directories by timestamp (newest first)
            sorted_dirs = sorted(backup_dirs.keys(), reverse=True)
            logger.info(f"Found {len(sorted_dirs)} backup directories in history")
            
            if len(sorted_dirs) <= max_backups:
                logger.info(f"No rotation needed, only {len(sorted_dirs)} backups exist (limit: {max_backups})")
                return len(sorted_dirs), 0
            
            # Keep max_backups, delete the rest
            to_keep = sorted_dirs[:max_backups]
            to_delete = sorted_dirs[max_backups:]
            
            deleted_count = 0
            # Delete older backups
            for old_dir in to_delete:
                logger.info(f"Removing old backup: {old_dir}")
                for obj_path in backup_dirs[old_dir]:
                    self.client.delete(obj_path)
                    deleted_count += 1
                    
            logger.info(f"Backup rotation complete: kept {len(to_keep)}, deleted {deleted_count} objects from {len(to_delete)} old backups")
            return len(to_keep), deleted_count
        
        except Exception as e:
            logger.error(f"Error during backup rotation: {str(e)}")
            return 0, 0
    
    def sync_with_object_storage(self) -> Tuple[bool, Optional[str]]:
        """
        Sync ChromaDB with Replit Object Storage (bidirectional)
        Returns: (success, message)
        """
        if not HAS_OBJECT_STORAGE:
            logger.warning("Object Storage not available, skipping sync")
            return False, "Object Storage not available"
            
        try:
            # First check if ChromaDB directory exists locally
            local_db_exists = os.path.exists(CHROMA_DB_PATH) and os.path.isdir(CHROMA_DB_PATH)
            
            # Check if important files exist locally
            local_sqlite_exists = False
            if local_db_exists:
                sqlite_path = os.path.join(CHROMA_DB_PATH, "chroma.sqlite3")
                local_sqlite_exists = os.path.exists(sqlite_path)
                if local_sqlite_exists:
                    # Get file size and modification time
                    size_mb = os.path.getsize(sqlite_path) / (1024 * 1024)
                    mod_time = datetime.fromtimestamp(os.path.getmtime(sqlite_path))
                    logger.info(f"Local SQLite file exists with size: {size_mb:.2f} MB, modified: {mod_time}")
                
            # Check if database exists in Object Storage
            manifest_key = self._get_storage_path("manifest.json")
            storage_db_exists = self.client.exists(manifest_key)
            
            # If neither exists, we have a fresh start
            if not local_db_exists and not storage_db_exists:
                logger.info("No existing ChromaDB found locally or in Object Storage")
                return True, "No existing database to sync"
                
            # If local exists but not in storage, backup local to storage
            if local_db_exists and local_sqlite_exists and not storage_db_exists:
                logger.info("Local ChromaDB exists but not in Object Storage, backing up")
                success, message = self.backup_to_object_storage()
                return success, f"Initial backup: {message}"
                
            # If storage exists but not local, restore from storage
            if storage_db_exists and (not local_db_exists or not local_sqlite_exists):
                logger.info("ChromaDB exists in Object Storage but not locally, restoring")
                success, message = self.restore_from_object_storage()
                return success, f"Initial restore: {message}"
                
            # Both exist, check timestamps to determine which is newer
            if local_db_exists and local_sqlite_exists and storage_db_exists:
                # Get local timestamp
                sqlite_path = os.path.join(CHROMA_DB_PATH, "chroma.sqlite3")
                local_timestamp = datetime.fromtimestamp(os.path.getmtime(sqlite_path))
                
                # Get storage timestamp from manifest
                manifest_content = self.client.download_as_bytes(manifest_key)
                import json
                manifest = json.loads(manifest_content.decode('utf-8'))
                storage_timestamp = datetime.strptime(manifest['timestamp'], "%Y%m%d_%H%M%S")
                
                logger.info(f"Local timestamp: {local_timestamp}, Storage timestamp: {storage_timestamp}")
                
                # If local is newer, backup to storage
                if local_timestamp > storage_timestamp:
                    logger.info("Local ChromaDB is newer, backing up to Object Storage")
                    success, message = self.backup_to_object_storage()
                    return success, f"Sync (local to storage): {message}"
                    
                # If storage is newer, restore from storage
                elif storage_timestamp > local_timestamp:
                    logger.info("Storage ChromaDB is newer, restoring from Object Storage")
                    success, message = self.restore_from_object_storage()
                    return success, f"Sync (storage to local): {message}"
                    
                # If timestamps match, no action needed
                else:
                    logger.info("Local and storage ChromaDB are in sync")
                    return True, "Already in sync"
            
            # Default fallback
            return False, "Unable to determine sync action"
                
        except Exception as e:
            logger.error(f"Failed to sync with Object Storage: {str(e)}", exc_info=True)
            return False, str(e)


# Create a singleton instance
_instance = None

def get_chroma_storage():
    """Get the ChromaObjectStorage instance"""
    global _instance
    if _instance is None:
        _instance = ChromaObjectStorage()
    return _instance


if __name__ == "__main__":
    """CLI for testing and manual operations"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ChromaDB Object Storage CLI")
    parser.add_argument('action', choices=['backup', 'restore', 'sync', 'list'], 
                      help='Action to perform')
    
    args = parser.parse_args()
    
    storage = ChromaObjectStorage()
    
    if args.action == 'backup':
        print("==== Backing up ChromaDB to Object Storage ====")
        success, message = storage.backup_to_object_storage()
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
            
    elif args.action == 'restore':
        print("==== Restoring ChromaDB from Object Storage ====")
        success, message = storage.restore_from_object_storage()
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
            
    elif args.action == 'sync':
        print("==== Syncing ChromaDB with Object Storage ====")
        success, message = storage.sync_with_object_storage()
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
            
    elif args.action == 'list':
        print("==== Listing ChromaDB files in Object Storage ====")
        files = storage.list_files()
        if files:
            print(f"Found {len(files)} files:")
            for file in files:
                print(f" - {file}")
        else:
            print("No files found")