import sys
import os

# Enable remote debugging on port 9222
os.environ["QTWEBENGINE_REMOTE_DEBUGGING"] = "9222"

# Disable sandbox so the renderer process can read /dev/input/event*
os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"

import re
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile

class CustomWebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        print(f"JS: {message} ({sourceID}:{lineNumber})", flush=True)

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

window = QMainWindow()
view = QWebEngineView()
page = CustomWebEnginePage(profile, view)
view.setPage(page)

view.setUrl(url)

window.setCentralWidget(view)
window.showFullScreen()

# Ensure the WebView receives input focus
view.setFocus()

sys.exit(app.exec_())
