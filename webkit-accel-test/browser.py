import sys
import os
import threading
import time

# Enable remote debugging on port 9222
os.environ["QTWEBENGINE_REMOTE_DEBUGGING"] = "9222"

# Disable sandbox so the renderer process can read /dev/input/event*
os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"

import re
import json
import subprocess
from PyQt5.QtCore import QUrl, QObject, pyqtSlot
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile, QWebEngineScript
from PyQt5.QtWebChannel import QWebChannel

class CustomWebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        print(f"JS: {message} ({sourceID}:{lineNumber})", flush=True)

class SystemApi(QObject):
    @pyqtSlot(list, result=str)
    def nmcli(self, args):
        try:
            cmd = ['sudo', 'nmcli'] + [str(a) for a in args]
            res = subprocess.run(cmd, capture_output=True, text=True)
            return json.dumps({"code": res.returncode, "stdout": res.stdout, "stderr": res.stderr})
        except Exception as e:
            return json.dumps({"code": -1, "stdout": "", "stderr": str(e)})

    @pyqtSlot(result=list)
    def connections(self):
        try:
            res = subprocess.run(['sudo', 'ls', '-1', '/etc/NetworkManager/system-connections/'], capture_output=True, text=True)
            if res.returncode == 0:
                return [f for f in res.stdout.strip().split('\n') if f]
            return []
        except Exception as e:
            print(f"Error listing connections: {e}", flush=True)
            return []

    @pyqtSlot(result=str)
    def check_update(self):
        try:
            repo_dir = "/home/ark/r36s-web-console"
            if not os.path.exists(repo_dir):
                return json.dumps({"code": -1, "error": "Repo not found"})
            
            local = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=repo_dir, capture_output=True, text=True).stdout.strip()
            remote = subprocess.run(['git', 'rev-parse', 'origin/main'], cwd=repo_dir, capture_output=True, text=True).stdout.strip()
            
            return json.dumps({"code": 0, "update_available": bool(local and remote and local != remote)})
        except Exception as e:
            return json.dumps({"code": -1, "error": str(e)})

    @pyqtSlot(result=str)
    def update_system(self):
        try:
            repo_dir = "/home/ark/r36s-web-console"
            if not os.path.exists(repo_dir):
                return json.dumps({"code": -1, "error": "Repo not found"})
            
            subprocess.run(['git', 'reset', '--hard', 'origin/main'], cwd=repo_dir, capture_output=True, text=True, check=True)
            
            print("Update applied. Restarting service...", flush=True)
            subprocess.Popen(['sudo', 'systemctl', 'restart', 'web-console'])
            return json.dumps({"code": 0, "status": "updated"})
        except Exception as e:
            print(f"Update failed: {e}", flush=True)
            return json.dumps({"code": -1, "error": str(e)})

def auto_update_thread():
    print("Background fetch thread started...", flush=True)
    while True:
        # Check network
        res = subprocess.run(['ping', '-c', '1', '-W', '2', '8.8.8.8'], capture_output=True)
        if res.returncode == 0:
            try:
                repo_dir = "/home/ark/r36s-web-console"
                if os.path.exists(repo_dir):
                    subprocess.run(['git', 'fetch', 'origin'], cwd=repo_dir, capture_output=True, text=True)
            except Exception as e:
                print(f"Background fetch failed: {e}", flush=True)
        # Wait 5 minutes before fetching again
        time.sleep(300)

threading.Thread(target=auto_update_thread, daemon=True).start()

app = QApplication(sys.argv)

# Determine URL
if len(sys.argv) > 1:
    url_str = sys.argv[1]
    if not url_str.startswith('http') and not url_str.startswith('file'):
        url_str = 'http://' + url_str
    url = QUrl(url_str)
else:
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    url = QUrl.fromLocalFile(html_path)

# Slugify hostname or filename
if url.isLocalFile():
    slug = os.path.basename(url.toLocalFile())
else:
    slug = url.host()
    if not slug:
        slug = "default"
slug = re.sub(r'[^a-zA-Z0-9\-]', '_', slug)

# Configure persistent storage
storage_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".storage", slug))
os.makedirs(storage_path, exist_ok=True)
print(f"Using storage path: {storage_path}", flush=True)

profile = QWebEngineProfile.defaultProfile()
profile.setPersistentStoragePath(storage_path)
profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)

# Inject Gamepad Polyfill to map R36S to W3C Standard
gamepad_polyfill = """
(function() {
    const origGetGamepads = navigator.getGamepads.bind(navigator);
    navigator.getGamepads = function() {
        const pads = origGetGamepads();
        const remapped = [];
        for (let i = 0; i < pads.length; i++) {
            const gp = pads[i];
            if (gp && gp.mapping === "") {
                remapped.push(new Proxy(gp, {
                    get: function(target, prop) {
                        if (prop === 'mapping') return 'standard';
                        if (prop === 'buttons') {
                            const b = target.buttons;
                            const std = [];
                            for(let j=0; j<17; j++) std.push({pressed: false, touched: false, value: 0});
                            const mapBtn = (stdIdx, r36sIdx) => { if (b[r36sIdx]) std[stdIdx] = b[r36sIdx]; };
                            mapBtn(0, 0);   // B -> Bottom
                            mapBtn(1, 1);   // A -> Right
                            mapBtn(2, 3);   // Y -> Left
                            mapBtn(3, 2);   // X -> Top
                            mapBtn(4, 4);   // L1
                            mapBtn(5, 5);   // R1
                            mapBtn(6, 6);   // L2
                            mapBtn(7, 7);   // R2
                            mapBtn(8, 12);  // Select
                            mapBtn(9, 13);  // Start
                            mapBtn(10, 14); // L3
                            mapBtn(11, 15); // R3
                            mapBtn(12, 8);  // D-Pad Up
                            mapBtn(13, 9);  // D-Pad Down
                            mapBtn(14, 10); // D-Pad Left
                            mapBtn(15, 11); // D-Pad Right
                            mapBtn(16, 16); // Special
                            return std;
                        }
                        if (prop === 'axes') {
                            const a = target.axes;
                            const std = [0, 0, 0, 0];
                            if (a.length > 0) std[0] = a[0];
                            if (a.length > 1) std[1] = a[1];
                            if (a.length > 2) std[2] = a[2];
                            if (a.length > 3) std[3] = a[3];
                            return std;
                        }
                        const value = target[prop];
                        return typeof value === 'function' ? value.bind(target) : value;
                    }
                }));
            } else {
                remapped.push(gp);
            }
        }
        return remapped;
    };
})();
"""
script = QWebEngineScript()
script.setName("GamepadPolyfill")
script.setSourceCode(gamepad_polyfill)
script.setInjectionPoint(QWebEngineScript.DocumentCreation)
script.setWorldId(QWebEngineScript.MainWorld)
script.setRunsOnSubFrames(True)
profile.scripts().insert(script)

window = QMainWindow()
view = QWebEngineView()
page = CustomWebEnginePage(profile, view)

channel = QWebChannel()
system_api = SystemApi()
channel.registerObject("systemApi", system_api)
page.setWebChannel(channel)

view.setPage(page)

view.setUrl(url)

window.setCentralWidget(view)
window.showFullScreen()

# Ensure the WebView receives input focus
view.setFocus()

sys.exit(app.exec_())
