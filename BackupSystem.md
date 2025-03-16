# ChromaDB Backup System

## Overview

This document describes the automatic backup and persistence system for ChromaDB data in our application. The system is designed to prevent data loss during Replit redeployments and ensure smooth application operation.

## Backup Rules

The backup system follows three simple core rules:

1. **Restore Last State on Start**: When the application starts, it automatically restores the most recent ChromaDB backup from object storage if the local database is missing or older.

2. **Save After Important Operations**: The system automatically creates a backup after document uploads when sufficient time has passed since the last backup (currently set to 1 hour).

3. **Maintain Backup History**: The system maintains a history of backups (maximum 24) with automatic rotation of older backups.

## Key Components

### ChromaObjectStorage (utils/object_storage.py)

This class handles all interactions with Replit Object Storage:

- **Backup**: Copies the local ChromaDB directory to object storage
- **Restore**: Retrieves ChromaDB data from object storage to local filesystem
- **Sync**: Bidirectional synchronization based on timestamps
- **Rotation**: Maintains a limited number of historical backups (24)

### VectorStore (services/vector_store.py)

The VectorStore class integrates with the backup system:

- **Scheduling**: After document uploads, it schedules backups based on a time interval
- **Execution**: Performs the actual backup operation when needed
- **State Management**: Tracks when backups are needed

## Storage Structure

Data in Replit Object Storage is organized as follows:

- **Current Files**: `chromadb/[filename]` - Latest versions of all ChromaDB files
- **History**: `chromadb/history/[timestamp]/[filename]` - Historical versions for recovery
- **Manifest**: `chromadb/manifest.json` - Information about the most recent backup

## Backup Interval

- The system waits **1 hour** between backups to prevent excessive storage operations
- This interval is defined in `VectorStore._backup_interval`

## Historical Backup Management

- Maximum 24 historical backups are maintained
- Older backups are automatically deleted during rotation
- The rotation happens immediately after a new backup is created

## Manual Operations

Several utility scripts are available for manual operations:

1. **utils/object_storage.py**: CLI tool for backup, restore, and sync operations
2. **utils/clear_history_backups.py**: Utility to clear all historical backups

## Recovery Process

If database loss occurs:

1. Application will automatically detect missing or outdated local database
2. It will restore from the most recent object storage backup on startup
3. If automatic recovery fails, manual restoration can be performed using the CLI tools

## Disk Space Management

The system includes features to handle disk quota limitations:

1. **Skip Local Backup Option**: When restoring, local backups can be skipped to conserve disk space
2. **Automatic Recovery**: If disk quota errors occur during restore, the system attempts recovery by skipping local backups
3. **CLI Support**: The command-line tool supports a `--skip-backup` flag for constrained environments
4. **Error Resilience**: Graceful error handling with detailed logging helps diagnose space issues

Example CLI usage in disk-constrained environments:
```bash
python utils/object_storage.py restore --skip-backup
```

## Monitoring

Backup operations are logged with detailed information:
- Success/failure status
- Timestamp
- Files affected
- Rotation statistics
- Disk space diagnostics