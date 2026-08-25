"""Optional clipboard watcher: detects a supported URL on the clipboard and
offers to add it to the queue. Never downloads automatically unless the
user has explicitly enabled that in Settings."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from app.platforms.detector import detect


class ClipboardMonitor(QObject):
    url_detected = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._last_seen: str | None = None
        self._enabled = False
        QApplication.clipboard().dataChanged.connect(self._on_clipboard_changed)

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def _on_clipboard_changed(self) -> None:
        if not self._enabled:
            return
        text = QApplication.clipboard().text().strip()
        if not text or text == self._last_seen:
            return
        self._last_seen = text
        match = detect(text)
        if match.is_supported:
            self.url_detected.emit(text)
