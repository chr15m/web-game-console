#!/bin/bash
set -e

IP=${1:-192.168.50.86}
USER="ark"

echo "Deploying to $USER@$IP..."
scp browser.py launch-browser.sh *.html *.css *.js $USER@$IP:/home/ark/r36s-web-console/webkit-accel-test/

echo "Launching on device..."
echo "Remote debugging will be available at http://localhost:9222"
ssh -L 9222:localhost:9222 $USER@$IP "sudo systemctl restart web-console && echo 'Web console restarted. Press Ctrl+C to close tunnel.' && sleep infinity"
