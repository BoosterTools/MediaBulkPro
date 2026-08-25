"""About / Diagnostics page."""

from __future__ import annotations

from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QPushButton, QWidget

from app.core.app_context import AppContext
from app.core.config import APP_NAME, APP_SUBTITLE, APP_VERSION, ffmpeg_available
from app.core.diagnostics import write_diagnostic_report, yt_dlp_version
from ui.dialogs.confirm_dialog import notify
from ui.pages.base_page import BasePage
from ui.widgets.card import Card
from ui.widgets.task_thread import TaskThread


class AboutPage(BasePage):
    key = "about"
    title = "About / Diagnostics"
    subtitle = f"{APP_NAME} {APP_VERSION}"

    def __init__(self, ctx: AppContext, parent: QWidget | None = None) -> None:
        super().__init__(ctx, parent)
        self._update_thread: TaskThread | None = None

        card = Card()
        card.body.addWidget(QLabel(f"<b>{APP_NAME}</b> — {APP_SUBTITLE}"))
        card.body.addWidget(QLabel(f"Version: {APP_VERSION}"))
        card.body.addWidget(QLabel(f"yt-dlp: {yt_dlp_version()}"))
        card.body.addWidget(QLabel(
            "FFmpeg: " + ("Detected on PATH" if ffmpeg_available() else "Not found on PATH")
        ))
        card.body.addWidget(QLabel(f"Data folder: {ctx.paths.data_dir}"))
        card.body.addWidget(QLabel(f"Logs folder: {ctx.paths.logs_dir}"))

        row = QHBoxLayout()
        self.update_btn = QPushButton("Check for Updates")
        self.update_btn.clicked.connect(self._check_updates)
        row.addWidget(self.update_btn)
        self.diag_btn = QPushButton("Export Diagnostic Report")
        self.diag_btn.clicked.connect(self._export_diagnostics)
        row.addWidget(self.diag_btn)
        row.addStretch()
        card.body.addLayout(row)

        note = QLabel(
            "MediaBulk Pro only downloads publicly accessible media you're authorized to "
            "access. It never bypasses DRM, private-account restrictions, paywalls, or "
            "CAPTCHAs, and never uploads your URLs, cookies, or history anywhere."
        )
        note.setObjectName("Muted")
        note.setWordWrap(True)
        card.body.addWidget(note)

        self.layout_.addWidget(card)
        self.layout_.addStretch()

    def _check_updates(self) -> None:
        from app.core.diagnostics import check_for_updates

        self.update_btn.setEnabled(False)
        thread = TaskThread(check_for_updates)
        thread.signals.finished.connect(self._updates_checked)
        thread.signals.error.connect(
            lambda msg: (self.update_btn.setEnabled(True),
                        notify(self, "Could not check for updates",
                              "This requires an internet connection.", warning=True))
        )
        self._update_thread = thread
        thread.start()

    def _updates_checked(self, result: dict) -> None:
        self.update_btn.setEnabled(True)
        if result["update_available"] == "True":
            notify(self, "Update available",
                  f"A newer yt-dlp is available: {result['latest']} "
                  f"(you have {result['current']}).")
        else:
            notify(self, "Up to date", f"yt-dlp {result['current']} is the latest version.")

    def _export_diagnostics(self) -> None:
        default_dir = str(self.ctx.paths.data_dir)
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Diagnostic Report", f"{default_dir}/diagnostic-report.txt",
            "Text (*.txt)",
        )
        if not path:
            return
        from pathlib import Path
        report_path = write_diagnostic_report(
            Path(path).parent, self.ctx.settings.all(),
            {"data_dir": str(self.ctx.paths.data_dir), "logs_dir": str(self.ctx.paths.logs_dir),
             "downloads_dir": str(self.ctx.paths.downloads_dir)},
        )
        notify(self, "Report exported", f"Saved to {report_path}")
