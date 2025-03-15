#!/usr/bin/env python3
"""
Migration utility for ChromaDB databases.
This tool helps migrate data from the old ChromaDB location to the new persistent location.
"""

import os
import sys
import shutil
import logging
import sqlite3
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("migrate_chromadb")

# Define paths
source_paths = [
    "/home/runner/workspace/chroma_db",
    "/home/runner/.cache/chromadb",
    "/home/runner/workspace/.cache/chromadb",
    "/home/runner/data/chroma_db",  # Old location in data folder
    "chroma_db",
    os.path.join(os.getcwd(), "chroma_db"),
]

# The destination is the official persistent path
DEST_PATH = "/home/runner/data/chromadb"  # New location

def check_db_contents(db_path):
    """Check the contents of a ChromaDB directory"""
    if not os.path.exists(db_path) or not os.path.isdir(db_path):
        logger.warning(f"{db_path} does not exist or is not a directory")
        return None
    
    contents = os.listdir(db_path)
    logger.info(f"Contents of {db_path}: {contents}")
    
    sqlite_path = os.path.join(db_path, "chroma.sqlite3")
    if not os.path.exists(sqlite_path):
        logger.warning(f"No SQLite file found at {sqlite_path}")
        return None
    
    size_mb = os.path.getsize(sqlite_path) / (1024 * 1024)
    logger.info(f"SQLite file size: {size_mb:.2f} MB")
    
    try:
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        
        # Check for collections
        cursor.execute("SELECT COUNT(*) FROM collections")
        collection_count = cursor.fetchone()[0]
        logger.info(f"Collection count: {collection_count}")
        
        if collection_count > 0:
            cursor.execute("SELECT name FROM collections")
            collection_names = [row[0] for row in cursor.fetchall()]
            logger.info(f"Collection names: {collection_names}")
        
        # Check for embeddings
        cursor.execute("SELECT COUNT(*) FROM embeddings")
        embeddings_count = cursor.fetchone()[0]
        logger.info(f"Embeddings count: {embeddings_count}")
        
        conn.close()
        
        return {
            "path": db_path,
            "size_mb": size_mb,
            "collection_count": collection_count,
            "embeddings_count": embeddings_count,
            "has_data": collection_count > 0 or embeddings_count > 0
        }
    except Exception as e:
        logger.error(f"Error checking database at {db_path}: {str(e)}")
        return None

def migrate_database(source_path, dest_path, force=False):
    """Migrate ChromaDB from source to destination"""
    if not os.path.exists(source_path):
        logger.error(f"Source path {source_path} does not exist")
        return False
    
    # Create destination directory if it doesn't exist
    os.makedirs(dest_path, exist_ok=True)
    
    # Check if destination already has data
    dest_info = check_db_contents(dest_path)
    if dest_info and dest_info["has_data"] and not force:
        logger.warning(f"Destination {dest_path} already has data. Use --force to overwrite.")
        return False
    
    # Backup destination first if it exists and has a SQLite file
    sqlite_dest = os.path.join(dest_path, "chroma.sqlite3")
    if os.path.exists(sqlite_dest):
        backup_dir = f"{dest_path}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Backing up destination to {backup_dir}")
        try:
            shutil.copytree(dest_path, backup_dir)
            logger.info(f"Backup created at {backup_dir}")
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            return False
    
    # Copy contents from source to destination
    try:
        # Clear destination first
        for item in os.listdir(dest_path):
            item_path = os.path.join(dest_path, item)
            if os.path.isfile(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        
        # Copy source to destination
        for item in os.listdir(source_path):
            s = os.path.join(source_path, item)
            d = os.path.join(dest_path, item)
            if os.path.isfile(s):
                shutil.copy2(s, d)
            elif os.path.isdir(s):
                shutil.copytree(s, d)
        
        logger.info(f"Successfully migrated data from {source_path} to {dest_path}")
        return True
    except Exception as e:
        logger.error(f"Error migrating data: {str(e)}")
        return False

def main():
    """Main function for database migration"""
    logger.info("Starting ChromaDB migration utility")
    
    # Parse command-line arguments
    force = "--force" in sys.argv
    if force:
        logger.warning("Force mode enabled - will overwrite destination if it has data")
    
    # Scan source paths for databases with data
    valid_sources = []
    for path in source_paths:
        logger.info(f"Checking {path}...")
        db_info = check_db_contents(path)
        if db_info and db_info["has_data"]:
            valid_sources.append(db_info)
    
    if not valid_sources:
        logger.error("No valid source databases found with data")
        return
    
    # Sort sources by embeddings count (most data first)
    valid_sources.sort(key=lambda x: x["embeddings_count"], reverse=True)
    
    logger.info(f"Found {len(valid_sources)} potential source databases:")
    for i, source in enumerate(valid_sources):
        logger.info(f"{i+1}. {source['path']} - {source['embeddings_count']} embeddings, {source['collection_count']} collections")
    
    # Check destination
    dest_info = check_db_contents(DEST_PATH)
    if dest_info and dest_info["has_data"]:
        logger.info(f"Destination {DEST_PATH} already has data: {dest_info['embeddings_count']} embeddings, {dest_info['collection_count']} collections")
        if dest_info["embeddings_count"] >= max(s["embeddings_count"] for s in valid_sources):
            logger.info("Destination already has the most data - no migration needed")
            return
    
    # Confirm migration
    source_path = valid_sources[0]["path"]
    logger.info(f"Will migrate from {source_path} to {DEST_PATH}")
    
    if not force:
        confirmation = input(f"Migrate data from {source_path} to {DEST_PATH}? [y/N]: ")
        if confirmation.lower() != 'y':
            logger.info("Migration canceled by user")
            return
    
    # Perform migration
    success = migrate_database(source_path, DEST_PATH, force)
    if success:
        logger.info("Migration completed successfully!")
        check_db_contents(DEST_PATH)  # Check the result
    else:
        logger.error("Migration failed")

if __name__ == "__main__":
    main()