#!/bin/bash
# Automated SQLite Hot Backup for SAKEC TBI Platform (172.16.100.31)
BACKUP_DIR="/home/sakecsandbox/sakec-tbi-backups"
DB_FILE="/home/sakecsandbox/sakec-tbi/data/sakec_tbi.db"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p "$BACKUP_DIR"

if [ -f "$DB_FILE" ]; then
    python3 -c "import sqlite3; src=sqlite3.connect('$DB_FILE'); dst=sqlite3.connect('$BACKUP_DIR/sakec_tbi_$TIMESTAMP.db'); src.backup(dst); dst.close(); src.close()"
    tar -czf "$BACKUP_DIR/sakec_tbi_$TIMESTAMP.tar.gz" -C "$BACKUP_DIR" "sakec_tbi_$TIMESTAMP.db"
    rm -f "$BACKUP_DIR/sakec_tbi_$TIMESTAMP.db"
    find "$BACKUP_DIR" -type f -name "sakec_tbi_*.tar.gz" -mtime +30 -delete
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup saved: $BACKUP_DIR/sakec_tbi_$TIMESTAMP.tar.gz"
fi
