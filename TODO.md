- [x] Audio is laggy - reduce buffer size (tested 256 vs 512 samples)

- [ ] Work through high-priority items in `performance-tuning.md`:
  - [ ] Set CPU & GPU governors to 'performance' on boot
  - [ ] Add Nice=-10 and LimitRTPRIO=99 to web-console.service
  - [ ] Test disabling PulseAudio service and validating direct ALSA playback

- [ ] Basic "browse games" page pulling from a nostr pubkey feed with tag #mainfeed

- [ ] Improve the game code entering interface and fix design to match front page

- [ ] WiFi page fixes
  - [ ] Make the design match the new homepage
  - [ ] Open wifi access points should be clearer
  - [ ] WiFi page hangs under different circumstances (e.g. connect)
  - [ ] Can't exit WiFi page

- [ ] Implement robust top level "exit game" buttons event handler (start + select)

- [ ] Initial placeholder page on webgameconsole.com with:
  - [ ] Basic copy
  - [ ] Uploader page
  - [ ] Game simulator

- [ ] "check for updates" freezes the screen - needs to be async with a callback

- [ ] Isolate games on their own .localhost domain

# Post-SLC

- [ ] Cache games locally after downloading and list downloaded games
- [ ] Can we improve the UI so the grid is still showing while entering?
- [ ] An LLM document to explain how to build games, with examples
- [ ] Support games with more than 1 file (?.localhost:8000 serving)

**QtWebEngine / EGLFS Tasks:**

- [ ] Test memory limits and OOM behavior and document. Ensure developers can easily profile this via remote debugging.
- [ ] Test HTML5 `<video>` software decoding performance and document caveats.
- [ ] Test WebAssembly (Wasm) support and document limitations (Chromium 69).

# Paused

- [-] Doom test?

- [-] Get https://rogule.com/game.html showing up and playable

*(Note: X11/surf tasks below are paused/archived while we pursue direct EGL/KMS rendering)*
- [-] Basic gamepad web app test in surf
- [-] Test basic EGL/KMS triangle rendering in C without SDL2 to isolate the display pipeline
- [x] Figure out how to get 3d acceleration working
- [-] Get it booting into surf instead of emustation

# Done

- [x] Git pull to update

- [x] Provide a way to configure wifi, either the original emustation TUI or a localhost API with web UI.
- [x] Do a basic Nostr receive to get a game on there.
- [x] EOSE should stop the loading spinner
- [x] Get emojis showing up on the real hardware? (Chromium or qt5 problem?)
- [x] Once the game is loaded the gamepad left/right aren't working and X crashes it

**QtWebEngine / EGLFS Tasks:**
- [x] Test basic Nostr WebCrypto (`window.crypto.subtle`) and WebSocket connections (using `relay.mccormick.cx`).
- [x] Replace the existing splash image.
- [x] Boot straight into our demo instead of emulationstation
- [x] Some way of "uninstalling" getting back to emustation without network access in case we brick
- [x] Figure out how to do 'Enable remote services' (from emulationstation), or enable SSH
- [x] Run `strace -e trace=ioctl` on EmulationStation via `openvt` on `tty1` to capture DRM/KMS ioctl calls to `/dev/dri/card0`
- [x] Compare EmulationStation strace output with SDL2 Python test output to find the missing display initialization step
- [x] Research WPE WebKit availability or compilation steps for Ubuntu 19.10 (Eoan) - *Not available, but QtWebEngine/QtWebKit are.*
- [x] Test QtWebEngine or QtWebKit rendering directly to EGLFS on `tty1`
- [x] Test performance with a basic CSS + emojis translate animation demo in QtWebEngine
- [x] Implement gamepad input handling in the PyQt5 application (Resolved: Native HTML5 Gamepad API works if `QTWEBENGINE_DISABLE_SANDBOX=1` is set)
- [x] Set up and test `localStorage` and `IndexedDB` persistence. (Implemented via `.storage/slugified-hostname` profiles).
- [x] Investigate Gamepad mapping: test how far off "standard" it is, and implement a JS polyfill (or OS-level Linux remap).

**Old**

- [x] Launch scripts - xorg
- [x] Fix the bug where there's a black bar at the bottom of the Xorg screen

- [x] Get SSH authorized_keys working
- [x] Automate extraction of `R36S-Xorg/XFCE/files/driver` or use a git submodule
