import sys
import os
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView

app = QApplication(sys.argv)
window = QMainWindow()
view = QWebEngineView()

# Load external index.html
html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
view.setUrl(QUrl.fromLocalFile(html_path))

window.setCentralWidget(view)
window.showFullScreen()

sys.exit(app.exec_())
