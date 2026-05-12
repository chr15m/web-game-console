- [x] Run `strace -e trace=ioctl` on EmulationStation via `openvt` on `tty1` to capture DRM/KMS ioctl calls to `/dev/dri/card0`
- [x] Compare EmulationStation strace output with SDL2 Python test output to find the missing display initialization step
- [x] Research WPE WebKit availability or compilation steps for Ubuntu 19.10 (Eoan) - *Not available, but QtWebEngine/QtWebKit are.*
- [x] Test QtWebEngine or QtWebKit rendering directly to EGLFS on `tty1`
- [ ] Test basic EGL/KMS triangle rendering in C without SDL2 to isolate the display pipeline

**QtWebEngine / EGLFS Tasks:**
- [x] Test performance with a basic CSS + emojis translate animation demo in QtWebEngine
- [x] Implement gamepad input handling in the PyQt5 application (Resolved: Native HTML5 Gamepad API works if `QTWEBENGINE_DISABLE_SANDBOX=1` is set)
- [ ] Set up and test `localStorage` and `IndexedDB` persistence. (Plan: isolate each game on its own `gameid.localhost:8000` domain).
- [ ] Test WebAssembly (Wasm) support and document limitations (Chromium 69).
- [ ] Test basic Nostr WebCrypto (`window.crypto.subtle`) and WebSocket connections (using `relay.mccormick.cx`).
- [ ] Investigate Gamepad mapping: test how far off "standard" it is, and implement a JS polyfill (or OS-level Linux remap).
- [ ] Test memory limits and OOM behavior. Ensure developers can easily profile this via remote debugging.
- [ ] Test HTML5 `<video>` software decoding performance and document caveats.
- [ ] Get https://rogule.com/game.html showing up and playable

*(Note: X11/surf tasks below are paused/archived while we pursue direct EGL/KMS rendering)*
- [ ] Basic gamepad web app test in surf

- [x] Figure out how to get 3d acceleration working
- [ ] Figure out how to do 'Enable remote services' (from emulationstation), or enable SSH
- [ ] Get it booting into surf instead of emustation
- [ ] Some way of easily getting back to emustation without network access

# Done

- [x] Launch scripts - xorg
- [x] Fix the bug where there's a black bar at the bottom of the Xorg screen

- [x] Get SSH authorized_keys working
- [x] Automate extraction of `R36S-Xorg/XFCE/files/driver` or use a git submodule
