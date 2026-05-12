#!/bin/bash
set -e

echo "Stopping emulationstation..."
sudo systemctl stop emulationstation
sudo pkill -9 -f emulationstation || true

echo "Killing old browser instances..."
pkill -9 -f browser.py || true

echo "Setting environment variables..."
export TERM=linux
export XDG_RUNTIME_DIR=/run/user/$(id -u)
export QT_QPA_PLATFORM=eglfs

echo "Launching browser..."
# Use tee so output goes to both the physical TTY (for DRM) and the SSH session
PYTHONUNBUFFERED=1 python3 /home/ark/browser.py < /dev/tty1 2>&1 | tee /dev/tty1
