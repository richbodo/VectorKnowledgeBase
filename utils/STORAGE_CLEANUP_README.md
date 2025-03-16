# ChromaDB Storage Cleanup Utilities

This directory contains utilities for cleaning up ChromaDB history files stored in Replit Object Storage. These tools help reduce storage usage by removing old backups while maintaining system functionality.

## Quick Reference

### Monitor Storage Usage

```bash
python utils/monitor_cleanup.py
```

This shows current storage statistics, including:
- Total backup directories
- Estimated storage usage
- Newest and oldest backup timestamps

### Clean Up History Files (With Limits)

```bash
python utils/simple_cleanup.py --force --limit 50
```

This deletes 50 history files at a time, preserving the 5 most recent backups.

### Clean Up All History Files

```bash
python utils/simple_cleanup.py --force
```

This deletes all history files except the 5 most recent backups.

### Test Without Deleting

```bash
python utils/simple_cleanup.py --dry-run
```

Shows what would be deleted without making any changes.

## Detailed Usage

### simple_cleanup.py

This is the primary cleanup tool. It directly accesses Replit Object Storage to delete history files while preserving recent backups.

Options:
- `--force`: Skip confirmation prompt and delete files
- `--dry-run`: Test the cleanup without actually deleting files
- `--limit N`: Limit deletion to N files (for controlled batch cleanup)
- `--keep N`: Keep the N most recent backups (default: 5)

Examples:

```bash
# Delete 100 oldest history files
python utils/simple_cleanup.py --force --limit 100

# Delete all history files except the 10 most recent
python utils/simple_cleanup.py --force --keep 10

# Show what would be deleted without making changes
python utils/simple_cleanup.py --dry-run
```

### monitor_cleanup.py

This tool provides insights into the current state of ChromaDB storage. It helps track cleanup progress and verify results.

```bash
python utils/monitor_cleanup.py
```

The script also saves progress history to `cleanup_progress.json` for tracking changes over time.

### delete_one_history_file.py

This is a minimal utility for testing deletion of a single file. Useful for verifying access to object storage.

```bash
python utils/delete_one_history_file.py
```

## Best Practices

1. Always run with `--dry-run` first to see what will be deleted
2. Start with small batches (`--limit 50`) to verify the process works
3. Monitor storage after each batch using `monitor_cleanup.py`
4. Keep at least 5 recent backups (`--keep 5`) for safety
5. Run cleanup during low-traffic periods

## Troubleshooting

If you encounter errors:

1. Check Replit Object Storage access
2. Verify that ChromaDB is not actively being written to
3. Check permissions for the running process
4. Look for detailed error messages in the logs