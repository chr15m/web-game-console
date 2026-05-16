# R36S Web Game Console

A web-based game console running on the R36S handheld device. Games are delivered over the Nostr network and run in a hardware-accelerated web environment directly on the device framebuffer.

## Architecture & Stack

- **Device**: R36S (Rockchip RK3326, Mali-G31 MP2 GPU, 1GB RAM, 720x720 screen).
- **OS**: ArkOS 2.0 (Ubuntu 19.10 Eoan Ermine, Kernel 4.4.189, aarch64).
- **Browser Engine**: Chromium 69 via `python3-pyqt5.qtwebengine`.
- **Display**: Renders directly to the DRM/KMS framebuffer using the `eglfs` Qt platform plugin (`QT_QPA_PLATFORM=eglfs`). Bypasses X11/Wayland entirely. Hardware acceleration (WebGL, CSS) is fully active at 50-60 FPS.
- **Input**: Native HTML5 Gamepad API. A JS polyfill remaps the raw R36S button indices to the W3C standard layout.
- **Audio**: Web Audio API via PulseAudio.
- **Storage**: `localStorage` and `IndexedDB` are persistent and isolated per game via `QWebEngineProfile` (`.storage/<slugified-hostname>`).

## How It Works

- **DRM Master Lock**: To render to the screen, the browser process *must* be attached to a physical TTY (`< /dev/tty1 > /dev/tty1 2>&1`). Running it blindly over an SSH pseudo-terminal (`/dev/pts/0`) will result in a black screen because it cannot acquire the DRM Master lock.
- **Sandbox Disabled**: The Chromium sandbox must be disabled (`QTWEBENGINE_DISABLE_SANDBOX=1`). Without this, the sandboxed renderer process is denied read access to `/dev/input/event*`, breaking the Gamepad API.
- **X11/Wayland Abandoned**: Do not attempt to use X11 or Wayland. The Mali userspace blobs and kernel driver versions on this BSP are mismatched. `eglfs` is the only working path for GPU acceleration.
- **Nostr Game Distribution**: Games are published to Nostr as Kind 30078 events containing a Base64-encoded ZIP of the game directory.
- **Emoji Game Codes**: Games are looked up using a 16-emoji "Pure Hash" generated via `SHA256(pk || salt)[0:64]`.

## Development & Hacking

### 1. Desktop Simulator
You can develop and test games on your local machine without the physical device.
```bash
./webkit-accel-test/r36s-simulator webkit-accel-test/index.html
```
This opens a 720x720 Chromium window, auto-opens DevTools, and injects a keyboard-to-gamepad shim so you can navigate the UI using your keyboard (Arrow keys, Z/X/C/V, Enter, etc.).

### 2. Device Setup
To prepare a fresh ArkOS R36S device:
```bash
./setup.sh <device-ip>
```
This is idempotent. It installs dependencies (PyQt5, emoji fonts), disables EmulationStation and GDM3, sets up the `web-console.service`, and copies the initial files.

### 3. Deploying Code
When hacking on the Python browser wrapper or the HTML/JS UI, deploy your changes with:
```bash
cd webkit-accel-test && ./deploy.sh <device-ip>
```
This syncs the files, restarts the systemd service, and automatically opens an SSH tunnel for remote debugging.

### 4. Remote Debugging
After running `deploy.sh`, open a Chromium-based browser on your local machine and navigate to:
```
http://localhost:9222
```
You will have full access to the Chrome DevTools for the web view running on the R36S.

## Key Files

- `webkit-accel-test/browser.py` - The PyQt5 browser wrapper. Handles EGLFS setup, gamepad polyfills, and per-game storage profiles.
- `webkit-accel-test/index.html` - The main console UI (Nostr fetching, game launching).
- `webkit-accel-test/web-console.service` - The systemd unit that attaches to `/dev/tty1` and launches the browser.
- `webkit-accel-test/r36s-simulator` - Local desktop development shim.
- `publisher/` - The web app used by developers to bundle and publish games to Nostr.
- `PROJECT.md` & `PROJECT-current.md` - Deep technical notes, investigation history, and current goals.
