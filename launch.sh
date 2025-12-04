#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <host>"
    exit 1
fi

HOST="$1"
SSH_OPTS="-o ControlMaster=auto -o ControlPath=/tmp/ssh-%r@%h:%p -o ControlPersist=60"

echo "Stopping gdm3..."
ssh $SSH_OPTS ark@$HOST "sudo systemctl stop gdm3"

echo "Setting tty permissions..."
ssh $SSH_OPTS ark@$HOST "sudo chmod 666 /dev/tty0 /dev/tty2"

echo "Killing emulationstation..."
ssh $SSH_OPTS ark@$HOST "pkill emulationstation || true"

echo "Starting X..."
ssh $SSH_OPTS ark@$HOST "startx"
