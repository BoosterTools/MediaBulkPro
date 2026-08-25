"""Download History: search, filter, sort, export, clear."""

from __future__ import annotations

import csv
from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from app.core.app_context import AppContext
from app.utils.formatting import human_size
from ui.dialogs.confirm_dialog import confirm, notify
from ui.pages.base_page import BasePage

PLATFORM_FILTERS = ["all", "youtube", "instagram", "tiktok"]
STATUS_FILTERS = ["all", "completed", "failed"]


class HistoryPage(BasePage):
    key = "history"
    title = "Download History"
    subtitle = "Every completed and failed download"

    def __init__(self, ctx: AppContext, parent: QWidget | None = None) -> None:
        super().__init__(ctx, parent)

        controls = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search by title or URL…")
        self.search_edit.textChanged.connect(self._refresh)
        controls.addWidget(self.search_edit, 1)

        self.platform_combo = QComboBox()
        for p in PLATFORM_FILTERS:
            self.platform_combo.addItem(p.title() if p != "all" else "All Platforms", p)
        self.platform_combo.currentIndexChanged.connect(self._refresh)
        controls.addWidget(self.platform_combo)

        self.status_combo = QComboBox()
        for s in STATUS_FILTERS:
            self.status_combo.addItem(s.title() if s != "all" else "All Statuses", s)
        self.status_combo.currentIndexChanged.connect(self._refresh)
        controls.addWidget(self.status_combo)

        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self._export)
        controls.addWidget(self.export_btn)
        self.clear_btn = QPushButton("Clear History")
        self.clear_btn.clicked.connect(self._clear)
        controls.addWidget(self.clear_btn)
        self.layout_.addLayout(controls)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Title", "Platform", "Date", "Size", "Quality", "Status"])
        self.table.setMinimumHeight(360)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.layout_.addWidget(self.table, 1)

    def on_show(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        rows = self.ctx.history.search(
            query=self.search_edit.text(), platform=self.platform_combo.currentData(),
            status=self.status_combo.currentData(),
        )
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(row["title"] or row["url"]))
            self.table.setItem(r, 1, QTableWidgetItem(row["platform"].title()))
            self.table.setItem(r, 2, QTableWidgetItem(row["date"][:16].replace("T", " ")))
            self.table.setItem(r, 3, QTableWidgetItem(human_size(row["file_size"])))
            self.table.setItem(r, 4, QTableWidgetItem(row["quality"] or "—"))
            self.table.setItem(r, 5, QTableWidgetItem(row["status"].title()))

    def _export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export History", "history.csv", "CSV (*.csv)")
        if not path:
            return
        rows = self.ctx.history.all_dicts()
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=[
                "title", "url", "platform", "date", "file_path", "file_size", "quality", "status",
            ])
            writer.writeheader()
            for row in rows:
                writer.writerow({k: row.get(k, "") for k in writer.fieldnames})
        notify(self, "Export complete", f"History exported to {Path(path).name}")

    def _clear(self) -> None:
        if confirm(self, "Clear history?", "This permanently deletes your download history log "
                  "(downloaded files themselves are not touched). Continue?"):
            self.ctx.history.clear()
            self._refresh()
