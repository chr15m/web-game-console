# R36S Web Console Project

## About

This project aims to create a web-based game console on the R36S handheld device. The R36S runs ArkOS (based on Ubuntu 19.10) and uses a Rockchip RK3326 SoC with a Mali-G31 MP2 GPU.

The goal is to run a web browser on Xorg to deliver games via Nostr feeds.

## Technical Details

### Hardware

- **Device**: R36S handheld game console (possibly R36S Plus variant)
- **SoC**: Rockchip RK3326
- **CPU**: Quad-core ARM Cortex-A35 (CPU part 0xd04)
- **GPU**: Mali-G31 MP2 (Bifrost architecture 7.0.9 r0p0)
- **RAM**: 897 MiB total
- **Storage**: 9.8G root partition, 41G roms partition
- **OS**: ArkOS 2.0 (Ubuntu 19.10 Eoan Ermine)
- **Kernel**: 4.4.189
- **Architecture**: aarch64
- **Screen**: 720x720 (as reported by xrandr and fb0)

#### System Info

```
$ uname -a
Linux rg351mp 4.4.189 #3 SMP Wed Oct 13 23:24:26 EDT 2021 aarch64 aarch64 aarch64 GNU/Linux
```

```
$ cat /etc/os-release
NAME="Ubuntu"
VERSION="19.10 (Eoan Ermine)"
ID=ubuntu
ID_LIKE=debian
PRETTY_NAME="Ubuntu 19.10"
VERSION_ID="19.10"
VERSION_CODENAME=eoan
UBUNTU_CODENAME=eoan
```

```
$ cat /proc/cpuinfo
processor	: 0
BogoMIPS	: 48.00
Features	: fp asimd evtstrm aes pmull sha1 sha2 crc32
CPU implementer	: 0x41
CPU architecture: 8
CPU variant	: 0x0
CPU part	: 0xd04
CPU revision	: 2

processor	: 1
BogoMIPS	: 48.00
Features	: fp asimd evtstrm aes pmull sha1 sha2 crc32
CPU implementer	: 0x41
CPU architecture: 8
CPU variant	: 0x0
CPU part	: 0xd04
CPU revision	: 2

processor	: 2
BogoMIPS	: 48.00
Features	: fp asimd evtstrm aes pmull sha1 sha2 crc32
CPU implementer	: 0x41
CPU architecture: 8
CPU variant	: 0x0
CPU part	: 0xd04
CPU revision	: 2

processor	: 3
BogoMIPS	: 48.00
Features	: fp asimd evtstrm aes pmull sha1 sha2 crc32
CPU implementer	: 0x41
CPU architecture: 8
CPU variant	: 0x0
CPU part	: 0xd04
CPU revision	: 2

Hardware	: Hardkernel ODROID-GO3
Revision	: 0000
Serial		: d5ffd534bc701888
```

```
$ free -h
              total        used        free      shared  buff/cache   available
Mem:          897Mi       405Mi       150Mi        10Mi       341Mi       466Mi
Swap:            0B          0B          0B
```

```
$ df -h
Filesystem      Size  Used Avail Use% Mounted on
/dev/mmcblk0p2  9.8G  6.3G  3.1G  68% /
/dev/mmcblk0p1  111M   42M   69M  38% /boot
/dev/mmcblk0p3   41G   40G  534M  99% /roms
```

```
$ ls /dev/dri/
by-path  card0  controlD64  renderD128
```

```
$ lsmod
Module                  Size  Used by
dwc2                  118784  0
8188eu               1536000  0
r8188eu               376832  0
exfat                  77824  1
gpio_keys              16384  0
sch_fq_codel           16384  5
ip_tables              24576  0
x_tables               20480  1 ip_tables
ipv6                  299008  46
```

Note: No Mali kernel module loaded as a module - it's built into the kernel (see GPU section below).

### GPU Acceleration Status

#### Current Status

**BLOCKED** - Both ArkOS variants have incompatible Mali userspace libraries:

1. **Missing GBM symbols** - Mali library doesn't implement `gbm_bo_unmap`, `gbm_bo_get_plane_count` required by modern tools
2. **Version mismatch** - Kernel Mali driver is 11.7, available userspace is either too old (10.6/r6p0) or too new (11.29+)

See [PROJECT-video-upgrade.md](PROJECT-video-upgrade.md) for detailed investigation and options.

#### Performance Impact

Software rendering causes **jerky CSS animations and transitions**. A 2D game was tested and rendered correctly, but movement and CSS transitions were noticeably jerky. This confirms GPU acceleration is needed for smooth animation - the CPU cannot keep up with compositing work that the GPU should handle.

### Software Stack

- **Display Server**: Xorg 1.20.5 (currently implemented, but being phased out for direct EGL/KMS), Wayland blocked by Mali GBM issues
- **Window Manager**: matchbox-window-manager (kiosk-style, single window)
- **GPU Driver**: modesetting (Mali driver fails to load)
- **Browser**: surf (WebKit-based, suckless) - *Note: pivoting to WPE WebKit*
- **Cursor hiding**: unclutter

### APT Sources

The system uses Ubuntu 19.10 (Eoan) EOL repositories:
- `http://old-releases.ubuntu.com/ubuntu eoan/main`
- `http://old-releases.ubuntu.com/ubuntu eoan-updates/main`

Ubuntu 19.10 reached EOL in July 2020, so only archived packages are available.

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
- `driver/mali_drv.so` - Mali GPU driver for Xorg (currently not working)
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

Note: Hardware acceleration is currently disabled (`AccelMethod "none"`), and the Mali driver fails to load anyway.

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

**Note**: `killall emulationstation` often fails. Use `pkill -f emulationstation` instead.

## Setup Process

### Manual Steps (on device)

1. Enable WiFi and connect from ArkOS menu
2. Enable remote services (SSH) from ArkOS menu (Options > Remote Services)

### Manual Debugging Notes
- `strace` is not installed by default on ArkOS. If debugging binaries, install it first: `sudo apt install strace`.

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

## Next Steps

See [PROJECT-video-upgrade.md](PROJECT-video-upgrade.md) for current GPU acceleration options.

**Current status:**
- **SUCCESS**: Hardware-accelerated web rendering achieved! By using `python3-pyqt5.qtwebengine` with `QT_QPA_PLATFORM=eglfs` and redirecting I/O to `/dev/tty1`, we successfully bypassed X11/Wayland and rendered directly to the screen using the Mali GPU.
- **Performance Verified**: Tested complex CSS animations ("Juice It" bounce) and confirmed they run smoothly, proving the hardware compositor is active and performant.
- **Strategic Pivot**: The X11/Wayland paths are archived. They are dead ends due to Mali blob/kernel mismatches and missing GBM symbols.
- **ROCKNIX blocked**: Fails to boot without hardware debugging (UART), which we are avoiding for now.

**Recommended next steps:**
1. **Input Handling**: Implement gamepad input handling within the PyQt5 application so it can be passed to the web environment.
2. **Game Testing**: Get a real web game (like rogule.com) running and playable to verify WebGL and input integration.
3. **Nostr Integration**: Begin building the actual web console UI and Nostr game delivery mechanism.

## Updates

- **2026-05-12**: SUCCESS - Hardware-accelerated browser working!
  - Successfully launched a PyQt5 WebEngine script directly to the screen using EGLFS.
  - The critical missing piece was TTY redirection: `< /dev/tty1 > /dev/tty1 2>&1`.
  - Without this redirection, processes running over SSH (`/dev/pts/0`) are denied the DRM Master lock, resulting in a black screen despite successful EGL context creation.
  - We now have a fully working, hardware-accelerated Chromium-based browser running on the R36S without X11 or Wayland.
  - Tested CSS animations and confirmed they run smoothly, proving the hardware compositor is active.

- **2026-05-11**: Discovered EmulationStation launch mechanism and Qt5 Web packages
  - Found `libqt5webengine5` and `libqt5webkit5` are available in the Ubuntu 19.10 repos. This provides a direct path to a hardware-accelerated browser using Qt's `eglfs` platform plugin.
  - Analyzed `/usr/bin/emulationstation/emulationstation.sh` wrapper script.
  - Discovered it does *not* use custom `LD_LIBRARY_PATH` or `SDL_VIDEODRIVER` vars.
  - Instead, it relies on physical TTY access: `chmod 666 /dev/tty1`, `TERM=linux`, and `XDG_RUNTIME_DIR=/run/user/$UID/`.
  - This explains why previous SDL2/KMSDRM Python tests over SSH (`/dev/pts/0`) failed with a black screen: they lacked the physical TTY required to acquire the DRM master lock.

- **2025-12-11**: Strategic Pivot - Abandoning X11/Wayland
  - Concluded that forcing a modern desktop Linux graphics stack (X11/Wayland) onto this BSP kernel (4.4.189) with proprietary blobs is a dead end.
  - EmulationStation proves the hardware and drivers are capable of EGL/DRM rendering.
  - Pivoting to the "Embedded Industry" approach: bypassing display servers entirely.
  - New focus: WPE WebKit (direct to EGL/KMS) and reverse-engineering EmulationStation's DRM ioctl calls via `strace`.
  - Hardware hacking (UART) for ROCKNIX debugging is explicitly avoided for now.

- **2025-12-10**: Extensive GPU rendering investigation
  - Discovered EmulationStation binary location: `/usr/bin/emulationstation/emulationstation`
  - Found custom Mali libraries in `/usr/local/lib/aarch64-linux-gnu/` (separate from `/usr/lib/`)
  - EmulationStation uses SDL2 + EGL + GLES via custom library path
  - Tested multiple rendering approaches - all show black screen:
    - Qt5 eglfs: EGL context creates successfully, but black screen (DRM atomic API warning)
    - SDL2 KMSDRM software rendering: initializes without errors, black screen
    - SDL2 + OpenGL ES (PyOpenGL): context created but `glGetString()` returns None, black screen
    - pygame: linked to ancient SDL 1.2, lacks KMSDRM support
  - Installed PySDL2 (python3-sdl2 0.9.6) for testing
  - Key finding: rendering layer works (no errors), but display scanout fails
  - ROCKNIX R36S Plus DTB test failed - screen flashes grey twice then nothing
  - Root cause unclear: EmulationStation uses same SDL2 library but renders successfully

- **2025-12-06**: ArkOS-R3XS GPU testing - BLOCKED
  - Installed kmscube, weston, sway for GPU testing
  - kmscube fails: `undefined symbol: gbm_bo_unmap`
  - weston fails: `undefined symbol: gbm_bo_get_plane_count`
  - sway fails: session/tty issues
  - Root cause: Mali GBM implementation (r6p0) predates Mesa 17.1, missing modern GBM functions
  - All Ubuntu 19.10 Wayland tools require GBM functions the Mali library doesn't have

- **2025-12-06**: ArkOS-R3XS flashed and booted successfully
  - Image: ArkOS_R36SPLUS_v2.0_11072025.img.xz
  - Boots to EmulationStation
  - Mali library: libmali-bifrost-g31-rxp0-wayland-gbm.so (r6p0)
  - Same kernel 4.4.189 as original ArkOS
  - Same Mali userspace library issues

- **2025-12-06**: Discovered ArkOS-R3XS community image
  - AeolusUX maintains ArkOS fork specifically for R36S/R35S/R33S
  - Uses r13p0 Mali userspace (from ODROID wiki)
  - Has dedicated R36S Plus image
  - Kernel likely has newer Mali driver than stock 4.4.189
  - Downloading to test GPU acceleration
  - GitHub: https://github.com/AeolusUX/ArkOS-R3XS

- **2025-12-06**: Mali r11p0 library search completed - NOT FOUND
  - Searched: Wayback Machine, all GitHub forks/mirrors, GitLab, Buildroot, ARM downloads
  - r11p0 libraries appear to have never been publicly released
  - rockchip-linux/libmali repo was restructured, old commits lost
  - All available versions (g2p0, g13p0, r13p0, r16p0) are too new for kernel 11.7

- **2025-12-06**: ROCKNIX R36S Plus image check - DOES NOT EXIST
  - No R36S Plus specific image in ROCKNIX releases
  - No "b" variant exists

- **2025-12-06**: ROCKNIX flash attempted - FAILED
  - Image: ROCKNIX-RK3326.aarch64-20250517-a.img.gz (SHA256 verified)
  - Result: Screen flashes, clicks heard, device does not boot
  - Possible cause: Image is for R36S, device may be R36S Plus (different hardware)
  - ArkOS SD card backed up to `roms/original-rom/`

- **2025-12-10**: ROCKNIX R36S Plus DTB obtained
  - Supplier provided custom device tree files in `rocknix-files/`
  - `rk3326-gameconsole-r36plus.dtb` - DTB for R36S Plus hardware
  - `extlinux.conf` - Boot config pointing to new DTB
  - Requires `mipi-panel.dtbo` overlay (included in ROCKNIX)

- **2025-12-10**: ROCKNIX R36S Plus DTB test - FAILED
  - Modified `boot.ini` to force-load R36S Plus DTB
  - Result: Screen goes grey twice, then nothing (vs original: just flashes)
  - Progress: Kernel appears to load (grey screen) but fails during init
  - Next step: Add boot logging to diagnose failure point

- **2025-12-06**: Consolidated GPU investigation into PROJECT-video-upgrade.md
  - Ruled out: AmberELEC (doesn't support R36S), ArkOS-K36 (same kernel/Mali issue), Wayland with g2p0 (version mismatch unfixable)
  - Remaining options documented with status

- **2025-12-06**: Identified ROCKNIX as recommended path forward
  - R36S explicitly supported with working Panfrost GPU
  - Download: ROCKNIX-RK3326.aarch64-20250517-a.img.gz
  - Challenge shifts from "find Mali libraries" to "build browser for ROCKNIX"

- **2025-12-06**: Documented performance impact of software rendering
  - 2D game tested - renders correctly but CSS animations/transitions are jerky
  - Confirms GPU acceleration is needed for smooth animation
  - CPU cannot handle compositing work efficiently

- **2025-12-06**: Mali library upgrade attempted - BLOCKED
  - Tried multiple Mali userspace libraries, all incompatible with kernel 11.7
  - tsukumijima g13p0 deb: requires libc 2.34 (system has 2.30)
  - ODROID r13p0: `gbm_bo_unmap` symbol missing, version too new
  - JeffyCN g2p0: reports user 11.29, too new (need 11.7-11.11)
  - Removed ArkOS packages (emulationstation-go2, libgo2, etc.) - NOT in repos
  - Current state: g2p0 library installed but not working
  - Need to find r11p0 libraries OR upgrade kernel to match available userspace

- **2025-12-05**: Root cause of GPU acceleration failure identified
  - Mali userspace libraries are version 10.6
  - Mali kernel driver is version 11.7
  - Version mismatch prevents EGL initialization
  - Error: `file /dev/mali0 is not of a compatible version (user 10.6, kernel 11.7)`
  - Tested weston, sway, kmscube - all fail due to this mismatch
  - Need to find Mali userspace libraries version 11.7 (r11p0)

- **2025-12-05**: GPU acceleration investigation complete
  - Mali kernel driver IS working (`/dev/mali0` present, built into kernel)
  - Correct userspace libraries installed (`libmali-rk-bifrost-g31-rxp0-wayland-gbm`)
  - **Key finding**: Libraries only support Wayland, not X11
  - X11 path is blocked - no compatible X11 Mali libraries available
  - Wayland is the path forward for GPU acceleration
  - Need to evaluate Wayland compositor options (weston available in repos)

- **2025-12-04**: Confirmed no GPU acceleration
  - Mali driver (`mali_drv.so`) fails to load with "maliModuleData" error
  - Likely ABI mismatch or wrong architecture for Xorg 1.20.5
  - X falls back to modesetting driver with software rendering (swrast)
  - glamor disabled, no DRI2 support
  - All OpenGL goes through CPU-based software rasterizer

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

## Custom ArkOS Libraries

The ldconfig warnings reveal custom-installed libraries (regular files instead of symlinks). These are likely GPU-accelerated builds specific to ArkOS:

### 64-bit (aarch64) - `/lib/aarch64-linux-gnu/`

| Library | Purpose |
|---------|---------|
| `libSDL2_gfx-1.0.so.0` | SDL2 graphics primitives |

### 32-bit (armhf) - `/lib/arm-linux-gnueabihf/`

| Library | Purpose |
|---------|---------|
| `libQt5EglFSDeviceIntegration.so.5` | Qt5 EGL fullscreen device integration |
| `libQt5EglFsKmsSupport.so.5` | Qt5 EGL KMS/DRM support |
| `libQt5OpenGL.so.5` | Qt5 OpenGL bindings |
| `libQt5Core.so.5` | Qt5 core library |
| `libQt5DBus.so.5` | Qt5 D-Bus IPC |
| `libQt5Svg.so.5` | Qt5 SVG rendering |
| `libQt5XcbQpa.so.5` | Qt5 X11/XCB platform plugin |
| `libQt5Network.so.5` | Qt5 networking |
| `libQt5Gui.so.5` | Qt5 GUI/rendering |
| `libQt5Widgets.so.5` | Qt5 widget toolkit |
| `libSDL2_net-2.0.so.0` | SDL2 networking |
| `libpcre2-16.so.0` | PCRE2 regex (Qt dependency) |
| `libdouble-conversion.so.3` | Float conversion (Qt dependency) |

### Implications

**Qt5 with EGL/KMS**: The presence of `libQt5EglFSDeviceIntegration` and `libQt5EglFsKmsSupport` suggests Qt5 apps can run with GPU acceleration via EGL, bypassing X11 entirely. This is the "eglfs" platform plugin.

**Potential QtWebEngine path**: `libqt5webengine5` (Chromium-based) and `libqt5webkit5` *are* available in the Ubuntu 19.10 repositories. Since Qt5 EGLFS is already proven to initialize an EGL context successfully on this device, building a minimal QtWebEngine/QtWebKit application running on the `eglfs` platform plugin is currently the most promising path for a hardware-accelerated browser.

**EmulationStation uses Qt?**: The presence of these Qt libraries suggests EmulationStation or other ArkOS components may use Qt with EGL for GPU-accelerated rendering. This could explain how they achieve smooth performance.

### Investigation Results

**EmulationStation does NOT use Qt** - it uses SDL2 + EGL + GLES directly.

**Qt5 packages installed** (5.12.4):
- libqt5core5a, libqt5gui5, libqt5widgets5, etc.
- Platform plugins: libqeglfs.so, libqlinuxfb.so, libqxcb.so, etc.
- Location: `/usr/lib/aarch64-linux-gnu/qt5/plugins/platforms/`

**QtWebKit available in repos**: `libqt5webkit5` - could provide GPU-accelerated browser via Qt eglfs platform.

## Working GPU Acceleration Path (EmulationStation)

EmulationStation achieves GPU acceleration through:

### EmulationStation Binary Location & Launch Mechanism

EmulationStation is launched via a systemd service (`emulationstation.service`) which calls a wrapper script:
```
/usr/bin/emulationstation/emulationstation.sh
```
This script eventually calls the binary at `/usr/bin/emulationstation/emulationstation`.

**Critical Discovery**: The wrapper script does *not* set `LD_LIBRARY_PATH` or `SDL_VIDEODRIVER`. Instead, it sets up physical TTY access:
```bash
sudo chmod 666 /dev/tty1
export TERM=linux
export XDG_RUNTIME_DIR=/run/user/$UID/
```
This reveals that KMS/DRM applications on this device must be attached to an active physical TTY (like `tty1`) to acquire the DRM master lock. Previous tests run over SSH (`/dev/pts/0`) failed with a black screen because they lacked this physical TTY attachment.

Verified with strace:
```bash
ldd /usr/bin/emulationstation/emulationstation | grep -i egl
# libEGL.so => /usr/local/lib/aarch64-linux-gnu/libEGL.so

strace -e openat /usr/bin/emulationstation/emulationstation 2>&1 | grep -i egl
# openat(AT_FDCWD, "/usr/local/lib/aarch64-linux-gnu/libEGL.so", O_RDONLY|O_CLOEXEC) = 3
# openat(AT_FDCWD, "/usr/local/lib/aarch64-linux-gnu/libEGL.so.1", O_RDONLY|O_CLOEXEC) = 9
```

### Library Chain
```
EmulationStation (/usr/bin/emulationstation/emulationstation)
  → libSDL2-2.0.so.0 (graphics/input)
  → libEGL.so @ /usr/local/lib/aarch64-linux-gnu/  ← KEY: custom path!
  → libGLES_CM.so (OpenGL ES)
  → libdrm.so.2 (DRM)
  → libmali-bifrost-g31-rxp0-gbm.so  ← NOT the wayland-gbm variant!
```

### Critical Library Locations

**Working Mali libraries** (`/usr/local/lib/`):
| Path | File | Notes |
|------|------|-------|
| `/usr/local/lib/aarch64-linux-gnu/` | `libmali-bifrost-g31-rxp0-gbm.so` | 64-bit, GBM only |
| `/usr/local/lib/aarch64-linux-gnu/` | `libmali.so` | Symlink to above |
| `/usr/local/lib/arm-linux-gnueabihf/` | `libmali-bifrost-g31-rxp0-gbm.so` | 32-bit, GBM only |
| `/usr/local/lib/arm-linux-gnueabihf/` | `libmali.so` | Symlink to above |

**Non-working Mali libraries** (`/usr/lib/`):
| Path | File | Notes |
|------|------|-------|
| `/usr/lib/aarch64-linux-gnu/` | `libmali-bifrost-g31-rxp0-wayland-gbm.so` | Wayland variant, missing GBM symbols |
| `/usr/lib/aarch64-linux-gnu/` | `libMali.so`, `libmali.so`, `libmali.so.1` | Symlinks |

### libgo2 Abstraction Library

The ODROID-GO2 library provides hardware abstraction:
| Path | Size | Date |
|------|------|------|
| `/usr/lib/aarch64-linux-gnu/libgo2.so` | 39840 | Apr 2021 |
| `/usr/lib/aarch64-linux-gnu/libgo2.so.bak` | 39864 | Mar 2020 |
| `/usr/lib/aarch64-linux-gnu/libgo2.so.last` | 91120 | Feb 2021 |
| `/usr/lib/arm-linux-gnueabihf/libgo2.so` | - | - |
| `/usr/local/bin/libgo2.so` | - | Unusual location |

### Why Our GPU Attempts Failed

We were using the wrong Mali library variant:
1. **wayland-gbm variant** (`/usr/lib/`) - missing `gbm_bo_unmap`, `gbm_bo_get_plane_count`
2. **gbm variant** (`/usr/local/lib/`) - used by EmulationStation, may have these symbols

### Next Steps for GPU Acceleration

1. **TESTED - /usr/local/lib Mali also missing GBM symbols**:
   - `nm -D` shows no `gbm_bo_unmap` or `gbm_bo_get_plane_count`
   - `LD_LIBRARY_PATH=/usr/local/lib/aarch64-linux-gnu kmscube` fails with same error
   - Both Mali variants are equally old

2. **TESTED - Qt eglfs shows black screen**:
   - Qt eglfs platform connects to EGL (no Mali symbol errors!)
   - But renders black screen with warnings
   - See "Qt eglfs Test Results" section below

3. **Debug ROCKNIX boot failure** - uses Panfrost which has proper GBM

## Qt eglfs Test Results (2025-12-10)

Qt eglfs bypasses GBM and talks directly to EGL/DRM. Tests show EGL is working but display is black:

```bash
# Kill emulationstation first
pkill -f emulationstation

# Test Qt OpenGL cube with debug
QT_QPA_EGLFS_DEBUG=1 QT_QPA_PLATFORM=eglfs /usr/lib/aarch64-linux-gnu/qt5/examples/opengl/cube/cube
```

**Debug output shows EGL working correctly:**
```
Created context for format QSurfaceFormat(version 2.0, ...) with config:
    EGL_BUFFER_SIZE: 24
    EGL_RED_SIZE: 8, EGL_GREEN_SIZE: 8, EGL_BLUE_SIZE: 8
    EGL_DEPTH_SIZE: 24
    EGL_STENCIL_SIZE: 8
    EGL_MAX_PBUFFER_WIDTH: 8192, EGL_MAX_PBUFFER_HEIGHT: 8192
    EGL_SURFACE_TYPE: 1029
    EGL_BIND_TO_TEXTURE_RGB: 1
```
Result: EGL context created successfully, but black screen

**Warnings:**
- `Setting framebuffer size is only available with DRM atomic API` - kernel 4.4.189 lacks atomic modesetting
- `Attribute Qt::AA_ShareOpenGLContexts must be set before QCoreApplication is created` - Qt example code issue

**Analysis:**
- **EGL is working** - Mali EGL creates valid OpenGL ES 2.0 contexts
- **GPU rendering likely working** - no errors from Mali driver
- **Display pipeline issue** - rendered content not reaching screen
- Likely cause: Qt eglfs can't set up DRM/KMS scanout without atomic API
- The kernel 4.4.189 predates DRM atomic modesetting support

**Next steps to debug:**
- Try `QT_QPA_EGLFS_INTEGRATION=eglfs_kms_egldevice` (uses EGLDevice instead of GBM)
- Try linuxfb platform: `QT_QPA_PLATFORM=linuxfb`
- Check if EmulationStation uses a different EGL surface type
- Investigate how ES presents frames without atomic modesetting

## SDL2 Investigation (2025-12-10)

**Key finding**: System pygame uses SDL 1.2, but SDL2 with KMSDRM is available.

### pygame SDL version mismatch
```bash
ldd /usr/lib/python3/dist-packages/pygame/*.so | grep -i sdl
# libSDL-1.2.so.0 => /lib/aarch64-linux-gnu/libSDL-1.2.so.0
```
pygame 1.9.4 is linked against ancient SDL 1.2, which lacks KMSDRM support.

### System SDL2 has KMSDRM
```bash
strings /usr/lib/aarch64-linux-gnu/libSDL2-2.0.so.0 | grep -i kmsdrm
# SDL_KMSDRM_DEVICE_INDEX
# SDL_KMSDRM_REQUIRE_DRM_MASTER
# KMSDRM
# KMSDRM_VideoInit()
```

### EmulationStation uses system SDL2
```bash
ldd /usr/bin/emulationstation/emulationstation | grep -i sdl
# libSDL2-2.0.so.0 => /lib/aarch64-linux-gnu/libSDL2-2.0.so.0
```
No custom SDL2 in `/usr/local/lib/` - ES uses the standard system SDL2 with KMSDRM.

### PySDL2 installed
```bash
apt install python3-sdl2
# Installed: python3-sdl2 0.9.6, libsdl2-gfx, libsdl2-image, libsdl2-ttf
```

### PySDL2 KMSDRM Test Results (2025-12-10)

**Result: Black screen (no errors)**

```bash
# Kill emulationstation first!
pkill -f emulationstation

SDL_VIDEODRIVER=kmsdrm python3 -c "
import sdl2
import sdl2.ext
sdl2.ext.init()
window = sdl2.ext.Window('Test', size=(720, 720), flags=sdl2.SDL_WINDOW_FULLSCREEN)
window.show()
surface = window.get_surface()
sdl2.ext.fill(surface, sdl2.ext.Color(255, 0, 0))
window.refresh()
import time
time.sleep(3)"
```

**Analysis:**
- SDL2 KMSDRM initializes without errors
- Window created, surface filled with red, refreshed
- But display shows black - same as Qt eglfs
- This rules out Qt-specific issues

**Pattern:** Both Qt eglfs and SDL2 KMSDRM can initialize display but rendered content doesn't reach screen. The problem is in the DRM/KMS scanout layer, not the rendering layer.

**Key question:** How does EmulationStation differ? It uses the same SDL2 library. Possibilities:
1. ES uses a different SDL2 video driver (not KMSDRM?)
2. ES uses OpenGL ES rendering which takes a different path
3. ES uses specific DRM plane/CRTC configuration
4. The software rendering path (get_surface/fill) doesn't work, but OpenGL does

### SDL2 + OpenGL ES Test Results (2025-12-10)

**Result: Black screen, GL queries return None**

```bash
pkill -f emulationstation
SDL_VIDEODRIVER=kmsdrm python3 test-sdl2-opengl.py
```

**Output:**
```
Starting SDL2 OpenGL ES test...
Initializing SDL2...
SDL2 initialized
Window created successfully
Creating OpenGL context...
OpenGL context created successfully
GL Vendor: None
GL Renderer: None
GL Version: None
Clearing to red...
Clearing to green...
Clearing to blue...
Cleaning up...
Done
```

**Analysis:**
- SDL2 KMSDRM initializes successfully
- OpenGL ES 2.0 context created successfully
- But `glGetString()` returns None for GL_VENDOR, GL_RENDERER, GL_VERSION
- Screen stays black despite glClear + SwapWindow calls

**Root cause hypothesis:**
PyOpenGL may be loading the wrong GL library (mesa's libGL instead of Mali's libGLESv2).
The GL context exists but isn't properly connected to Mali hardware.

**Next steps to investigate:**
1. Check which GL library PyOpenGL loads: `python3 -c "from OpenGL.GL import *; import OpenGL; print(OpenGL.__file__)"`
2. Try forcing GLES2: `from OpenGL.GLES2 import *` instead of `from OpenGL.GL import *`
3. Check if ES uses `LD_LIBRARY_PATH=/usr/local/lib/aarch64-linux-gnu` to find Mali libs
4. Try running with Mali lib path: `LD_LIBRARY_PATH=/usr/local/lib/aarch64-linux-gnu:$LD_LIBRARY_PATH SDL_VIDEODRIVER=kmsdrm python3 test-sdl2-opengl.py`

### EmulationStation uses OpenGL ES
ES definitely uses GPU acceleration - it has animated menus, transitions, and renders game art with effects. The library chain shows it links to:
- `libEGL.so` from `/usr/local/lib/aarch64-linux-gnu/`
- `libGLES_CM.so` (OpenGL ES 1.x Common profile)

This confirms SDL2+EGL+GLES works on this device. The question is how ES presents frames - our SDL2 software rendering test shows black screen, so ES must use a different rendering path (likely OpenGL ES).

## Known Issues
- **ldconfig warnings** - Multiple ArkOS libraries (SDL2, Qt5) are regular files instead of symlinks, causing warnings but not affecting functionality
- **Mali GBM too old** - BOTH variants (`/usr/lib/` wayland-gbm AND `/usr/local/lib/` gbm) missing `gbm_bo_unmap`, `gbm_bo_get_plane_count`
- **Mali version mismatch** - Kernel 11.7, no compatible userspace found (need 11.7-11.11)
- **ROCKNIX boot failure** - R36S image doesn't boot, no R36S Plus specific image exists
- **ArkOS packages removed** - emulationstation-go2, libgo2, retrorun-go2, utils-go2 not in repos
- Mali Xorg driver fails to load ("maliModuleData" error) - incompatible with Xorg 1.20.5
- X server uses modesetting driver, not Mali driver
- All 3D/OpenGL uses software rendering (swrast) - no GPU acceleration under X11
- TTY permissions reset on reboot (launch.sh handles this)
- Roms partition nearly full (99% used)
- Ubuntu 19.10 repos have limited Wayland compositor options

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

## References

Repo for getting xorg and xfce working on similar devices:

- <https://github.com/OkJacket2022/R36S-Xorg>
- <https://github.com/OkJacket2022/R36S-Xorg/blob/main/XFCE/Install-XFCE.sh>

ArkOS wiki:

- [ArkOS Wiki](https://github.com/christianhaitian/arkos/wiki)

ArkOS-R3XS (community maintained for R36S):

- [ArkOS-R3XS GitHub](https://github.com/AeolusUX/ArkOS-R3XS)
- [ArkOS-R3XS Releases](https://github.com/AeolusUX/ArkOS-R3XS/releases)
- [RetroHandhelds Discord](https://discord.gg/RetroHandhelds)

Mali GPU documentation (note: these are for older Mali-400/Utgard, not Mali-G31/Bifrost):

- [Mali Binary Driver Wiki](context-video/mali-binary-driver.wiki)
- [Mali Xorg Wiki](context-video/mali-xorg.wiki)

Rockchip Mali libraries:

- [rockchip-linux/libmali](https://github.com/rockchip-linux/libmali) - Official Rockchip Mali userspace

JeffyCN Mali mirrors (has g2p0, g13p0, g24p0 - none compatible with kernel 11.7):

- [JeffyCN/mirrors libmali branch](https://github.com/JeffyCN/mirrors/tree/libmali/lib/aarch64-linux-gnu)

tsukumijima pre-built packages (require newer libc than Ubuntu 19.10):

- [tsukumijima/libmali-rockchip releases](https://github.com/tsukumijima/libmali-rockchip/releases)

ODROID Mali packages (r13p0 - used by ArkOS):

- [ODROID RK3326 downloads](https://dn.odroid.com/RK3326/ODROID-GO-Advance/)
- [ODROID Vulkan on RK3326](https://wiki.odroid.com/odroid_go_advance/application_note/vulkan_on_rk3326)

ARM Mali kernel driver source (userspace not included):

- [ARM Bifrost GPU Kernel Drivers](https://developer.arm.com/Downloads/-/Bifrost%20Mali%203rd%20Gen%20GPU%20Architecture)
- r11p0 kernel source available (dated 2018-03-09) but userspace is commercial-only

Alternative OSes for RK3326:

- [ROCKNIX](https://github.com/ROCKNIX/distribution) - JELOS successor, R36S supported, Panfrost GPU (boot failed - may need different SD card/flash method)
- [JELOS](https://github.com/JustEnoughLinuxOS/distribution) - Archived, but has RK3326 support
