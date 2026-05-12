import sys
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView

app = QApplication(sys.argv)
window = QMainWindow()
view = QWebEngineView()

# A simple high-contrast Hello World
html = """
<html>
<body style='background: #222; color: #0f0; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;'>
    <h1>Hello Hardware Accelerated World!</h1>
</body>
</html>
"""
view.setHtml(html)

window.setCentralWidget(view)
window.showFullScreen()

sys.exit(app.exec_())
