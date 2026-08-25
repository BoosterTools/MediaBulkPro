"""Main application window: header + sidebar + stacked pages."""

from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from app.core.app_context import AppContext
from app.core.config import APP_NAME
from app.queue.crash_recovery import discard_all, find_interrupted, resume_all
from ui.dialogs.confirm_dialog import confirm
from ui.pages.about_page import AboutPage
from ui.pages.base_page import BasePage
from ui.pages.dashboard_page import DashboardPage
from ui.pages.history_page import HistoryPage
from ui.pages.settings_page import SettingsPage
from ui.queue_controller import QueueController
from ui.theme.theme_manager import ThemeManager
from ui.widgets.clipboard_monitor import ClipboardMonitor
from ui.widgets.header import Header
from ui.widgets.sidebar import Sidebar


class MainWindow(QMainWindow):
    def __init__(self, ctx: AppContext, themes: ThemeManager) -> None:
        super().__init__()
        self.ctx = ctx
        self.themes = themes
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(QSize(1150, 720))
        self.resize(1360, 860)

        self.controller = QueueController(ctx.queue_manager)

        root = QWidget()
        root.setObjectName("Root")
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.header = Header(str(ctx.paths.downloads_dir))
        self.header.theme_toggle_requested.connect(self._toggle_theme)
        self.header.settings_requested.connect(lambda: self.show_section("settings"))
        self.header.about_requested.connect(lambda: self.show_section("about"))
        outer.addWidget(self.header)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.stack = QStackedWidget()
        body_layout.addWidget(self.sidebar)
        body_layout.addWidget(self.stack, 1)
        outer.addWidget(body, 1)
        self.setCentralWidget(root)

        self.pages: dict[str, BasePage] = {}
        self._add_page(DashboardPage(ctx, self.controller))
        self._add_page(HistoryPage(ctx))
        settings_page = SettingsPage(ctx)
        settings_page.theme_requested.connect(self.themes.apply)
        self._add_page(settings_page)
        self._add_page(AboutPage(ctx))

        self.sidebar.section_selected.connect(self.show_section)
        self.statusBar().showMessage("Ready")
        self.show_section("dashboard")

        self.clipboard_monitor = ClipboardMonitor()
        self.clipboard_monitor.set_enabled(bool(ctx.settings.get("clipboard_monitoring")))
        self.clipboard_monitor.url_detected.connect(self._on_clipboard_url)

        self._check_crash_recovery()

    def _add_page(self, page: BasePage) -> None:
        self.pages[page.key] = page
        self.stack.addWidget(page)

    def show_section(self, key: str) -> None:
        page = self.pages.get(key)
        if page is None:
            return
        self.stack.setCurrentWidget(page)
        self.sidebar.select(key)
        page.on_show()
        self.statusBar().showMessage(page.title)

    def _toggle_theme(self) -> None:
        order = ["system", "light", "dark"]
        current = self.themes.mode
        next_mode = order[(order.index(current) + 1) % len(order)] if current in order else "light"
        self.themes.apply(next_mode)
        self.ctx.settings.set("theme", next_mode)

    def _on_clipboard_url(self, url: str) -> None:
        auto = self.ctx.settings.get("clipboard_auto_download")
        if auto:
            self.ctx.queue_manager.enqueue_url(url)
            self.show_section("dashboard")
        else:
            if confirm(self, "New media URL detected",
                      f"{url}\n\nAdd this to the download queue?"):
                self.ctx.queue_manager.enqueue_url(url)
                self.show_section("dashboard")

    def _check_crash_recovery(self) -> None:
        interrupted = find_interrupted(self.ctx.queue_repo)
        if not interrupted:
            return
        if confirm(
            self, "Interrupted downloads detected",
            f"{len(interrupted)} interrupted download(s) were found from a previous session.\n\n"
            "Resume them now?",
        ):
            resume_all(self.ctx.queue_repo, interrupted)
            # Public API nudge to re-run the scheduler now that items are queued again.
            self.ctx.queue_manager.set_concurrency(self.ctx.queue_manager.max_concurrent)
        else:
            discard_all(self.ctx.queue_repo, interrupted)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt naming
        self.ctx.shutdown()
        super().closeEvent(event)
