"""Base class for all main-content pages."""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from app.core.app_context import AppContext


class BasePage(QWidget):
    key: str = "base"
    title: str = "Page"
    subtitle: str = ""

    def __init__(self, ctx: AppContext, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ctx = ctx

        # Every page's content sits inside a scroll area rather than
        # directly on the page widget. Without this, a page whose content
        # is taller than the current window (e.g. Settings with five
        # stacked sections) doesn't get force-compressed/overlapping —
        # Qt has no way to "shrink to fit" a QVBoxLayout gracefully, so
        # without scrolling it just squashes every row's height toward its
        # minimum, which is exactly what caused Settings to look broken.
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setObjectName("PageScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        content.setObjectName("PageContent")
        self.layout_ = QVBoxLayout(content)
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

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def on_show(self) -> None:
        """Called each time the page becomes visible. Override to refresh data."""
