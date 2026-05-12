import sys
import os

# Enable remote debugging on port 9222
os.environ["QTWEBENGINE_REMOTE_DEBUGGING"] = "9222"

# Disable sandbox so the renderer process can read /dev/input/event*
os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"

from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage

class CustomWebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        print(f"JS: {message} ({sourceID}:{lineNumber})", flush=True)

app = QApplication(sys.argv)
window = QMainWindow()
view = QWebEngineView()
page = CustomWebEnginePage(view)
view.setPage(page)

# Load external index.html
html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
view.setUrl(QUrl.fromLocalFile(html_path))

window.setCentralWidget(view)
window.showFullScreen()

# Ensure the WebView receives input focus
view.setFocus()

sys.exit(app.exec_())
