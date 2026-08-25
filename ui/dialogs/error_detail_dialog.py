"""User-friendly failure dialog with an optional raw-details expander.

Never shows a raw Python traceback to the ordinary user by default.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

_FRIENDLY_MESSAGE = (
    "Something went wrong. The media could not be downloaded.\n\n"
    "Possible causes:\n"
    "\u2022 The URL is unavailable\n"
    "\u2022 The content is restricted\n"
    "\u2022 The platform changed its format\n"
    "\u2022 Network connection failed"
)


class ErrorDetailDialog(QDialog):
    def __init__(self, technical_detail: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Download failed")
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)

        label = QLabel(_FRIENDLY_MESSAGE)
        label.setWordWrap(True)
        layout.addWidget(label)

        self.details = QPlainTextEdit(technical_detail)
        self.details.setReadOnly(True)
        self.details.setVisible(False)
        self.details.setMaximumHeight(140)
        layout.addWidget(self.details)

        self.toggle_btn = QPushButton("View Details")
        self.toggle_btn.clicked.connect(self._toggle)
        layout.addWidget(self.toggle_btn)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def _toggle(self) -> None:
        self.details.setVisible(not self.details.isVisible())
        self.toggle_btn.setText("Hide Details" if self.details.isVisible() else "View Details")
