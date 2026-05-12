#!/bin/bash
set -e

IP=${1:-192.168.50.86}
USER="ark"

echo "Deploying to $USER@$IP..."
scp browser.py launch-browser.sh index.html $USER@$IP:/home/ark/

echo "Launching on device..."
ssh $USER@$IP "chmod +x /home/ark/launch-browser.sh && /home/ark/launch-browser.sh"
