- [x] Run `strace -e trace=ioctl` on EmulationStation via `openvt` on `tty1` to capture DRM/KMS ioctl calls to `/dev/dri/card0`
- [x] Compare EmulationStation strace output with SDL2 Python test output to find the missing display initialization step
- [x] Research WPE WebKit availability or compilation steps for Ubuntu 19.10 (Eoan) - *Not available, but QtWebEngine/QtWebKit are.*
- [x] Test QtWebEngine or QtWebKit rendering directly to EGLFS on `tty1`
- [ ] Test basic EGL/KMS triangle rendering in C without SDL2 to isolate the display pipeline

**QtWebEngine / EGLFS Tasks:**
- [ ] Test performance with a basic CSS + emojis translate animation demo in QtWebEngine
- [ ] Implement gamepad input handling in the PyQt5 application
- [ ] Get https://rogule.com/game.html showing up and playable

*(Note: X11/surf tasks below are paused/archived while we pursue direct EGL/KMS rendering)*
- [ ] Basic gamepad web app test in surf

- [ ] Figure out how to get 3d acceleration working
- [ ] Figure out how to do 'Enable remote services' (from emulationstation), or enable SSH
- [ ] Get it booting into surf instead of emustation
- [ ] Some way of easily getting back to emustation without network access

# Done

- [x] Launch scripts - xorg
- [x] Fix the bug where there's a black bar at the bottom of the Xorg screen

- [x] Get SSH authorized_keys working
- [x] Automate extraction of `R36S-Xorg/XFCE/files/driver` or use a git submodule
