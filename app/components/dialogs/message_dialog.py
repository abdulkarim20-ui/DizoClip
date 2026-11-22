"""
Message dialog helper with unified DizoClip dark title bar and styling.
"""
from __future__ import annotations

from PySide6.QtWidgets import QMessageBox

from app.config.theme import ACCENT, BG_MAIN, TEXT_MAIN
from app.core.window_utils import apply_dark_title_bar


def show_message(parent, kind: str, title: str, text: str) -> int:
    """
    Shows a message box with unified DizoClip dark title bar and styling.
    Seamlessly passes through to QMessageBox.<kind> if monkeypatched in tests.
    """
    method = getattr(QMessageBox, kind)
    # If monkeypatched by pytest fixtures, call the mock directly
    if not str(type(method)).startswith("<class 'builtin"):
        return method(parent, title, text)

    box = QMessageBox(parent)
    win_title = f"{title} - DizoClip" if "DizoClip" not in title else title
    box.setWindowTitle(win_title)
    box.setText(text)
    if kind == "information":
        box.setIcon(QMessageBox.Information)
    elif kind == "warning":
        box.setIcon(QMessageBox.Warning)
    elif kind == "critical":
        box.setIcon(QMessageBox.Critical)

    box.setStyleSheet(f"""
        QDialog {{ background-color: {BG_MAIN}; border: none; }}
        QLabel  {{ color: {TEXT_MAIN}; background: transparent; font-size: 12.5px; }}
        QPushButton {{
            background: {ACCENT};
            color: #0b0d10;
            font-weight: 700;
            border-radius: 6px;
            padding: 5px 18px;
            min-width: 60px;
            border: none;
        }}
        QPushButton:hover {{ background: #d5693c; }}
    """)
    if parent and hasattr(parent, "windowIcon") and not parent.windowIcon().isNull():
        box.setWindowIcon(parent.windowIcon())

    apply_dark_title_bar(box, BG_MAIN, TEXT_MAIN)
    return box.exec()
