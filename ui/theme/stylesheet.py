"""Builds the application QSS from a Palette."""

from __future__ import annotations

from ui.theme.palette import Palette


def build_stylesheet(p: Palette) -> str:
    return f"""
    * {{
        font-family: "Segoe UI Variable", "Segoe UI", "Inter", sans-serif;
        font-size: 10pt; color: {p.text};
    }}
    QMainWindow, QWidget#Root {{ background: {p.window}; }}
    QToolTip {{ background: {p.surface}; color: {p.text}; border: 1px solid {p.border};
        padding: 6px 8px; border-radius: 6px; }}

    QWidget#Header {{ background: {p.surface}; border-bottom: 1px solid {p.border}; }}
    QLabel#BrandTitle {{ font-size: 15pt; font-weight: 700; }}
    QLabel#BrandSubtitle {{ font-size: 8.5pt; color: {p.text_muted}; }}

    QWidget#Sidebar {{ background: {p.surface}; border-right: 1px solid {p.border}; }}
    QPushButton#NavButton {{
        text-align: left; padding: 9px 14px; border: none; border-radius: 8px;
        background: transparent; color: {p.text}; font-size: 10pt;
    }}
    QPushButton#NavButton:hover {{ background: {p.surface_alt}; }}
    QPushButton#NavButton:checked {{ background: {p.accent}; color: {p.accent_text}; font-weight: 600; }}
    QScrollArea#NavScroll, QWidget#NavInner {{ background: transparent; border: none; }}
    QScrollArea#PageScroll, QWidget#PageContent {{ background: transparent; border: none; }}

    QFrame#Card {{ background: {p.surface}; border: 1px solid {p.border}; border-radius: 12px; }}
    QLabel#CardTitle {{ font-size: 9pt; color: {p.text_muted}; font-weight: 600; }}
    QLabel#CardValue {{ font-size: 19pt; font-weight: 700; }}
    QLabel#PageTitle {{ font-size: 17pt; font-weight: 700; }}
    QLabel#PageSubtitle {{ font-size: 10pt; color: {p.text_muted}; }}
    QLabel#SectionTitle {{ font-size: 11pt; font-weight: 600; }}
    QLabel#Muted {{ color: {p.text_muted}; }}
    QLabel#EmptyState {{ color: {p.text_muted}; font-size: 11pt; }}
    QLabel#PlatformBadge {{
        background: {p.surface_alt}; border-radius: 6px; padding: 2px 8px; font-size: 8.5pt;
        font-weight: 600; color: {p.text_muted};
    }}

    QPushButton {{ background: {p.surface_alt}; border: 1px solid {p.border}; border-radius: 8px;
        padding: 8px 16px; }}
    QPushButton:hover {{ border-color: {p.accent}; }}
    QPushButton:pressed {{ background: {p.border}; }}
    QPushButton:disabled {{ color: {p.text_muted}; }}
    QPushButton#Primary {{ background: {p.accent}; color: {p.accent_text}; border: none; font-weight: 600; }}
    QPushButton#Primary:hover {{ background: {p.accent_hover}; }}
    QPushButton#Danger {{ background: {p.danger}; color: white; border: none; font-weight: 600; }}

    QLineEdit, QComboBox, QSpinBox, QPlainTextEdit, QTextEdit {{
        background: {p.surface}; border: 1px solid {p.border}; border-radius: 8px; padding: 7px 10px;
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QPlainTextEdit:focus {{ border-color: {p.accent}; }}

    QProgressBar {{ background: {p.surface_alt}; border: none; border-radius: 6px; height: 10px;
        text-align: center; color: transparent; }}
    QProgressBar::chunk {{ background: {p.accent}; border-radius: 6px; }}

    QTableView, QTreeView, QListView {{
        background: {p.surface}; border: 1px solid {p.border}; border-radius: 10px;
        gridline-color: {p.border}; selection-background-color: {p.accent};
        selection-color: {p.accent_text}; alternate-background-color: {p.surface_alt};
    }}
    QHeaderView::section {{ background: {p.surface_alt}; border: none;
        border-bottom: 1px solid {p.border}; padding: 8px; font-weight: 600; }}

    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: {p.border}; border-radius: 5px; min-height: 30px; }}
    QScrollBar::handle:vertical:hover {{ background: {p.text_muted}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

    QStatusBar {{ background: {p.surface}; border-top: 1px solid {p.border}; color: {p.text_muted}; }}
    QTabWidget::pane {{ border: 1px solid {p.border}; border-radius: 8px; }}
    QTabBar::tab {{ background: {p.surface_alt}; padding: 8px 16px; border-top-left-radius: 8px;
        border-top-right-radius: 8px; margin-right: 2px; }}
    QTabBar::tab:selected {{ background: {p.accent}; color: {p.accent_text}; }}
    """
