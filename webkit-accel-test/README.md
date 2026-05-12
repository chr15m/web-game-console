# WebKit Hardware Acceleration Test

This directory contains the proof-of-concept for running a hardware-accelerated web browser directly on the R36S screen, bypassing X11 and Wayland entirely.

It uses `python3-pyqt5.qtwebengine` (which wraps Chromium 69) and the `eglfs` Qt platform plugin to render directly to the DRM/KMS framebuffer using the Mali-G31 GPU.

## Launch Requirements

To successfully acquire the DRM Master lock and render to the screen, the process must be attached to a physical TTY. Running it blindly over an SSH pseudo-terminal (`/dev/pts/0`) will result in a black screen.

Required environment variables and redirection:
```bash
export TERM=linux
export XDG_RUNTIME_DIR=/run/user/$(id -u)
export QT_QPA_PLATFORM=eglfs

python3 browser.py < /dev/tty1 > /dev/tty1 2>&1
```

## Browser Capabilities under EGLFS

Running Chromium in this embedded context changes how it interacts with the host OS compared to a standard desktop Linux environment.

### 🟢 Working by Default
*   **WebGL & Canvas:** Fully supported and hardware-accelerated. The unmasked renderer correctly reports `Mali-G31` (Vendor: ARM) and achieves 50-60 FPS.
*   **CSS Animations:** Hardware composited and smooth.
*   **Networking:** HTTP, HTTPS, Fetch, XHR, and WebSockets work perfectly.
*   **Web Audio API:** Supported (routes through the device's PulseAudio daemon).

### 🟡 Requires Configuration
*   **Local Storage / IndexedDB:** By default, a basic `QWebEngineView` may use volatile temporary storage. We must explicitly configure a `QWebEngineProfile` with a persistent path on the SD card so game saves survive reboots.

### 🔴 Missing or Broken
*   **HTML5 Gamepad API (`navigator.getGamepads()`):** Broken. Chromium relies on desktop Linux subsystems (udev/X11) to detect controllers. Under `eglfs`, Qt consumes the `/dev/input/event*` nodes directly, leaving Chromium blind to the joysticks.
*   **Keyboard Events from Gamepad:** The R36S gamepad (`/dev/input/event2`) is recognized as a joystick, not a keyboard. Pressing buttons will not trigger standard DOM `onkeydown` events by default.
*   **Hardware Video Decoding:** `<video>` tags will likely fall back to software decoding, as the standard Ubuntu Chromium build lacks Rockchip VPU patches.

## The Input Bridge Plan

Because the HTML5 Gamepad API is unavailable and the gamepad doesn't trigger keyboard events, we must build a custom input bridge:

1.  **Read:** Use Python's `evdev` library in `browser.py` to asynchronously read `/dev/input/event2` (the GO-Super Gamepad).
2.  **Translate:** Convert raw evdev button presses and axis movements into a standardized format.
3.  **Inject:** Pass these events into the web environment either by:
    *   Injecting synthetic Qt Key Events into the `QWebEngineView` (so the browser fires standard `keydown`/`keyup` events).
    *   Using `view.page().runJavaScript()` to call a global JavaScript callback (e.g., `window.onGamepadEvent(data)`).
