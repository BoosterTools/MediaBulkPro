"""Generic background-task runner for one-off work (URL extraction, channel
expansion, etc.) that must not block the GUI thread."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QThread, Signal


class _Signals(QObject):
    finished = Signal(object)
    error = Signal(str)


class TaskThread(QThread):
    def __init__(self, fn: Callable[..., Any], *args: Any, parent: QObject | None = None,
               **kwargs: Any) -> None:
        super().__init__(parent)
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self.signals = _Signals()

    def run(self) -> None:
        try:
            result = self._fn(*self._args, **self._kwargs)
        except Exception as exc:  # noqa: BLE001 - surfaced to the UI, not swallowed
            self.signals.error.emit(str(exc))
            return
        self.signals.finished.emit(result)
