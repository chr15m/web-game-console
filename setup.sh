#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <host>"
    exit 1
fi

HOST="$1"
SCRIPT_DIR=$(dirname "$(realpath "$0")")
SSH_OPTS="-o ControlMaster=auto -o ControlPath=/tmp/ssh-%r@%h:%p -o ControlPersist=60"
REPO_URL=$(git config --get remote.origin.url || echo "https://github.com/chr15m/web-game-console.git")

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

echo "Ensuring Git, PyQt5 WebEngine and Emoji fonts are installed..."
ssh $SSH_OPTS ark@$HOST "sudo apt-get install -y git python3-pyqt5.qtwebengine fonts-noto-color-emoji"

echo "Enabling SSH to start on boot..."
ssh $SSH_OPTS ark@$HOST "sudo systemctl enable ssh"

if [ -f "$SCRIPT_DIR/repo-ro-key" ]; then
    echo "Installing read-only deploy key for GitHub..."
    KEY_FILE="$SCRIPT_DIR/repo-ro-key"
    rsync -e "ssh $SSH_OPTS" --checksum "$KEY_FILE" ark@$HOST:~/.ssh/repo-ro-key
    ssh $SSH_OPTS ark@$HOST "chmod 600 ~/.ssh/repo-ro-key"
    ssh $SSH_OPTS ark@$HOST "touch ~/.ssh/config && chmod 600 ~/.ssh/config"
    ssh $SSH_OPTS ark@$HOST "grep -q 'IdentityFile ~/.ssh/repo-ro-key' ~/.ssh/config || echo -e 'Host github.com\n  IdentityFile ~/.ssh/repo-ro-key\n  StrictHostKeyChecking no\n' >> ~/.ssh/config"
    
    # Force SSH URL so the deploy key is actually used
    REPO_URL="git@github.com:chr15m/web-game-console.git"
fi

echo "Migrating legacy files and cloning repository..."
ssh $SSH_OPTS ark@$HOST "
    if ls /home/ark/browser.py 1> /dev/null 2>&1; then
        BACKUP_DIR=\"/home/ark/legacy_backup_\$(date +%s)\"
        mkdir -p \"\$BACKUP_DIR\"
        mv /home/ark/browser.py /home/ark/*.html /home/ark/*.css /home/ark/*.js /home/ark/launch-browser.sh \"\$BACKUP_DIR/\" 2>/dev/null || true
        echo \"Legacy files moved to \$BACKUP_DIR\"
    fi
    if [ ! -d \"/home/ark/r36s-web-console\" ]; then
        git clone $REPO_URL /home/ark/r36s-web-console
    else
        cd /home/ark/r36s-web-console && git fetch origin && git reset --hard origin/main
    fi
"

echo "Syncing local changes to device..."
rsync -avz -e "ssh $SSH_OPTS" --filter=':- .gitignore' "$SCRIPT_DIR/webkit-accel-test/" ark@$HOST:/home/ark/r36s-web-console/webkit-accel-test/

echo "Installing web-console service..."
rsync -e "ssh $SSH_OPTS" --checksum "$SCRIPT_DIR/webkit-accel-test/web-console.service" ark@$HOST:/tmp/
ssh $SSH_OPTS ark@$HOST "sudo cp /tmp/web-console.service /etc/systemd/system/ && sudo systemctl daemon-reload"

echo "Disabling EmulationStation and enabling Web Console..."
ssh $SSH_OPTS ark@$HOST "sudo systemctl disable emulationstation && sudo systemctl enable web-console"

echo "Disabling GDM3 to speed up boot and free memory..."
ssh $SSH_OPTS ark@$HOST "sudo systemctl disable gdm3 gdm display-manager || true"
ssh $SSH_OPTS ark@$HOST "sudo rm -f /etc/systemd/system/display-manager.service"
ssh $SSH_OPTS ark@$HOST "sudo systemctl mask gdm3 gdm display-manager || true"

if [ -f "$SCRIPT_DIR/assets/splash.svg" ]; then
    echo "Converting splash.svg to logo.png..."
    if command -v rsvg-convert >/dev/null 2>&1; then
        rsvg-convert -w 720 -h 720 -b black "$SCRIPT_DIR/assets/splash.svg" -o /tmp/logo.png
    elif command -v convert >/dev/null 2>&1; then
        convert -background black -resize 720x720\! "$SCRIPT_DIR/assets/splash.svg" /tmp/logo.png
    else
        echo "Warning: rsvg-convert or convert not found. Skipping splash screen update."
    fi

    if [ -f /tmp/logo.png ]; then
        echo "Backing up and uploading new boot logo..."
        ssh $SSH_OPTS ark@$HOST "sudo cp /boot/logo.png /boot/logo.png.bak 2>/dev/null || true"
        rsync -e "ssh $SSH_OPTS" --checksum /tmp/logo.png ark@$HOST:/tmp/logo.png
        ssh $SSH_OPTS ark@$HOST "sudo cp /tmp/logo.png /boot/logo.png && sudo rm /tmp/logo.png"
        rm -f /tmp/logo.png
    fi
fi

echo "Done."
