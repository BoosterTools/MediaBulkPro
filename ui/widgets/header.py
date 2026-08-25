"""Top header bar: brand, theme switcher, settings/downloads-folder/help shortcuts."""

from __future__ import annotations

import os
import subprocess
import sys

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.core.config import APP_NAME, APP_SUBTITLE


class Header(QWidget):
    theme_toggle_requested = Signal()
    settings_requested = Signal()
    about_requested = Signal()

    def __init__(self, downloads_dir: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Header")
        self._downloads_dir = downloads_dir
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)

        text = QVBoxLayout()
        title = QLabel(APP_NAME)
        title.setObjectName("BrandTitle")
        subtitle = QLabel(APP_SUBTITLE)
        subtitle.setObjectName("BrandSubtitle")
        text.addWidget(title)
        text.addWidget(subtitle)
        layout.addLayout(text)
        layout.addStretch()

        theme_btn = QPushButton("🌓 Theme")
        theme_btn.clicked.connect(self.theme_toggle_requested.emit)
        layout.addWidget(theme_btn)

        folder_btn = QPushButton("📁 Download Folder")
        folder_btn.clicked.connect(self._open_downloads_folder)
        layout.addWidget(folder_btn)

        settings_btn = QPushButton("⚙ Settings")
        settings_btn.clicked.connect(self.settings_requested.emit)
        layout.addWidget(settings_btn)

        help_btn = QPushButton("❓ Help")
        help_btn.clicked.connect(self.about_requested.emit)
        layout.addWidget(help_btn)

    def set_downloads_dir(self, path: str) -> None:
        self._downloads_dir = path

    def _open_downloads_folder(self) -> None:
        os.makedirs(self._downloads_dir, exist_ok=True)
        if sys.platform.startswith("win"):
            os.startfile(self._downloads_dir)  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.Popen(["open", self._downloads_dir])  # noqa: S603,S607
        else:
            subprocess.Popen(["xdg-open", self._downloads_dir])  # noqa: S603,S607
