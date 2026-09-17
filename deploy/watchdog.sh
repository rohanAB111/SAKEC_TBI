#!/bin/bash
# ==============================================================================
# SAKEC TBI Platform - Self-Healing Watchdog Daemon
# Developed by Dr. Rohan Appasaheb Borgalli
# Checks health every 2 minutes; auto-recovers and alerts if unresponsive
# ==============================================================================

ENDPOINT="http://127.0.0.1:8080/api/analytics/portfolio"
LOG_FILE="/var/log/sakec_tbi_watchdog.log"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Check HTTP status with 5-second timeout
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$ENDPOINT" || echo "000")

if [ "$HTTP_STATUS" != "200" ]; then
    echo "[$TIMESTAMP] ALERT: SAKEC TBI service unresponsive (HTTP $HTTP_STATUS). Initiating automatic recovery..." >> "$LOG_FILE"
    
    # Restart the systemd service
    sudo systemctl restart sakec-tbi.service
    sleep 3
    
    # Verify post-restart status
    NEW_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$ENDPOINT" || echo "000")
    if [ "$NEW_STATUS" == "200" ]; then
        echo "[$TIMESTAMP] RECOVERY: SAKEC TBI service restored successfully." >> "$LOG_FILE"
    else
        echo "[$TIMESTAMP] CRITICAL: Recovery failed. Manual inspection required." >> "$LOG_FILE"
    fi
fi
