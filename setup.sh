#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <host>"
    exit 1
fi

HOST="$1"
SCRIPT_DIR=$(dirname "$(realpath "$0")")
SSH_OPTS="-o ControlMaster=auto -o ControlPath=/tmp/ssh-%r@%h:%p -o ControlPersist=60"

# Find available SSH public key
PUBKEY=""
for keyfile in ~/.ssh/id_ed25519.pub ~/.ssh/id_rsa.pub ~/.ssh/id_ecdsa.pub; do
    if [ -f "$keyfile" ]; then
        PUBKEY=$(cat "$keyfile")
        echo "Using SSH key: $keyfile"
        break
    fi
done

if [ -z "$PUBKEY" ]; then
    echo "No SSH public key found in ~/.ssh/"
    exit 1
fi

echo "Setting up SSH authorized_keys..."
ssh $SSH_OPTS ark@$HOST "mkdir -p ~/.ssh && chmod 700 ~/.ssh"
ssh $SSH_OPTS ark@$HOST "grep -qF '$PUBKEY' ~/.ssh/authorized_keys 2>/dev/null || echo '$PUBKEY' >> ~/.ssh/authorized_keys"
ssh $SSH_OPTS ark@$HOST "chmod 600 ~/.ssh/authorized_keys"

echo "Updating apt repos..."
ssh $SSH_OPTS ark@$HOST "sudo apt-get update -qq"

echo "Ensuring xorg is installed..."
ssh $SSH_OPTS ark@$HOST "sudo apt-get install -y xorg"

echo "Installing Mali driver..."
rsync -e "ssh $SSH_OPTS" --checksum "$SCRIPT_DIR/driver/mali_drv.so" ark@$HOST:/tmp/
rsync -e "ssh $SSH_OPTS" --checksum "$SCRIPT_DIR/driver/99-mali.conf" ark@$HOST:/tmp/
ssh $SSH_OPTS ark@$HOST "sudo cp /tmp/mali_drv.so /usr/lib/xorg/modules/drivers/ && \
    sudo mkdir -p /etc/X11/xorg.conf.d && \
    sudo cp /tmp/99-mali.conf /etc/X11/xorg.conf.d/ && \
    sudo cp /tmp/99-mali.conf /usr/share/X11/xorg.conf.d/"

echo "Installing surf browser..."
ssh $SSH_OPTS ark@$HOST "sudo apt-get install -y surf"

echo "Copying index.html..."
rsync -e "ssh $SSH_OPTS" --checksum "$SCRIPT_DIR/index.html" ark@$HOST:/home/ark/

echo "Done."
