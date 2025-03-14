
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

def backup_chroma_db():
    """Create a backup of the ChromaDB directory"""
    # Create timestamp for the backup folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"{CHROMA_DB_PATH}_backup_{timestamp}"
    
    print(f"ChromaDB path: {os.path.abspath(CHROMA_DB_PATH)}")
    print(f"Directory exists: {os.path.exists(CHROMA_DB_PATH)}")
    
    if not os.path.exists(CHROMA_DB_PATH):
        logger.error(f"ChromaDB directory not found at {CHROMA_DB_PATH}")
        return False, f"Database directory not found at {CHROMA_DB_PATH}"
    
    try:
        # Copy the entire ChromaDB directory
        shutil.copytree(CHROMA_DB_PATH, backup_dir)
        logger.info(f"Created backup at: {backup_dir}")
        return True, backup_dir
    except Exception as e:
        logger.error(f"Failed to create backup: {str(e)}", exc_info=True)
        return False, str(e)

if __name__ == "__main__":
    print(f"===== ChromaDB Backup Tool =====")
    print(f"This tool will create a backup of your ChromaDB database")
    
    success, message = backup_chroma_db()
    
    if success:
        print(f"\n✅ Backup created successfully at: {message}")
    else:
        print(f"\n❌ Backup failed: {message}")
