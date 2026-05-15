# R36S+ Web Game Console

A web-based game console running on the R36S+ handheld device. Games are delivered via Nostr.

## Stack

- **Device**: R36S (Rockchip RK3326, Mali-G31 MP2, 720x720 screen, ArkOS/Ubuntu 19.10)
- **Browser**: Chromium 69 via `python3-pyqt5.qtwebengine`, rendered direct to framebuffer using `QT_QPA_PLATFORM=eglfs`
- **GPU**: Hardware-accelerated via Mali-G31 (50-60 FPS WebGL confirmed)
- **Input**: HTML5 Gamepad API (requires `QTWEBENGINE_DISABLE_SANDBOX=1`), with a JS polyfill to remap raw R36S indices to the W3C standard layout
- **Audio**: Web Audio API via PulseAudio
- **Storage**: `localStorage` and `IndexedDB`, isolated per game via `QWebEngineProfile`

## Setup

```bash
./setup.sh <device-ip>
```

Installs dependencies, copies files, enables the `web-console` systemd service, and disables EmulationStation.

## Deploy

```bash
cd webkit-accel-test && ./deploy.sh <device-ip>
```

Copies updated files and restarts the service. Also opens an SSH tunnel for remote debugging at `http://localhost:9222`.

## Key Files

- `webkit-accel-test/browser.py` - PyQt5 browser wrapper with gamepad polyfill and per-game storage
- `webkit-accel-test/index.html` - Main menu
- `webkit-accel-test/web-console.service` - systemd unit (attaches to `/dev/tty1` for DRM master)
- `setup.sh` - Idempotent device setup script
- `PROJECT.md` - Full technical notes and investigation history

