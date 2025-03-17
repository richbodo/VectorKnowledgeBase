# ChromaDB Backup System

## Overview

This application implements a robust backup and persistence system for ChromaDB that ensures data is preserved across Replit restarts and deployments. The system uses Replit's Object Storage for cloud persistence while implementing efficient disk space management for the local filesystem.

## Key Features

1. **Automatic Backups**
   - Automatic backup after document upload if enough time has passed (1 hour interval)
   - Backup rotation limiting historical backups to 24
   - Persistence across Replit restarts and deployments

2. **Disk Space Optimization**
   - Skip local backups during restore when disk space is constrained
   - Cleanup utilities for both local backups and object storage history
   - Efficient storage management to prevent filling quotas

3. **Monitoring and Recovery**
   - Automatic recovery from cloud storage on startup
   - Detailed logging of all backup/restore operations
   - Separate utilities for manual backup and restore

## Usage

### Automatic Operation

The system automatically:
- Restores from object storage on application startup
- Backs up after document uploads (if interval passed)
- Rotates backups to prevent excessive storage usage

### Manual Backup/Restore

```bash
# Manually trigger backup to object storage
python utils/object_storage.py backup

# Restore from object storage (with local backup)
python utils/object_storage.py restore

# Restore without creating local backup (for disk-constrained environments)
python utils/object_storage.py restore --skip-backup
```

### Cleaning Up

```bash
# Clean up local backup directories (keep most recent)
python utils/clean_local_backups.py

# Keep more than 1 recent backup
python utils/clean_local_backups.py --keep 3

# Legacy method (not recommended)
python utils/delete_backup_history.py --force

# NEW RECOMMENDED METHOD: Clean up history with more control
python utils/simple_cleanup.py --dry-run      # Preview what would be deleted
python utils/simple_cleanup.py --force        # Delete old backups, keep 5 most recent
python utils/simple_cleanup.py --force --keep 10  # Keep more recent backups
python utils/simple_cleanup.py --force --limit 50  # Delete in small batches

# Monitor cleanup progress and storage usage
python utils/monitor_cleanup.py
```

## Technical Details

### Backup Locations

- **Local ChromaDB**: `/home/runner/data/chromadb/`
- **Local Backups**: `/home/runner/data/chromadb_local_backup_*`
- **Object Storage**: `chromadb/` prefix in Replit Object Storage
- **History Backups**: `chromadb/history/YYYYMMDD_HHMMSS/` in Object Storage

### Backup Rotation

The system maintains up to 24 historical backups in object storage and automatically cleans up older backups during the backup process.

### Disk Space Management

Each ChromaDB backup is approximately 152MB. The system uses strategies to manage disk space:

1. Skip creating local backups during restore operations with `--skip-backup`
2. Clean local backups with `clean_local_backups.py`
3. Limit historical backups to 24 through automatic rotation

## Troubleshooting

1. **Disk Quota Issues**:
   - Run `python utils/clean_local_backups.py` to remove old local backups
   - Use `--skip-backup` when restoring to avoid creating additional local backups

2. **Data Not Persisting Across Restarts**:
   - Check if Object Storage is enabled for your Replit
   - Verify `main.py` initializes `VectorStore` which triggers the restore

3. **Excessive Storage Usage**:
   - Run `python utils/simple_cleanup.py --force` to clear old backups (recommended)
   - For more control, use options like `--keep-recent` and `--limit`
   - Check if backup rotation is working properly in the logs

## Implementation Files

- `utils/object_storage.py`: Primary backup/restore functionality
- `utils/clean_local_backups.py`: Local backup cleanup utility
- `utils/simple_cleanup.py`: Modern storage history cleanup (recommended)
- `utils/monitor_cleanup.py`: Track cleanup progress and storage usage
- `utils/STORAGE_CLEANUP_README.md`: Detailed cleanup documentation
- `services/vector_store.py`: Integrates backup system with ChromaDB