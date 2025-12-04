# R36S Web Console Project

## About

This project aims to create a web-based game console on the R36S handheld device. The R36S runs ArkOS (based on Ubuntu 19.10) and uses a Rockchip RK3326 SoC with a Mali-G31 MP2 GPU.

The goal is to run a web browser on Xorg to deliver games via Nostr feeds.

## Technical Details

### Hardware

- **Device**: R36S handheld game console
- **SoC**: Rockchip RK3326
- **GPU**: Mali-G31 MP2
- **OS**: ArkOS 2.0 (based on Ubuntu 19.10)
- **Kernel**: 4.4.189
- **Architecture**: aarch64
- **Screen**: 720x720 (as reported by xrandr)

### Software Stack

- **Display Server**: Xorg 1.20.5
- **Window Manager**: matchbox-window-manager (kiosk-style, single window)
- **GPU Driver**: Mali driver (mali_drv.so) with hardware acceleration disabled
- **Browser**: surf (WebKit-based, suckless)
- **Cursor hiding**: unclutter

### Network Access

- Default user: `ark`
- Default password: `ark`
- SSH enabled via ArkOS menu (Options > Remote Services)
- Hostname: `rg351mp`
- IP configured in `.envrc` as `IP=...`

### Key Files

- `setup.sh` - Idempotent setup script run from local machine
- `launch.sh` - Stops GDM, sets tty permissions, kills emulationstation, starts X
- `xinitrc` - X startup script (copied to `~/.xinitrc` on device)
- `driver/mali_drv.so` - Mali GPU driver for Xorg
- `driver/99-mali.conf` - Xorg configuration for Mali GPU
- `index.html` - Test HTML file

### Driver Configuration

The Mali driver is configured in `/etc/X11/xorg.conf.d/99-mali.conf`:

```
Section "Device"
    Identifier "Mali-G31MP2"
    Driver     "mali"
    Option     "AccelMethod" "none"
EndSection

Section "Screen"
    Identifier "Default Screen"
    Device     "Mali-G31MP2"
EndSection
```

Note: Hardware acceleration is currently disabled (`AccelMethod "none"`).

### Input Devices

The R36S has the following input devices:

| Device | Name | Description |
|--------|------|-------------|
| `/dev/input/event0` | rk8xx_pwrkey | Power button |
| `/dev/input/event1` | rockchip,rk817-codec Headphones | Headphone jack detection |
| `/dev/input/event2` | GO-Super Gamepad | Main gamepad (buttons + analog sticks) |
| `/dev/input/event3` | odroidgo3-keys | Additional keys |

#### GO-Super Gamepad Details

- **Device**: `/dev/input/event2`
- **Bus**: 0x19, Vendor: 0x484b, Product: 0x1100, Version: 0x100

**Buttons (EV_KEY):**

| Code | Name | Physical |
|------|------|----------|
| 304 | BTN_SOUTH | A button |
| 305 | BTN_EAST | B button |
| 307 | BTN_NORTH | X button |
| 308 | BTN_WEST | Y button |
| 310 | BTN_TL | Left shoulder (L1) |
| 311 | BTN_TR | Right shoulder (R1) |
| 312 | BTN_TL2 | Left trigger (L2) |
| 313 | BTN_TR2 | Right trigger (R2) |
| 544 | BTN_DPAD_UP | D-pad up |
| 545 | BTN_DPAD_DOWN | D-pad down |
| 546 | BTN_DPAD_LEFT | D-pad left |
| 547 | BTN_DPAD_RIGHT | D-pad right |
| 704-708 | BTN_TRIGGER_HAPPY1-5 | Select, Start, etc. |

**Analog Axes (EV_ABS):**

| Code | Name | Range | Description |
|------|------|-------|-------------|
| 0 | ABS_X | -1800 to 1800 | Left stick horizontal |
| 1 | ABS_Y | -1800 to 1800 | Left stick vertical |
| 3 | ABS_RX | -1800 to 1800 | Right stick horizontal |
| 4 | ABS_RY | -1800 to 1800 | Right stick vertical |

**Other:**
- Supports force feedback (FF_RUMBLE)

#### Testing Input

Use `evtest` to monitor input events:

```bash
ssh ark@$HOST "evtest /dev/input/event2"
```

### Background Processes

Key processes running on the device:

- **emulationstation** (PID varies) - Main ArkOS frontend, uses ~35% memory
- **pulseaudio** - Audio daemon
- **gdm3** - Display manager (disabled, but still runs until stopped)
- **filebrowser** - Web file manager on port 80
- **sshd** - SSH server
- **smbd/nmbd** - Samba file sharing
- **NetworkManager** - Network management
- **bluetoothd** - Bluetooth daemon

**Important**: EmulationStation must be killed before running X experiments, as it holds the display. The `launch.sh` script handles this automatically.

## Setup Process

### Manual Steps (on device)

1. Enable WiFi and connect from ArkOS menu
2. Enable remote services (SSH) from ArkOS menu (Options > Remote Services)

### Automated Steps (via setup.sh)

Run from local machine:

```bash
./setup.sh <device-ip>
```

The script:
- Copies SSH public key for passwordless login (idempotent)
- Adds `ark` user to `tty`, `video`, and `input` groups
- Sets permissions on `/dev/tty0` and `/dev/tty2` for non-root X access
- Configures Xwrapper to allow non-root users
- Updates apt repos if cache is older than 30 days
- Installs xorg, surf browser, matchbox-window-manager, and unclutter
- Installs Mali GPU driver and config
- Copies index.html and xinitrc

Uses SSH connection multiplexing to avoid multiple password prompts.

## Running the Browser

Use the launch script:

```bash
./launch.sh <device-ip>
```

The script:
1. Stops gdm3 service
2. Sets tty permissions (`chmod 666 /dev/tty0 /dev/tty2`)
3. Kills emulationstation
4. Runs `startx`

The `~/.xinitrc` will:
1. Start `unclutter` to hide the mouse cursor
2. Start `matchbox-window-manager` (no title bars, auto-fullscreen)
3. Launch `surf` in fullscreen mode with `/home/ark/index.html`

## Updates

- **2025-12-04**: Created launch.sh script
  - Stops gdm3 to free memory and prevent conflicts
  - Sets tty permissions (required after each reboot)
  - Kills emulationstation before starting X
  - Single command to launch the browser kiosk

- **2025-12-04**: Disabled GDM3 display manager
  - GDM was running a full GNOME greeter session on tty1 with its own Xorg
  - This wasted ~60MB RAM from Xorg plus ~15 gsd-* daemon processes
  - Disabled with `systemctl disable gdm3`
  - EmulationStation now starts directly without the GDM overhead

- **2025-12-04**: Kiosk setup complete
  - Installed matchbox-window-manager for proper fullscreen handling
  - Installed unclutter to hide mouse cursor (`-idle 0` for immediate hiding)
  - Created xinitrc that starts matchbox + unclutter + surf
  - Configured non-root X access:
    - Added ark to tty, video, input groups
    - Set `/dev/tty0` and `/dev/tty2` to 666 permissions
    - Configured Xwrapper with `allowed_users=anybody`
  - X now starts as regular `ark` user (no sudo required)
  - Fullscreen working correctly via matchbox (no xdotool workaround needed)

- **2025-12-04**: Tested surf `-g` geometry flag
  - Surf does not support `-g` flag - it interprets it as a URL
  - Confirmed xdotool resize is the correct workaround (now superseded by matchbox)

- **2025-12-04**: Fixed black bar issue
  - Root cause: surf's WebKit window defaults to 800x600, ignoring `-F` flag
  - The `-F` flag doesn't work because there's no window manager running
  - Solution: Use matchbox-window-manager which auto-fullscreens windows

- **2025-12-04**: SSH key automation
  - setup.sh now copies SSH public key to authorized_keys
  - Idempotent - won't add duplicate keys
  - Supports id_rsa, id_ed25519, and id_ecdsa keys
  - Apt update now skipped if cache is less than 30 days old

- **2025-11-28**: Initial Xorg setup complete
  - Xorg installed and working
  - Mali driver installed to `/usr/lib/xorg/modules/drivers/`
  - Driver config installed to `/etc/X11/xorg.conf.d/` and `/usr/share/X11/xorg.conf.d/`
  - Verified X starts successfully with `sudo startx xterm`
  - xterm installed for testing
  - Created `setup.sh` with SSH connection multiplexing for single-password operation

- **2025-11-28**: Browser setup complete
  - Abandoned Chromium (snap-only on Ubuntu 19.10, snapd doesn't work on this kernel)
  - Installed surf (WebKit-based suckless browser)
  - surf working with local HTML and SVG files

## Known Issues

- X server uses modeset driver, not Mali driver (need to investigate)
- Hardware acceleration disabled in Mali config
- TTY permissions reset on reboot (launch.sh handles this)

## Debugging Black Bar Issue (Resolved)

### Findings (2025-12-04)

1. **xrandr confirms 720x720**: Screen is correctly detected as 720x720
   ```
   Screen 0: minimum 320 x 200, current 720 x 720, maximum 8192 x 8192
   DSI-1 connected primary 720x720+0+0 (normal left inverted right x axis y axis) 0mm x 0mm
      720x720       59.87*+
   ```

2. **Xorg can draw to bottom of screen**: Tested with `xterm -geometry 80x10+0+620` positioned at y=620, and it rendered correctly at the bottom of the screen.

3. **surf creates two windows**:
   - Window 1 (InputOnly, unmapped): 720x720 at +10+10 - this is a wrapper/input window
   - Window 2 (InputOutput, visible): 800x600 at +0+0 - this is the actual WebKit content window

4. **Root cause**: WebKit defaults to 800x600 regardless of the `-F` fullscreen flag. The `-F` flag requires a window manager to handle the fullscreen request.

5. **Solution**: Use matchbox-window-manager which automatically fullscreens all windows.

### Diagnostic commands

```bash
# Check xrandr
ssh ark@${IP} "DISPLAY=:0 xrandr"

# Find surf windows
ssh ark@${IP} "DISPLAY=:0 xdotool search --class surf"

# Check window properties
ssh ark@${IP} "DISPLAY=:0 xprop -id <window-id>"

# Check window geometry
ssh ark@${IP} "DISPLAY=:0 xwininfo -id <window-id>"
```

## Next Steps

- Set up joystick-to-keyboard mapping (joy2key or similar) for game controls
- Set up Nostr game feed integration
- Create auto-start mechanism for X + browser
- Investigate Mali hardware acceleration

## References

Repo for getting xorg and xfce working on similar devices:

- <https://github.com/OkJacket2022/R36S-Xorg>
- <https://github.com/OkJacket2022/R36S-Xorg/blob/main/XFCE/Install-XFCE.sh>

ArkOS wiki:

- [ArkOS Wiki](https://github.com/christianhaitian/arkos/wiki)
