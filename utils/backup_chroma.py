
#!/usr/bin/env python3
import os
import sys
import shutil
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import CHROMA_DB_PATH
from utils.object_storage import get_chroma_storage

def backup_chroma_db(use_object_storage=True):
    """
    Create a backup of the ChromaDB directory
    
    Args:
        use_object_storage: If True, also backup to Replit Object Storage
        
    Returns:
        Tuple[success, message]
    """
    # Create timestamp for the backup folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"{CHROMA_DB_PATH}_backup_{timestamp}"
    
    print(f"ChromaDB path: {os.path.abspath(CHROMA_DB_PATH)}")
    print(f"Directory exists: {os.path.exists(CHROMA_DB_PATH)}")
    
    if not os.path.exists(CHROMA_DB_PATH):
        logger.error(f"ChromaDB directory not found at {CHROMA_DB_PATH}")
        return False, f"Database directory not found at {CHROMA_DB_PATH}"
    
    success_messages = []
    
    try:
        # Create local backup
        shutil.copytree(CHROMA_DB_PATH, backup_dir)
        logger.info(f"Created local backup at: {backup_dir}")
        success_messages.append(f"Local backup created at: {backup_dir}")
        
        # If object storage is available and requested, also backup to object storage
        if use_object_storage:
            try:
                # Get the object storage handler
                storage = get_chroma_storage()
                
                # Backup to object storage
                os_success, os_message = storage.backup_to_object_storage()
                
                if os_success:
                    logger.info(f"Object Storage backup successful: {os_message}")
                    success_messages.append(f"Object Storage backup: {os_message}")
                else:
                    logger.warning(f"Object Storage backup failed: {os_message}")
                    success_messages.append(f"Object Storage backup failed: {os_message}")
                    
            except Exception as os_error:
                logger.error(f"Object Storage backup error: {str(os_error)}", exc_info=True)
                success_messages.append(f"Object Storage backup error: {str(os_error)}")
        
        return True, " | ".join(success_messages)
        
    except Exception as e:
        logger.error(f"Failed to create backup: {str(e)}", exc_info=True)
        
        # If local backup failed but we want to try object storage
        if use_object_storage:
            try:
                logger.info("Attempting backup to Object Storage despite local backup failure")
                storage = get_chroma_storage()
                os_success, os_message = storage.backup_to_object_storage()
                
                if os_success:
                    logger.info(f"Object Storage backup successful despite local failure: {os_message}")
                    return True, f"Local backup failed, but Object Storage backup succeeded: {os_message}"
            except Exception as os_error:
                logger.error(f"Both backups failed. Object Storage error: {str(os_error)}", exc_info=True)
                
        return False, str(e)

def restore_from_object_storage():
    """
    Restore ChromaDB from Replit Object Storage
    
    Returns:
        Tuple[success, message]
    """
    try:
        # Get the object storage handler
        storage = get_chroma_storage()
        
        # Restore from object storage
        success, message = storage.restore_from_object_storage()
        
        return success, message
        
    except Exception as e:
        logger.error(f"Failed to restore from Object Storage: {str(e)}", exc_info=True)
        return False, str(e)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ChromaDB Backup Tool")
    parser.add_argument('--action', choices=['backup', 'restore', 'list'], 
                      default='backup', help='Action to perform')
    parser.add_argument('--local-only', action='store_true', 
                      help='For backup: Only create local backup, skip Object Storage')
    
    args = parser.parse_args()
    
    if args.action == 'backup':
        print(f"===== ChromaDB Backup Tool =====")
        print(f"This tool will create a backup of your ChromaDB database")
        
        use_object_storage = not args.local_only
        if use_object_storage:
            print("Using both local and Replit Object Storage for backup")
        else:
            print("Using local filesystem backup only")
            
        success, message = backup_chroma_db(use_object_storage=use_object_storage)
        
        if success:
            print(f"\n✅ Backup created successfully: {message}")
        else:
            print(f"\n❌ Backup failed: {message}")
            
    elif args.action == 'restore':
        print(f"===== ChromaDB Restore Tool =====")
        print(f"This tool will restore ChromaDB from Replit Object Storage")
        
        success, message = restore_from_object_storage()
        
        if success:
            print(f"\n✅ Restore completed successfully: {message}")
        else:
            print(f"\n❌ Restore failed: {message}")
            
    elif args.action == 'list':
        print(f"===== ChromaDB Object Storage Contents =====")
        
        try:
            storage = get_chroma_storage()
            files = storage.list_files()
            
            if files:
                print(f"Found {len(files)} files in Object Storage:")
                for file in files:
                    print(f" - {file}")
            else:
                print("No ChromaDB files found in Object Storage")
        except Exception as e:
            print(f"\n❌ Failed to list files: {str(e)}")
