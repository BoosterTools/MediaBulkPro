"""Applies light/dark/system themes and notifies widgets when it changes."""

from __future__ import annotations

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

from ui.theme.palette import DARK, LIGHT, Palette
from ui.theme.stylesheet import build_stylesheet

THEMES = ("light", "dark", "system")


class ThemeManager(QObject):
    theme_changed = Signal(Palette)

    def __init__(self, app: QApplication) -> None:
        super().__init__()
        self._app = app
        self._mode = "system"
        self._palette = LIGHT
        hints = QGuiApplication.styleHints()
        if hasattr(hints, "colorSchemeChanged"):
            hints.colorSchemeChanged.connect(self._on_system_change)

    @property
    def palette(self) -> Palette:
        return self._palette

    @property
    def mode(self) -> str:
        return self._mode

    def apply(self, mode: str) -> None:
        if mode not in THEMES:
            mode = "system"
        self._mode = mode
        self._palette = self._resolve(mode)
        self._app.setStyleSheet(build_stylesheet(self._palette))
        self.theme_changed.emit(self._palette)

    def _resolve(self, mode: str) -> Palette:
        if mode == "dark":
            return DARK
        if mode == "light":
            return LIGHT
        hints = QGuiApplication.styleHints()
        scheme = getattr(hints, "colorScheme", lambda: None)()
        return DARK if scheme == Qt.ColorScheme.Dark else LIGHT

    def _on_system_change(self, *_: object) -> None:
        if self._mode == "system":
            self.apply("system")
