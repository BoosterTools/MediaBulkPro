"""The bulk download queue table: thumbnail/title/platform/duration/quality/
status/progress/speed columns, drag-to-reorder, and a right-click context menu."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QMenu,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
)

from app.database.repositories import QueueItem
from app.utils.formatting import human_duration, human_speed

COLUMNS = ["#", "Title", "Platform", "Duration", "Quality", "Status", "Progress", "Speed"]

_STATUS_LABELS = {
    "queued": "Queued", "extracting": "Extracting…", "downloading": "Downloading",
    "paused": "Paused", "completed": "Completed", "failed": "Failed",
    "cancelled": "Cancelled", "skipped_duplicate": "Already downloaded",
}


class QueueTable(QTableWidget):
    pause_requested = Signal(int)
    resume_requested = Signal(int)
    retry_requested = Signal(int)
    cancel_requested = Signal(int)
    remove_requested = Signal(int)
    copy_url_requested = Signal(int)
    open_file_requested = Signal(int)
    open_folder_requested = Signal(int)
    view_error_requested = Signal(int)
    reordered = Signal(list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setColumnCount(len(COLUMNS))
        self.setHorizontalHeaderLabels(COLUMNS)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._id_by_row: dict[int, int] = {}

    def set_items(self, items: list[QueueItem]) -> None:
        self.setRowCount(len(items))
        self._id_by_row.clear()
        for row, item in enumerate(items):
            self._id_by_row[row] = item.id
            self.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.setItem(row, 1, QTableWidgetItem(item.title or item.url))
            self.setItem(row, 2, QTableWidgetItem(item.platform.title()))
            self.setItem(row, 3, QTableWidgetItem(human_duration(item.duration_secs)))
            self.setItem(row, 4, QTableWidgetItem(item.quality))
            status_item = QTableWidgetItem(_STATUS_LABELS.get(item.status, item.status))
            if item.status == "failed":
                status_item.setToolTip(item.error_message or "")
            self.setItem(row, 5, status_item)

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(int(item.progress))
            self.setCellWidget(row, 6, bar)

            speed_text = human_speed(item.speed_bps) if item.status == "downloading" else "—"
            self.setItem(row, 7, QTableWidgetItem(speed_text))

    def item_id_for_row(self, row: int) -> int | None:
        return self._id_by_row.get(row)

    def selected_ids(self) -> list[int]:
        rows = {idx.row() for idx in self.selectedIndexes()}
        return [self._id_by_row[r] for r in sorted(rows) if r in self._id_by_row]

    def _show_context_menu(self, pos) -> None:
        row = self.rowAt(pos.y())
        if row < 0 or row not in self._id_by_row:
            return
        item_id = self._id_by_row[row]
        menu = QMenu(self)
        menu.addAction("Start / Resume", lambda: self.resume_requested.emit(item_id))
        menu.addAction("Pause", lambda: self.pause_requested.emit(item_id))
        menu.addAction("Retry", lambda: self.retry_requested.emit(item_id))
        menu.addAction("Cancel", lambda: self.cancel_requested.emit(item_id))
        menu.addSeparator()
        menu.addAction("Open File", lambda: self.open_file_requested.emit(item_id))
        menu.addAction("Open Containing Folder", lambda: self.open_folder_requested.emit(item_id))
        menu.addAction("Copy URL", lambda: self.copy_url_requested.emit(item_id))
        menu.addSeparator()
        menu.addAction("View Error Details", lambda: self.view_error_requested.emit(item_id))
        menu.addSeparator()
        menu.addAction("Remove", lambda: self.remove_requested.emit(item_id))
        menu.exec(self.viewport().mapToGlobal(pos))

    def dropEvent(self, event) -> None:  # noqa: N802 - Qt naming
        super().dropEvent(event)
        ordered = [self._id_by_row[r] for r in range(self.rowCount()) if r in self._id_by_row]
        self.reordered.emit(ordered)
