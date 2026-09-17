#!/bin/bash
# ==============================================================================
# SAKEC TBI Platform - Free Zero-Trust Cloudflare Tunnel Setup
# Developed by Dr. Rohan Appasaheb Borgalli
# Provides 100% FREE Public HTTPS access without public IP or router port forwarding
# ==============================================================================

echo "======================================================================"
echo " Cloudflare Tunnel - Free Secure Ingress for SAKEC College Server"
echo " Developed by Dr. Rohan Appasaheb Borgalli"
echo "======================================================================"

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "Installing free cloudflared binary..."
    curl -L --output /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    sudo dpkg -i /tmp/cloudflared.deb
    rm /tmp/cloudflared.deb
fi

echo ""
echo "Choose deployment mode:"
echo " 1) Instant Quick Tunnel (Free randomized URL: https://xxxx.trycloudflare.com)"
echo " 2) Custom College Domain Tunnel (e.g., https://tbi.sakec.ac.in)"
read -p "Select option (1 or 2): " OPTION

if [ "$OPTION" == "1" ]; then
    echo "Launching Quick Tunnel on port 8080..."
    cloudflared tunnel --url http://127.0.0.1:8080
else
    echo "To configure your custom domain (tbi.sakec.ac.in):"
    echo " 1. Run: cloudflared tunnel login"
    echo " 2. Run: cloudflared tunnel create sakec-tbi"
    echo " 3. Route domain: cloudflared tunnel route dns sakec-tbi tbi.sakec.ac.in"
    echo " 4. Run tunnel: cloudflared tunnel run sakec-tbi"
fi
