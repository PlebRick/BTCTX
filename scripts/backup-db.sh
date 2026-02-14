#!/usr/bin/env bash
#
# Daily SQLite backup for BTCTX production database.
# Uses sqlite3 .backup for a safe online copy (handles WAL mode).
# Keeps 60 days of dated backups, then prunes older ones.
#

set -euo pipefail

PROJECT_DIR="/home/ubuntu76/Projects/BTCTX-org"
DB_PATH="$PROJECT_DIR/backend/bitcoin_tracker.db"
BACKUP_DIR="$PROJECT_DIR/backups"
KEEP_DAYS=60

DATE=$(date +%Y-%m-%d)
BACKUP_FILE="$BACKUP_DIR/btctx_${DATE}.db"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Skip if DB doesn't exist
if [ ! -f "$DB_PATH" ]; then
    echo "$(date -Iseconds) ERROR: Database not found at $DB_PATH" >&2
    exit 1
fi

# Safe online backup via sqlite3
sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"

echo "$(date -Iseconds) Backed up to $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"

# Prune backups older than KEEP_DAYS
find "$BACKUP_DIR" -name "btctx_*.db" -mtime +$KEEP_DAYS -delete -print | while read f; do
    echo "$(date -Iseconds) Pruned old backup: $f"
done
