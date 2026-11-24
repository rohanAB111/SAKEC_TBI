#!/bin/bash
# ==============================================================================
# SAKEC TBI Platform - Automated On-Server Deployment Script
# Target College Server: 172.16.100.31 | User: sakecsandbox
# Developed by Dr. Rohan Appasaheb Borgalli
# ==============================================================================
set -e

APP_DIR="/home/sakecsandbox/sakec-tbi"
DATA_DIR="$APP_DIR/data"
BACKUP_DIR="/home/sakecsandbox/sakec-tbi-backups"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(dirname "$SCRIPT_DIR")"

echo "=================================================================="
echo " Deploying SAKEC TBI Platform on College Server (172.16.100.31)"
echo " Developed by Dr. Rohan Appasaheb Borgalli"
echo "=================================================================="

mkdir -p "$APP_DIR" "$DATA_DIR" "$BACKUP_DIR"

if [ "$SRC_DIR" != "$APP_DIR" ]; then
    cp -r "$SRC_DIR"/* "$APP_DIR/"
fi

chmod +x "$APP_DIR/deploy/"*.sh

echo "[1/5] Initializing SQLite database (WAL mode) with 2024-25 to 2026-27 data..."
SAKEC_DB_PATH="$DATA_DIR/sakec_tbi.db" python3 "$APP_DIR/database.py"

echo "[2/5] Installing systemd service (sakec-tbi.service)..."
sudo cp "$APP_DIR/deploy/sakec-tbi.service" /etc/systemd/system/sakec-tbi.service
sudo systemctl daemon-reload
sudo systemctl enable sakec-tbi.service
sudo systemctl restart sakec-tbi.service

echo "[3/5] Configuring Nginx reverse proxy on Port 80 (if Nginx is installed)..."
if command -v nginx >/dev/null 2>&1; then
    sudo cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/sakec-tbi
    sudo ln -sf /etc/nginx/sites-available/sakec-tbi /etc/nginx/sites-enabled/sakec-tbi
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t && sudo systemctl reload nginx
    echo "Nginx configured! Access at: http://172.16.100.31"
else
    echo "Nginx not installed. Direct access at: http://172.16.100.31:8080"
fi

echo "[4/5] Configuring automated watchdog (2 min) & nightly backup (2 AM)..."
CRON_TMP="/tmp/sakec_tbi_cron"
crontab -l > "$CRON_TMP" 2>/dev/null || true
grep -q "sakec-tbi/deploy/watchdog.sh" "$CRON_TMP" || echo "*/2 * * * * $APP_DIR/deploy/watchdog.sh >> $APP_DIR/watchdog.log 2>&1" >> "$CRON_TMP"
grep -q "sakec-tbi/deploy/backup.sh" "$CRON_TMP" || echo "0 2 * * * $APP_DIR/deploy/backup.sh >> $APP_DIR/backup.log 2>&1" >> "$CRON_TMP"
crontab "$CRON_TMP"
rm -f "$CRON_TMP"

echo "[5/5] Verifying live API response..."
sleep 2
curl -s http://127.0.0.1:8080/api/analytics/portfolio | head -c 300
echo ""
echo "=================================================================="
echo " DEPLOYMENT COMPLETE!"
echo " Direct URL : http://172.16.100.31:8080"
echo " Nginx URL  : http://172.16.100.31"
echo "=================================================================="
