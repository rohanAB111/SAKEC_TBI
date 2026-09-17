#!/bin/bash
# ==============================================================================
# SAKEC Technology Business Incubator (TBI) Database Backup & Rotation Script
# Developed by Dr. Rohan Appasaheb Borgalli
# ==============================================================================

BACKUP_DIR="/var/backups/sakec_tbi"
DATA_DIR="/var/lib/sakec_tbi"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/sakec_tbi_backup_$TIMESTAMP.tar.gz"

mkdir -p "$BACKUP_DIR"

if [ -f "$DATA_DIR/sakec_tbi.db" ]; then
    echo "Creating SQLite snapshot..."
    sqlite3 "$DATA_DIR/sakec_tbi.db" ".backup '$BACKUP_DIR/snapshot_$TIMESTAMP.db'"
    tar -czf "$BACKUP_FILE" -C "$BACKUP_DIR" "snapshot_$TIMESTAMP.db"
    rm "$BACKUP_DIR/snapshot_$TIMESTAMP.db"
    echo "Backup completed: $BACKUP_FILE"
else
    echo "No database found at $DATA_DIR/sakec_tbi.db"
fi

# Rotate backups older than 30 days
find "$BACKUP_DIR" -type f -name "sakec_tbi_backup_*.tar.gz" -mtime +30 -delete
