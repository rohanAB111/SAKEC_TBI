#!/bin/bash
# Self-Healing Watchdog for SAKEC TBI Platform (172.16.100.31)
ENDPOINT="http://127.0.0.1:8080/api/analytics/portfolio"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$ENDPOINT" || echo "000")
if [ "$HTTP_STATUS" != "200" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ALERT: HTTP $HTTP_STATUS - restarting sakec-tbi.service"
    sudo systemctl restart sakec-tbi.service
fi
