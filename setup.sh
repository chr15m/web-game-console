#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <host>"
    exit 1
fi

HOST="$1"
SCRIPT_DIR=$(dirname "$(realpath "$0")")
SSH_OPTS="-o ControlMaster=auto -o ControlPath=/tmp/ssh-%r@%h:%p -o ControlPersist=60"

echo "Updating apt repos..."
ssh $SSH_OPTS ark@$HOST "sudo apt-get update -qq"

echo "Ensuring xorg is installed..."
ssh $SSH_OPTS ark@$HOST "sudo apt-get install -y xorg"

echo "Installing Mali driver..."
scp $SSH_OPTS "$SCRIPT_DIR/driver/mali_drv.so" ark@$HOST:/tmp/
scp $SSH_OPTS "$SCRIPT_DIR/driver/99-mali.conf" ark@$HOST:/tmp/
ssh $SSH_OPTS ark@$HOST "sudo cp /tmp/mali_drv.so /usr/lib/xorg/modules/drivers/ && \
    sudo mkdir -p /etc/X11/xorg.conf.d && \
    sudo cp /tmp/99-mali.conf /etc/X11/xorg.conf.d/ && \
    sudo cp /tmp/99-mali.conf /usr/share/X11/xorg.conf.d/"

echo "Installing Chromium..."
ssh $SSH_OPTS ark@$HOST "sudo apt-get install -y chromium-browser"

echo "Done."
