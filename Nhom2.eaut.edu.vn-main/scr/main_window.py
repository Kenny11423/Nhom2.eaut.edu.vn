from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QCoreApplication, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView

from src.train_ticket_app.backend.bridge import AppBridge
from src.train_ticket_app.backend.database import DatabaseManager


BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
DATA_DIR = BASE_DIR.parent.parent / "data"


def run() -> None:
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    QGuiApplication.setAttribute(Qt.ApplicationAttribute.AA_UseSoftwareOpenGL)
    app = QApplication(sys.argv)
    app.setApplicationName("Train Ticket Manager")

    database = DatabaseManager(DATA_DIR / "train_ticket.db")
    database.initialize()

    bridge = AppBridge(database)
    channel = QWebChannel()
    channel.registerObject("bridge", bridge)

    view = QWebEngineView()
    view.setWindowTitle("Phan mem quan ly ban ve tau")
    view.resize(1440, 920)
    view.page().setWebChannel(channel)
    view.load(QUrl.fromLocalFile(str(ASSETS_DIR / "index.html")))
    view.show()

    sys.exit(app.exec())
