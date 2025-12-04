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
for keyfile in ~/.ssh/id_rsa.pub ~/.ssh/id_ed25519.pub ~/.ssh/id_ecdsa.pub; do
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

echo "Connecting via SSH..."
ssh $SSH_OPTS ark@$HOST "echo 'Connected.'"

echo "Setting up SSH authorized_keys..."
ssh $SSH_OPTS ark@$HOST "mkdir -p ~/.ssh && chmod 700 ~/.ssh"
ssh $SSH_OPTS ark@$HOST "grep -qF '$PUBKEY' ~/.ssh/authorized_keys 2>/dev/null || echo '$PUBKEY' >> ~/.ssh/authorized_keys"
ssh $SSH_OPTS ark@$HOST "chmod 600 ~/.ssh/authorized_keys"

echo "Adding ark user to tty, video, and input groups..."
ssh $SSH_OPTS ark@$HOST "sudo usermod -a -G tty,video,input ark"

echo "Setting tty permissions for X..."
ssh $SSH_OPTS ark@$HOST "sudo chmod 666 /dev/tty0 /dev/tty2"

echo "Checking apt cache age..."
APT_UPDATE_NEEDED=$(ssh $SSH_OPTS ark@$HOST '
    cache=/var/cache/apt/pkgcache.bin
    if [ -f "$cache" ]; then
        age=$(($(date +%s) - $(stat -c %Y "$cache")))
        if [ $age -lt 2592000 ]; then
            echo "no"
        else
            echo "yes"
        fi
    else
        echo "yes"
    fi
')

if [ "$APT_UPDATE_NEEDED" = "yes" ]; then
    echo "Updating apt repos..."
    ssh $SSH_OPTS ark@$HOST "sudo apt-get update -qq"
else
    echo "Apt cache is fresh (less than 30 days old), skipping update."
fi

echo "Ensuring xorg is installed..."
ssh $SSH_OPTS ark@$HOST "sudo apt-get install -y xorg"

echo "Installing Mali driver..."
rsync -e "ssh $SSH_OPTS" --checksum "$SCRIPT_DIR/driver/mali_drv.so" ark@$HOST:/tmp/
rsync -e "ssh $SSH_OPTS" --checksum "$SCRIPT_DIR/driver/99-mali.conf" ark@$HOST:/tmp/
ssh $SSH_OPTS ark@$HOST "sudo cp /tmp/mali_drv.so /usr/lib/xorg/modules/drivers/ && \
    sudo mkdir -p /etc/X11/xorg.conf.d && \
    sudo cp /tmp/99-mali.conf /etc/X11/xorg.conf.d/ && \
    sudo cp /tmp/99-mali.conf /usr/share/X11/xorg.conf.d/"

echo "Configuring Xwrapper to allow non-root users..."
ssh $SSH_OPTS ark@$HOST "echo 'allowed_users=anybody' | sudo tee /etc/X11/Xwrapper.config > /dev/null"

echo "Installing surf browser..."
ssh $SSH_OPTS ark@$HOST "sudo apt-get install -y surf"

echo "Installing matchbox window manager..."
ssh $SSH_OPTS ark@$HOST "sudo apt-get install -y matchbox-window-manager"

echo "Installing unclutter..."
ssh $SSH_OPTS ark@$HOST "sudo apt-get install -y unclutter"

echo "Installing xdotool..."
ssh $SSH_OPTS ark@$HOST "sudo apt-get install -y xdotool"

echo "Copying index.html..."
rsync -e "ssh $SSH_OPTS" --checksum "$SCRIPT_DIR/index.html" ark@$HOST:/home/ark/

echo "Copying xinitrc..."
rsync -e "ssh $SSH_OPTS" --checksum "$SCRIPT_DIR/xinitrc" ark@$HOST:/home/ark/.xinitrc

echo "Copying launch.sh..."
rsync -e "ssh $SSH_OPTS" --checksum "$SCRIPT_DIR/launch.sh" ark@$HOST:/home/ark/

echo "Copying joy-keys-hack.sh..."
rsync -e "ssh $SSH_OPTS" --checksum "$SCRIPT_DIR/joy-keys-hack.sh" ark@$HOST:/home/ark/

echo "Done."
