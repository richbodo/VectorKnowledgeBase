#!/usr/bin/env python3
"""
Utility to check for potential code that could be resetting the ChromaDB database.
This scans the codebase for patterns that might indicate problematic operations.
"""

import os
import re
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("db_reset_checker")

def find_potential_reset_patterns():
    """Scan codebase for patterns that might reset the database"""
    patterns = [
        r"client\.reset\(",  # Explicit reset calls
        r"\.reset\(\)",      # Any reset method calls
        r"allow_reset=True",  # Settings that allow resets
        r"persist\(\)",      # Manual persist calls (might indicate incorrect persistence)
        r"delete_collection\(",  # Deleting collections
        r"delete\(",         # General delete operations
        r"reset_collection",  # Functions that might reset collections
        r"wipe_",            # Functions that wipe data
        r"clear\(",          # Clear methods
        r"drop\(",           # Drop methods
        r"purge\(",          # Purge methods
        r"recreate\(",       # Recreate methods
        r"reinitialize\("    # Reinitialize methods
    ]
    
    # Skip directories that aren't relevant or contain too many false positives
    skip_dirs = [
        ".git", 
        "__pycache__", 
        "node_modules", 
        "venv",
        ".venv", 
        "build",
        "dist",
        "chroma_db_backup",
    ]
    
    found_issues = []
    
    # Start from the current working directory
    root_dir = os.getcwd()
    logger.info(f"Scanning directory: {root_dir}")
    
    for root, dirs, files in os.walk(root_dir):
        # Skip directories that should be excluded
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            # Only check Python files
            if not file.endswith('.py'):
                continue
                
            file_path = os.path.join(root, file)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Check for each pattern in the file content
                    for pattern in patterns:
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            # Get some context around the match (line number and the line itself)
                            line_num = content[:match.start()].count('\n') + 1
                            line_content = content.split('\n')[line_num - 1].strip()
                            rel_path = os.path.relpath(file_path, root_dir)
                            
                            issue = {
                                'file': rel_path,
                                'line': line_num,
                                'pattern': pattern,
                                'content': line_content
                            }
                            found_issues.append(issue)
                            logger.warning(f"Potential issue in {rel_path}:{line_num} - {line_content}")
            except Exception as e:
                logger.error(f"Error reading {file_path}: {str(e)}")
    
    return found_issues

def check_db_files():
    """Check for the presence and state of ChromaDB files"""
    # Common ChromaDB storage locations
    db_paths = [
        "/home/runner/data/chromadb",  # Our preferred location
        "/home/runner/.cache/chromadb",
        "/home/runner/workspace/.cache/chromadb",
        "chroma_db",
        os.path.join(os.getcwd(), "chroma_db"),
        os.path.join(os.getcwd(), ".cache", "chromadb")
    ]
    
    found_dbs = []
    
    for path in db_paths:
        if os.path.exists(path):
            try:
                size = 0
                file_count = 0
                
                if os.path.isdir(path):
                    for root, _, files in os.walk(path):
                        for f in files:
                            file_path = os.path.join(root, f)
                            size += os.path.getsize(file_path)
                            file_count += 1
                    
                    sqlite_path = os.path.join(path, "chroma.sqlite3")
                    sqlite_exists = os.path.exists(sqlite_path)
                    sqlite_size = os.path.getsize(sqlite_path) if sqlite_exists else 0
                    
                    db_info = {
                        'path': path,
                        'size_mb': round(size / (1024 * 1024), 2),
                        'file_count': file_count,
                        'sqlite_exists': sqlite_exists,
                        'sqlite_size_mb': round(sqlite_size / (1024 * 1024), 2) if sqlite_exists else 0
                    }
                    found_dbs.append(db_info)
                    logger.info(f"Found DB at {path}, size: {db_info['size_mb']} MB, files: {file_count}")
            except Exception as e:
                logger.error(f"Error checking {path}: {str(e)}")
    
    return found_dbs

def main():
    """Main function to run the checks"""
    logger.info("Starting database reset issue detection")
    
    # Check for patterns that might cause resets
    logger.info("Checking for code patterns that might reset the database...")
    issues = find_potential_reset_patterns()
    
    if issues:
        logger.warning(f"Found {len(issues)} potential issues that might cause database resets")
        print("\n--- Potential Database Reset Issues ---")
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue['file']}:{issue['line']} - {issue['content']}")
    else:
        print("No obvious database reset patterns found in the code.")
    
    # Check for database files
    logger.info("Checking for ChromaDB database files...")
    dbs = check_db_files()
    
    if dbs:
        print("\n--- Found ChromaDB Databases ---")
        for i, db in enumerate(dbs, 1):
            print(f"{i}. {db['path']}")
            print(f"   Size: {db['size_mb']} MB, Files: {db['file_count']}")
            if db['sqlite_exists']:
                print(f"   SQLite: {db['sqlite_size_mb']} MB")
    else:
        print("No ChromaDB database files found on disk.")
    
    # Final advice
    print("\n--- Recommendations ---")
    if issues:
        print("⚠️ Check the identified patterns in your code that might be causing database resets")
    if len(dbs) > 1:
        print("⚠️ Multiple ChromaDB databases found. This could cause confusion about which one is active.")
        print("   Ensure your application is using the correct persistent path.")
    elif not dbs:
        print("⚠️ No ChromaDB database found. This suggests data isn't being persisted properly.")
    
    print("\nThe most reliable persistent location on Replit is: /home/runner/data/chromadb")
    print("Make sure your application is configured to use this path and has permission to write to it.")

if __name__ == "__main__":
    main()