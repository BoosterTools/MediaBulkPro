"""Channel/playlist/profile expansion dialog:

"Playlist detected — 87 videos found [Add All] [Select Videos] [Cancel]"

Lets the user pick individual items before they get queued, per the spec.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from app.downloader.models import CollectionEntry


class CollectionDialog(QDialog):
    def __init__(self, source_label: str, entries: list[CollectionEntry], parent=None) -> None:
        super().__init__(parent)
        self.entries = entries
        self.setWindowTitle("Collection Detected")
        self.setMinimumSize(480, 460)
        layout = QVBoxLayout(self)

        heading = QLabel(f"{source_label}\n{len(entries)} videos found")
        heading.setObjectName("SectionTitle")
        layout.addWidget(heading)

        self.list_widget = QListWidget()
        for entry in entries:
            label = entry.title or entry.url
            item = QListWidgetItem(label)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget, 1)

        select_row = QHBoxLayout()
        select_all = QPushButton("Select All")
        select_all.clicked.connect(lambda: self._set_all(Qt.CheckState.Checked))
        select_none = QPushButton("Select None")
        select_none.clicked.connect(lambda: self._set_all(Qt.CheckState.Unchecked))
        select_row.addWidget(select_all)
        select_row.addWidget(select_none)
        select_row.addStretch()
        layout.addLayout(select_row)

        buttons = QDialogButtonBox()
        self.add_all_btn = buttons.addButton("Add All", QDialogButtonBox.ButtonRole.AcceptRole)
        self.add_selected_btn = buttons.addButton("Add Selected", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
        self.add_all_btn.clicked.connect(self._accept_all)
        self.add_selected_btn.clicked.connect(self._accept_selected)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._result_urls: list[str] = []

    def _set_all(self, state) -> None:
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(state)

    def _accept_all(self) -> None:
        self._result_urls = [e.url for e in self.entries]
        self.accept()

    def _accept_selected(self) -> None:
        self._result_urls = [
            self.entries[i].url for i in range(self.list_widget.count())
            if self.list_widget.item(i).checkState() == Qt.CheckState.Checked
        ]
        self.accept()

    def selected_urls(self) -> list[str]:
        return self._result_urls
