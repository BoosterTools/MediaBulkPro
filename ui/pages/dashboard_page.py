"""Dashboard: statistics cards, bulk URL input, toolbar, and the queue table."""

from __future__ import annotations

import os
import subprocess
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QComboBox, QGridLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox, QWidget

from app.core.app_context import AppContext
from app.platforms.detector import detect
from app.queue.collection_expansion import expand_collection
from app.queue.models import QueueEvent
from app.utils.formatting import human_size
from ui.dialogs.collection_dialog import CollectionDialog
from ui.dialogs.confirm_dialog import confirm, notify
from ui.dialogs.error_detail_dialog import ErrorDetailDialog
from ui.pages.base_page import BasePage
from ui.queue_controller import QueueController
from ui.widgets.card import StatCard
from ui.widgets.queue_table import QueueTable
from ui.widgets.task_thread import TaskThread
from ui.widgets.url_input import UrlInputWidget

QUALITIES = ["best", "2160p", "1440p", "1080p", "720p", "480p", "360p", "audio_only"]
FORMATS = ["mp4", "mkv", "webm", "mp3", "m4a", "wav", "opus"]


class DashboardPage(BasePage):
    key = "dashboard"
    title = "MediaBulk Pro"
    subtitle = "Professional Bulk Video Downloader"

    def __init__(self, ctx: AppContext, controller: QueueController, parent: QWidget | None = None) -> None:
        super().__init__(ctx, parent)
        self.controller = controller
        self._expand_thread: TaskThread | None = None
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(200)
        self._refresh_timer.timeout.connect(self._refresh_all)

        self._build_stats()
        self._build_url_input()
        self._build_toolbar()
        self._build_table()
        controller.event_occurred.connect(self._on_event)

    # -- stats ------------------------------------------------------------
    def _build_stats(self) -> None:
        grid = QGridLayout()
        grid.setSpacing(12)
        self.stat_cards: dict[str, StatCard] = {}
        for i, (key, label) in enumerate([
            ("total", "Total URLs"), ("queued", "Queued"), ("downloading", "Downloading"),
            ("completed", "Completed"), ("failed", "Failed"), ("size", "Downloaded"),
        ]):
            card = StatCard(label, "0")
            self.stat_cards[key] = card
            grid.addWidget(card, 0, i)
        self.layout_.addLayout(grid)

    def _refresh_stats(self) -> None:
        counts = self.ctx.queue_repo.counts_by_status()
        total = sum(counts.values())
        self.stat_cards["total"].set_value(str(total))
        self.stat_cards["queued"].set_value(str(counts.get("queued", 0)))
        self.stat_cards["downloading"].set_value(
            str(counts.get("downloading", 0) + counts.get("extracting", 0)))
        self.stat_cards["completed"].set_value(str(counts.get("completed", 0)))
        self.stat_cards["failed"].set_value(str(counts.get("failed", 0)))
        total_bytes = sum(
            (i.downloaded_bytes or 0) for i in self.ctx.queue_repo.all() if i.status == "completed"
        )
        self.stat_cards["size"].set_value(human_size(total_bytes))

    # -- url input ------------------------------------------------------
    def _build_url_input(self) -> None:
        self.url_input = UrlInputWidget()
        self.url_input.urls_submitted.connect(self._handle_submitted_urls)
        self.layout_.addWidget(self.url_input)

    def _handle_submitted_urls(self, urls: list[str]) -> None:
        singles: list[str] = []
        collections: list[str] = []
        unsupported: list[str] = []
        for url in urls:
            match = detect(url)
            if not match.is_supported:
                unsupported.append(url)
            elif match.is_collection:
                collections.append(url)
            else:
                singles.append(url)

        if singles:
            self.ctx.queue_manager.enqueue_many(
                singles, quality=self.quality_combo.currentData(),
                output_format=self.format_combo.currentData(),
            )
        for url in collections:
            self._expand_collection(url)
        if unsupported:
            notify(self, "Some URLs were not recognized",
                  f"{len(unsupported)} URL(s) didn't match a supported platform and were skipped.",
                  warning=True)
        self._refresh_all()

    def _expand_collection(self, url: str) -> None:
        match = detect(url)

        def task():
            return expand_collection(url, self.ctx.backend)

        thread = TaskThread(task)
        thread.signals.finished.connect(lambda result: self._collection_expanded(url, match, result))
        thread.signals.error.connect(
            lambda msg: notify(self, "Could not read that channel/profile", msg, warning=True)
        )
        self._expand_thread = thread
        thread.start()

    def _collection_expanded(self, url: str, match, result) -> None:
        _, entries = result
        if not entries:
            notify(self, "No videos found", f"No videos were found at:\n{url}", warning=True)
            return
        label = f"{match.platform.value.title()} {match.media_type.value} detected"
        dialog = CollectionDialog(label, entries, parent=self)
        if dialog.exec():
            chosen = dialog.selected_urls()
            if chosen:
                self.ctx.queue_manager.enqueue_many(
                    chosen, quality=self.quality_combo.currentData(),
                    output_format=self.format_combo.currentData(), source_batch=url,
                )
                self._refresh_all()

    # -- toolbar ------------------------------------------------------
    def _build_toolbar(self) -> None:
        row = QHBoxLayout()
        row.addWidget(QLabel("Quality:"))
        self.quality_combo = QComboBox()
        for q in QUALITIES:
            self.quality_combo.addItem(q, q)
        idx = self.quality_combo.findData(self.ctx.settings.get("default_quality"))
        self.quality_combo.setCurrentIndex(max(idx, 0))
        row.addWidget(self.quality_combo)

        row.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        for f in FORMATS:
            self.format_combo.addItem(f, f)
        idx = self.format_combo.findData(self.ctx.settings.get("default_format"))
        self.format_combo.setCurrentIndex(max(idx, 0))
        row.addWidget(self.format_combo)

        row.addWidget(QLabel("Concurrent:"))
        self.concurrency_spin = QSpinBox()
        self.concurrency_spin.setRange(1, 16)
        self.concurrency_spin.setValue(self.ctx.queue_manager.max_concurrent)
        self.concurrency_spin.valueChanged.connect(self.ctx.queue_manager.set_concurrency)
        row.addWidget(self.concurrency_spin)
        row.addStretch()

        self.retry_all_btn = QPushButton("Retry All Failed")
        self.retry_all_btn.clicked.connect(self._retry_all_failed)
        row.addWidget(self.retry_all_btn)
        self.clear_completed_btn = QPushButton("Clear Completed")
        self.clear_completed_btn.clicked.connect(self._clear_completed)
        row.addWidget(self.clear_completed_btn)
        self.layout_.addLayout(row)

    def _retry_all_failed(self) -> None:
        n = self.ctx.queue_manager.retry_all_failed()
        if n == 0:
            notify(self, "Nothing to retry", "There are no failed downloads.")
        self._refresh_all()

    def _clear_completed(self) -> None:
        self.ctx.queue_repo.clear_completed()
        self._refresh_all()

    # -- table ------------------------------------------------------
    def _build_table(self) -> None:
        self.table = QueueTable()
        self.table.setMinimumHeight(320)
        self.table.pause_requested.connect(self.ctx.queue_manager.pause)
        self.table.resume_requested.connect(self.ctx.queue_manager.resume)
        self.table.retry_requested.connect(self._retry_with_detail)
        self.table.cancel_requested.connect(self._cancel_with_confirm)
        self.table.remove_requested.connect(self.ctx.queue_manager.remove)
        self.table.copy_url_requested.connect(self._copy_url)
        self.table.open_file_requested.connect(self._open_file)
        self.table.open_folder_requested.connect(self._open_folder)
        self.table.reordered.connect(self.ctx.queue_manager.reorder)
        self.table.view_error_requested.connect(self.show_error_detail)
        self.table.itemDoubleClicked.connect(self._on_row_double_clicked)
        self.layout_.addWidget(self.table, 1)

    def _retry_with_detail(self, item_id: int) -> None:
        self.ctx.queue_manager.retry(item_id)
        self._refresh_all()

    def _cancel_with_confirm(self, item_id: int) -> None:
        if confirm(self, "Cancel download?", "This download will be stopped and its partial file removed."):
            self.ctx.queue_manager.cancel(item_id)
            self._refresh_all()

    def _copy_url(self, item_id: int) -> None:
        item = self.ctx.queue_repo.get(item_id)
        if item:
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(item.url)

    def _open_file(self, item_id: int) -> None:
        item = self.ctx.queue_repo.get(item_id)
        if item and item.output_path and os.path.exists(item.output_path):
            self._open_path(item.output_path)
        else:
            notify(self, "File not found", "This item hasn't finished downloading yet.")

    def _open_folder(self, item_id: int) -> None:
        item = self.ctx.queue_repo.get(item_id)
        if item and item.output_path:
            self._open_path(os.path.dirname(item.output_path))

    def _open_path(self, path: str) -> None:
        if sys.platform.startswith("win"):
            os.startfile(path)  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])  # noqa: S603,S607
        else:
            subprocess.Popen(["xdg-open", path])  # noqa: S603,S607

    def show_error_detail(self, item_id: int) -> None:
        item = self.ctx.queue_repo.get(item_id)
        if item and item.error_message:
            ErrorDetailDialog(item.error_message, parent=self).exec()
        elif item:
            notify(self, "No error details", "This item has no recorded error.")

    def _on_row_double_clicked(self, table_item) -> None:
        row = table_item.row()
        item_id = self.table.item_id_for_row(row)
        if item_id is None:
            return
        item = self.ctx.queue_repo.get(item_id)
        if item and item.status == "failed":
            self.show_error_detail(item_id)

    # -- live events ------------------------------------------------------
    def _on_event(self, event: QueueEvent) -> None:
        # Progress ticks can fire many times a second per active download —
        # coalesce them into a single debounced UI refresh instead of
        # rebuilding the whole table on every tick. Structural changes
        # (added/removed/status/reorder) still refresh immediately.
        if event.type == "progress":
            self._refresh_timer.start()
        else:
            self._refresh_all()

    def _refresh_all(self) -> None:
        self.table.set_items(self.ctx.queue_repo.all())
        self._refresh_stats()

    def on_show(self) -> None:
        self._refresh_all()
