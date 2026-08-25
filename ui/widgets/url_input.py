"""Bulk URL input: paste, drag-and-drop .txt/.csv, auto-dedup, auto-classify preview."""

from __future__ import annotations

import csv
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.platforms.detector import deduplicate_urls, detect


class UrlInputWidget(QWidget):
    """Emits a de-duplicated list of raw URL strings when the user submits."""

    urls_submitted = Signal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlaceholderText(
            "Paste one or more URLs (one per line)\u2014YouTube, YouTube Shorts, "
            "Instagram Reels, or TikTok\u2014or drag a .txt/.csv file here."
        )
        self.text_edit.setMinimumHeight(140)
        layout.addWidget(self.text_edit)

        self.status_label = QLabel("")
        self.status_label.setObjectName("Muted")
        layout.addWidget(self.status_label)

        row = QHBoxLayout()
        self.import_btn = QPushButton("Import .txt / .csv")
        self.import_btn.clicked.connect(self._import_file)
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.text_edit.clear)
        row.addWidget(self.import_btn)
        row.addWidget(self.clear_btn)
        row.addStretch()
        self.add_btn = QPushButton("Add to Queue")
        self.add_btn.setObjectName("Primary")
        self.add_btn.clicked.connect(self._submit)
        row.addWidget(self.add_btn)
        layout.addLayout(row)

        self.text_edit.textChanged.connect(self._update_status)

    # -- text parsing ---------------------------------------------------
    def raw_lines(self) -> list[str]:
        text = self.text_edit.toPlainText()
        # Accept whitespace- or newline-separated URLs.
        tokens: list[str] = []
        for line in text.splitlines():
            tokens.extend(line.split())
        return tokens

    def _update_status(self) -> None:
        lines = deduplicate_urls(self.raw_lines())
        if not lines:
            self.status_label.setText("")
            return
        matches = [detect(u) for u in lines]
        supported = sum(1 for m in matches if m.is_supported)
        unsupported = len(matches) - supported
        text = f"{len(lines)} URLs \u2014 {supported} recognized"
        if unsupported:
            text += f", {unsupported} unrecognized"
        self.status_label.setText(text)

    def _submit(self) -> None:
        urls = deduplicate_urls(self.raw_lines())
        if urls:
            self.urls_submitted.emit(urls)
            self.text_edit.clear()

    # -- file import ------------------------------------------------------
    def _import_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import URL list", "", "Text/CSV (*.txt *.csv)")
        if path:
            self._load_file(Path(path))

    def _load_file(self, path: Path) -> None:
        urls: list[str] = []
        try:
            if path.suffix.lower() == ".csv":
                with open(path, newline="", encoding="utf-8", errors="ignore") as fh:
                    for row in csv.reader(fh):
                        urls.extend(cell.strip() for cell in row if cell.strip().startswith("http"))
            else:
                text = path.read_text(encoding="utf-8", errors="ignore")
                for line in text.splitlines():
                    urls.extend(tok for tok in line.split() if tok.startswith("http"))
        except OSError:
            return
        if urls:
            existing = self.text_edit.toPlainText()
            joined = "\n".join(urls)
            self.text_edit.setPlainText(f"{existing}\n{joined}" if existing.strip() else joined)

    # -- drag and drop ------------------------------------------------------
    def dragEnterEvent(self, event) -> None:  # noqa: N802 - Qt naming
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802 - Qt naming
        for url in event.mimeData().urls():
            local_path = url.toLocalFile()
            if local_path and Path(local_path).suffix.lower() in (".txt", ".csv"):
                self._load_file(Path(local_path))
        if event.mimeData().hasText() and not event.mimeData().hasUrls():
            self.text_edit.appendPlainText(event.mimeData().text())
        event.acceptProposedAction()
