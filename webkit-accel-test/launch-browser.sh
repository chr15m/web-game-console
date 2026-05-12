#!/bin/bash
set -e

echo "Stopping emulationstation..."
sudo systemctl stop emulationstation
sudo pkill -9 -f emulationstation || true

echo "Setting environment variables..."
export TERM=linux
export XDG_RUNTIME_DIR=/run/user/$(id -u)
export QT_QPA_PLATFORM=eglfs

echo "Launching browser..."
python3 /home/ark/browser.py < /dev/tty1 > /dev/tty1 2>&1
