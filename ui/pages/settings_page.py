"""Settings: General, Downloads, Video, File Naming, Advanced."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QWidget,
)

from app.core.app_context import AppContext
from app.core.config import ffmpeg_available
from ui.dialogs.confirm_dialog import confirm, notify
from ui.pages.base_page import BasePage
from ui.pages.dashboard_page import FORMATS, QUALITIES
from ui.widgets.card import Card


class SettingsPage(BasePage):
    key = "settings"
    title = "Settings"
    subtitle = "Configure MediaBulk Pro"

    theme_requested = Signal(str)

    def __init__(self, ctx: AppContext, parent: QWidget | None = None) -> None:
        super().__init__(ctx, parent)
        self._build_general()
        self._build_downloads()
        self._build_video()
        self._build_naming()
        self._build_advanced()
        self.layout_.addStretch()

    def _bool_setting(self, form: QFormLayout, label: str, key: str, extra_cb=None) -> None:
        box = QCheckBox()
        box.setChecked(bool(self.ctx.settings.get(key)))

        def on_toggle(v: bool) -> None:
            self.ctx.settings.set(key, v)
            if extra_cb:
                extra_cb(v)

        box.toggled.connect(on_toggle)
        form.addRow(label, box)

    def _build_general(self) -> None:
        card = Card()
        h = QLabel("General")
        h.setObjectName("SectionTitle")
        card.body.addWidget(h)
        form = QFormLayout()

        theme_combo = QComboBox()
        theme_combo.addItem("System", "system")
        theme_combo.addItem("Light", "light")
        theme_combo.addItem("Dark", "dark")
        idx = theme_combo.findData(self.ctx.settings.get("theme"))
        theme_combo.setCurrentIndex(max(idx, 0))
        theme_combo.currentIndexChanged.connect(
            lambda: (self.ctx.settings.set("theme", theme_combo.currentData()),
                     self.theme_requested.emit(theme_combo.currentData()))
        )
        form.addRow("Theme", theme_combo)

        self._bool_setting(form, "Start minimized", "start_minimized")
        self._bool_setting(form, "Monitor clipboard for supported URLs", "clipboard_monitoring")
        self._bool_setting(form, "Automatically add clipboard URLs to queue "
                                 "(never auto-downloads without this)", "clipboard_auto_download")
        self._bool_setting(form, "Show desktop notifications", "show_notifications")
        card.body.addLayout(form)
        self.layout_.addWidget(card)

    def _build_downloads(self) -> None:
        card = Card()
        h = QLabel("Downloads")
        h.setObjectName("SectionTitle")
        card.body.addWidget(h)
        form = QFormLayout()

        folder_row = QHBoxLayout()
        self.folder_edit = QLineEdit(
            self.ctx.settings.get("download_folder") or str(self.ctx.paths.downloads_dir)
        )
        browse = QPushButton("Browse…")

        def pick_folder():
            path = QFileDialog.getExistingDirectory(self, "Download folder", self.folder_edit.text())
            if path:
                self.folder_edit.setText(path)
                self.ctx.settings.set("download_folder", path)
                self.ctx.queue_manager.download_folder = path

        browse.clicked.connect(pick_folder)
        folder_row.addWidget(self.folder_edit, 1)
        folder_row.addWidget(browse)
        form.addRow("Download folder", folder_row)

        concurrency_spin = QSpinBox()
        concurrency_spin.setRange(1, 16)
        concurrency_spin.setValue(int(self.ctx.settings.get("concurrent_downloads")))
        concurrency_spin.valueChanged.connect(
            lambda v: (self.ctx.settings.set("concurrent_downloads", v),
                       self.ctx.queue_manager.set_concurrency(v))
        )
        form.addRow("Concurrent downloads", concurrency_spin)

        retry_spin = QSpinBox()
        retry_spin.setRange(0, 10)
        retry_spin.setValue(int(self.ctx.settings.get("retry_count")))
        retry_spin.valueChanged.connect(lambda v: self.ctx.settings.set("retry_count", v))
        form.addRow("Retry count", retry_spin)

        dup_combo = QComboBox()
        dup_combo.addItem("Skip if already downloaded", "skip")
        dup_combo.addItem("Download again", "download_again")
        idx = dup_combo.findData(self.ctx.settings.get("duplicate_behavior"))
        dup_combo.setCurrentIndex(max(idx, 0))
        dup_combo.currentIndexChanged.connect(
            lambda: (self.ctx.settings.set("duplicate_behavior", dup_combo.currentData()),
                     setattr(self.ctx.queue_manager, "duplicate_behavior", dup_combo.currentData()))
        )
        form.addRow("Duplicate behavior", dup_combo)

        speed_spin = QSpinBox()
        speed_spin.setRange(0, 1_000_000)
        speed_spin.setSuffix(" KB/s (0 = unlimited)")
        speed_spin.setValue(int(self.ctx.settings.get("speed_limit_kbps")))
        speed_spin.valueChanged.connect(lambda v: self.ctx.settings.set("speed_limit_kbps", v))
        form.addRow("Speed limit", speed_spin)

        card.body.addLayout(form)
        self.layout_.addWidget(card)

    def _build_video(self) -> None:
        card = Card()
        h = QLabel("Video")
        h.setObjectName("SectionTitle")
        card.body.addWidget(h)
        form = QFormLayout()

        quality_combo = QComboBox()
        for q in QUALITIES:
            quality_combo.addItem(q, q)
        idx = quality_combo.findData(self.ctx.settings.get("default_quality"))
        quality_combo.setCurrentIndex(max(idx, 0))
        quality_combo.currentIndexChanged.connect(
            lambda: self.ctx.settings.set("default_quality", quality_combo.currentData())
        )
        form.addRow("Default quality", quality_combo)

        format_combo = QComboBox()
        for f in FORMATS:
            format_combo.addItem(f, f)
        idx = format_combo.findData(self.ctx.settings.get("default_format"))
        format_combo.setCurrentIndex(max(idx, 0))
        format_combo.currentIndexChanged.connect(
            lambda: self.ctx.settings.set("default_format", format_combo.currentData())
        )
        form.addRow("Default format", format_combo)

        card.body.addLayout(form)
        self.layout_.addWidget(card)

    def _build_naming(self) -> None:
        card = Card()
        h = QLabel("File Naming")
        h.setObjectName("SectionTitle")
        card.body.addWidget(h)
        form = QFormLayout()

        template_edit = QLineEdit(self.ctx.settings.get("filename_template"))
        template_edit.setPlaceholderText("%(uploader)s - %(title)s")
        template_edit.editingFinished.connect(
            lambda: (self.ctx.settings.set("filename_template", template_edit.text()),
                     setattr(self.ctx.queue_manager, "filename_template", template_edit.text()))
        )
        form.addRow("Filename template", template_edit)
        hint = QLabel("Available fields: %(title)s %(uploader)s %(platform)s "
                     "%(upload_date)s %(id)s %(ext)s")
        hint.setObjectName("Muted")
        form.addRow("", hint)

        self._bool_setting(
            form, "Organize into per-platform subfolders", "folder_structure_by_platform",
            extra_cb=lambda v: setattr(self.ctx.queue_manager, "folder_structure_by_platform", v),
        )
        card.body.addLayout(form)
        self.layout_.addWidget(card)

    def _build_advanced(self) -> None:
        card = Card()
        h = QLabel("Advanced")
        h.setObjectName("SectionTitle")
        card.body.addWidget(h)
        form = QFormLayout()

        ffmpeg_status = QLabel("Detected on PATH" if ffmpeg_available() else
                              "Not found — video+audio merging will not work until installed")
        ffmpeg_status.setObjectName("Muted" if ffmpeg_available() else "")
        form.addRow("FFmpeg", ffmpeg_status)

        timeout_spin = QSpinBox()
        timeout_spin.setRange(5, 300)
        timeout_spin.setValue(int(self.ctx.settings.get("timeout_secs")))
        timeout_spin.valueChanged.connect(lambda v: self.ctx.settings.set("timeout_secs", v))
        form.addRow("Network timeout (seconds)", timeout_spin)

        card.body.addLayout(form)

        reset_row = QHBoxLayout()
        reset_row.addStretch()
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setObjectName("Danger")
        reset_btn.clicked.connect(self._reset_defaults)
        reset_row.addWidget(reset_btn)
        card.body.addLayout(reset_row)
        self.layout_.addWidget(card)

    def _reset_defaults(self) -> None:
        if confirm(self, "Reset settings?", "All settings will return to their default values."):
            self.ctx.settings.reset_to_defaults()
            notify(self, "Settings reset", "Restart MediaBulk Pro for all changes to fully apply.")
