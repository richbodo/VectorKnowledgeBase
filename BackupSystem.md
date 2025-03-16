# Vector Database Backup System

## Overview
This document describes the backup and restore system for the ChromaDB vector database used in our PDF document processing service. The system utilizes Replit's Object Storage to ensure data persistence across application restarts and deployments.

## Core Principles
The backup system follows three fundamental rules:

1. **Restore on Start**: Restore the most recent backup from object storage when the application starts to ensure data persistence.
2. **Backup on Upload**: Create a new backup when data is added to the database through the `/upload` endpoint, but only if at least one hour has passed since the last backup.
3. **Limit Backup Count**: Maintain no more than 24 historical backups (one for each hour of the day) to optimize storage usage.

## Object Storage Structure
The backup system uses Replit's Object Storage with the following directory structure:

```
chromadb/
├── chroma.sqlite3         # Current database snapshot
├── backup_manifest.json   # Metadata about the latest backup
└── history/
    ├── YYYYMMDD_HHMMSS/   # Timestamped backup directories
    │   ├── chroma.sqlite3
    │   └── ...
    └── ...
```

### Backup Manifest
The backup manifest (`backup_manifest.json`) stores metadata about the latest backup:

```json
{
  "timestamp": "ISO-8601 formatted date-time",
  "files": ["chroma.sqlite3", "..."],
  "version": "1.0"
}
```

## Backup Algorithm Details

### 1. Restoration Process
During application initialization, the system:
- Checks for the existence of a backup manifest in object storage
- If found, compares the timestamp of local and stored databases
- Restores from object storage if the stored version is newer or if no local database exists
- Does NOT create a new backup during initialization

### 2. Backup Process
When data is added to the database via the `/upload` endpoint:
- Checks if at least one hour has passed since the last backup
- If so, creates a backup in both the main location and in a timestamped history folder
- Updates the backup manifest with the new timestamp
- Sets the `_last_backup_time` to the current time

### 3. Backup Rotation
To maintain the 24-backup limit:
- Rotation is performed automatically as part of each successful backup process
- The system lists all existing backup directories in the `chromadb/history/` path
- It sorts them by timestamp (newest first)
- It keeps the 24 most recent backups and deletes all older ones
- This approach ensures we maintain exactly the intended number of historical backups without requiring a separate scheduling mechanism
- Rotation only happens when backups are successfully created

## Implementation Details

### Key Classes and Methods

#### `ChromaObjectStorage` (utils/object_storage.py)
- `backup_to_object_storage()`: Creates a backup in object storage
- `restore_from_object_storage()`: Restores from object storage
- `_rotate_backups()`: Ensures only 24 historical backups are kept
- `_fetch_manifest()`: Retrieves the backup manifest

#### `VectorStore` (services/vector_store.py)
- `_schedule_backup()`: Checks if enough time has passed for a backup
- `_execute_backup()`: Performs the actual backup operation
- `add_document()`: Triggers backup scheduling after adding documents

## Performance Considerations
- Backups are only performed after data additions, not during reads or application startup
- The one-hour interval prevents excessive backups during bulk uploads
- Historical backups are limited to 24 to control storage usage
- Backup operations are lightweight and non-blocking to maintain application responsiveness

## Monitoring and Troubleshooting
- All backup and restore operations are logged with appropriate log levels
- Success/failure status is returned from all operations
- The backup manifest provides a reliable way to verify the latest backup timestamp

## Future Improvements
- Consider implementing incremental backups for very large databases
- Add backup integrity verification
- Implement notification system for backup failures
- Consider environment-specific backup configurations

## Security Considerations
- Backups are stored within Replit's secure Object Storage
- No sensitive user data is stored in the backup manifest
- Backup operations don't expose sensitive information in logs