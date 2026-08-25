"""Navigation sidebar."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QPushButton, QScrollArea, QVBoxLayout, QWidget

SECTIONS: list[tuple[str, str, str]] = [
    ("dashboard", "🏠", "Dashboard"),
    ("history", "🕘", "History"),
    ("settings", "⚙", "Settings"),
    ("about", "❓", "About / Diagnostics"),
]


class Sidebar(QWidget):
    section_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(210)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 16, 12, 14)
        outer.setSpacing(2)

        scroll = QScrollArea()
        scroll.setObjectName("NavScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        inner = QWidget()
        inner.setObjectName("NavInner")
        nav = QVBoxLayout(inner)
        nav.setContentsMargins(0, 0, 0, 0)
        nav.setSpacing(2)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons: dict[str, QPushButton] = {}
        for key, icon, label in SECTIONS:
            btn = QPushButton(f"{icon}   {label}")
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, k=key: self.section_selected.emit(k))
            self._group.addButton(btn)
            self._buttons[key] = btn
            nav.addWidget(btn)
        nav.addStretch()
        scroll.setWidget(inner)
        outer.addWidget(scroll, 1)

    def select(self, key: str) -> None:
        if key in self._buttons:
            self._buttons[key].setChecked(True)
