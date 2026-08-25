"""MediaBulk Pro entry point."""

from __future__ import annotations

import sys


def main() -> int:
    from dotenv import load_dotenv
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    from app.core.app_context import AppContext
    from app.core.config import APP_NAME, ORG_NAME
    from ui.theme.theme_manager import ThemeManager
    from ui.windows.main_window import MainWindow

    load_dotenv()
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    app.setStyle("Fusion")

    ctx = AppContext.create()
    themes = ThemeManager(app)
    themes.apply(ctx.settings.get("theme"))

    window = MainWindow(ctx, themes)
    if not ctx.settings.get("start_minimized"):
        window.show()
    else:
        window.showMinimized()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
