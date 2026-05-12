#!/bin/bash
set -e

echo "Stopping gdm3..."
sudo systemctl stop gdm3

echo "Setting tty permissions..."
sudo chmod 666 /dev/tty0 /dev/tty2

echo "Killing emulationstation..."
pkill emulationstation || true

echo "Starting X..."
startx
