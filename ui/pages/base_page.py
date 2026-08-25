"""Base class for all main-content pages."""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.core.app_context import AppContext


class BasePage(QWidget):
    key: str = "base"
    title: str = "Page"
    subtitle: str = ""

    def __init__(self, ctx: AppContext, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ctx = ctx
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(28, 24, 28, 24)
        self.layout_.setSpacing(16)

        header = QHBoxLayout()
        text = QVBoxLayout()
        t = QLabel(self.title)
        t.setObjectName("PageTitle")
        text.addWidget(t)
        if self.subtitle:
            s = QLabel(self.subtitle)
            s.setObjectName("PageSubtitle")
            text.addWidget(s)
        header.addLayout(text)
        header.addStretch()
        self.header_actions = QHBoxLayout()
        header.addLayout(self.header_actions)
        self.layout_.addLayout(header)

    def on_show(self) -> None:
        """Called each time the page becomes visible. Override to refresh data."""
