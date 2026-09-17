"""
Clipboard integration and copy-feedback helpers.
"""

from typing import Optional

from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QPushButton


def copy_to_clipboard(text: str) -> None:
    """Set system clipboard text."""
    QGuiApplication.clipboard().setText(text)


def show_copy_feedback(btn: Optional[QPushButton], check_icon=None, restore_icon=None, duration_ms: int = 1200) -> None:
    """Show temporary checkmark feedback on an icon button."""
    if btn is None:
        return
    if check_icon:
        btn.setText("")
        btn.setIcon(check_icon)
    else:
        btn.setText("✓")

    def _restore():
        if restore_icon:
            btn.setText("")
            btn.setIcon(restore_icon)
        else:
            btn.setText("")

    QTimer.singleShot(duration_ms, _restore)
