"""Thin Qt bridge around the Qt-free QueueManager.

QueueManager reports activity via a plain callback invoked from background
threads; this wraps that in a QObject signal, which Qt automatically
marshals onto the GUI thread for any connected slot (auto connection across
threads is queued by default), so pages never touch queue internals from a
worker thread directly.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from app.queue.manager import QueueManager
from app.queue.models import QueueEvent


class QueueController(QObject):
    event_occurred = Signal(QueueEvent)

    def __init__(self, manager: QueueManager, parent=None) -> None:
        super().__init__(parent)
        self.manager = manager
        manager.on_event = self._on_event

    def _on_event(self, event: QueueEvent) -> None:
        self.event_occurred.emit(event)
