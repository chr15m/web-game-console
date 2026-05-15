#!/bin/bash
# Map gamepad D-pad and buttons to keyboard events
# Requires: evtest, xdotool

DEVICE=/dev/input/event2

# Find the X server run by ark user and get its display number
XORG_PID=$(pgrep -u ark Xorg | head -1)
if [ -z "$XORG_PID" ]; then
    echo "ERROR: No Xorg process found for user ark"
    exit 1
fi

# Extract display from Xorg command line (e.g., ":1")
XDISPLAY=$(ps -p "$XORG_PID" -o args= | grep -oE ':[0-9]+' | head -1)
if [ -z "$XDISPLAY" ]; then
    echo "ERROR: Could not determine DISPLAY from Xorg process"
    exit 1
fi

# Extract -auth file from Xorg command line
XAUTH=$(ps -p "$XORG_PID" -o args= | grep -oE '\-auth [^ ]+' | cut -d' ' -f2)
if [ -z "$XAUTH" ]; then
    echo "ERROR: Could not determine XAUTHORITY from Xorg process"
    exit 1
fi

export DISPLAY="$XDISPLAY"
export XAUTHORITY="$XAUTH"

echo "joy-keys-hack: mapping gamepad to keys"
echo "  D-pad -> Arrow keys"
echo "  A (BTN_SOUTH) -> Enter"
echo "  B (BTN_EAST) -> Tab"
echo "Reading from $DEVICE..."

echo "DEBUG: DISPLAY=$DISPLAY"
echo "DEBUG: XAUTHORITY=$XAUTHORITY"
echo "DEBUG: XAUTHORITY file exists: $(test -f "$XAUTHORITY" && echo yes || echo no)"
echo "DEBUG: XAUTHORITY file readable: $(test -r "$XAUTHORITY" && echo yes || echo no)"
echo "DEBUG: XAUTHORITY file contents (xauth list):"
xauth -f "$XAUTHORITY" list 2>&1
echo "DEBUG: Xorg command line:"
ps -p "$XORG_PID" -o args=
echo "DEBUG: Checking if cookie matches display $XDISPLAY:"
xauth -f "$XAUTHORITY" list | grep -E "$XDISPLAY|:${XDISPLAY#:}" || echo "(no match found)"
echo "DEBUG: Trying to add local access..."
xhost +local: 2>&1 || echo "(xhost failed, continuing anyway)"
echo "DEBUG: Testing xdpyinfo after xhost:"
xdpyinfo 2>&1 | head -3

echo "Starting event loop..."

evtest "$DEVICE" 2>/dev/null | while read line; do
    if echo "$line" | grep -q "EV_KEY.*value 1"; then
        case "$line" in
            *BTN_DPAD_UP*)    echo "UP"; xdotool key Up ;;
            *BTN_DPAD_DOWN*)  echo "DOWN"; xdotool key Down ;;
            *BTN_DPAD_LEFT*)  echo "LEFT"; xdotool key Left ;;
            *BTN_DPAD_RIGHT*) echo "RIGHT"; xdotool key Right ;;
            *BTN_SOUTH*)      echo "A->Enter"; xdotool key Return ;;
            *BTN_EAST*)       echo "B->Tab"; xdotool key Tab ;;
        esac
    fi
done
