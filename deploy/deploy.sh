#!/bin/bash
# ==============================================================================
# SAKEC Technology Business Incubator (TBI) Automated Server Deployment Script
# Developed by Dr. Rohan Appasaheb Borgalli
# Target: Ubuntu / Debian / RHEL College Server (100% Free, Scalable, Zero-Maintenance)
# ==============================================================================

set -e

echo "=================================================================="
echo " Starting SAKEC TBI Platform Free Automated Server Deployment"
echo " Developed by Dr. Rohan Appasaheb Borgalli"
echo "=================================================================="

INSTALL_DIR="/var/www/sakec-tbi"
DATA_DIR="/var/lib/sakec_tbi"
BACKUP_DIR="/var/backups/sakec_tbi"

echo "[1/7] Verifying prerequisites (Python 3)..."
if ! command -v python3 &> /dev/null; then
    echo "Installing python3..."
    sudo apt update && sudo apt install -y python3 sqlite3 curl
fi

echo "[2/7] Creating system directories..."
sudo mkdir -p "$INSTALL_DIR"
sudo mkdir -p "$DATA_DIR"
sudo mkdir -p "$BACKUP_DIR"
sudo mkdir -p "/var/log"

echo "[3/7] Copying application assets..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="$(dirname "$SCRIPT_DIR")"

sudo cp "$APP_ROOT/server.py" "$INSTALL_DIR/"
sudo cp "$APP_ROOT/database.py" "$INSTALL_DIR/"
sudo cp "$APP_ROOT/simulator.py" "$INSTALL_DIR/"
sudo cp -r "$APP_ROOT/static" "$INSTALL_DIR/"
sudo cp -r "$APP_ROOT/deploy" "$INSTALL_DIR/"

echo "[4/7] Initializing SQLite database with WAL mode & SAKEC seed data..."
sudo SAKEC_DB_PATH="$DATA_DIR/sakec_tbi.db" python3 "$INSTALL_DIR/database.py"

echo "[5/7] Configuring system permissions..."
sudo chown -R www-data:www-data "$INSTALL_DIR"
sudo chown -R www-data:www-data "$DATA_DIR"
sudo chmod -R 775 "$DATA_DIR"

echo "[6/7] Installing systemd daemon and log rotation..."
sudo cp "$INSTALL_DIR/deploy/sakec-tbi.service" /etc/systemd/system/
sudo cp "$INSTALL_DIR/deploy/logrotate.conf" /etc/logrotate.d/sakec-tbi
sudo systemctl daemon-reload
sudo systemctl enable sakec-tbi.service
sudo systemctl restart sakec-tbi.service

echo "[7/7] Setting up automated zero-maintenance cron jobs (Watchdog & Backups)..."
# Add watchdog (every 2 mins) and daily backup (2:00 AM) to crontab if not present
CRON_TMP="/tmp/sakec_cron"
sudo crontab -l > "$CRON_TMP" 2>/dev/null || true
if ! grep -q "sakec_tbi/deploy/watchdog.sh" "$CRON_TMP"; then
    echo "*/2 * * * * $INSTALL_DIR/deploy/watchdog.sh >> /var/log/sakec_tbi_watchdog.log 2>&1" >> "$CRON_TMP"
fi
if ! grep -q "sakec_tbi/deploy/backup.sh" "$CRON_TMP"; then
    echo "0 2 * * * $INSTALL_DIR/deploy/backup.sh >> /var/log/sakec_tbi_backup.log 2>&1" >> "$CRON_TMP"
fi
sudo crontab "$CRON_TMP"
rm -f "$CRON_TMP"

echo ""
echo "=================================================================="
echo " SAKEC TBI Platform Successfully Deployed!"
echo " Status: $(systemctl is-active sakec-tbi.service)"
echo " Listening on http://0.0.0.0:8080"
echo " High-Concurrency Mode: SQLite WAL Mode Active"
echo " Maintenance: Automated Self-Healing Watchdog + Daily Rolling Backups"
echo " Developed by Dr. Rohan Appasaheb Borgalli"
echo "=================================================================="
