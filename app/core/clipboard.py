"""
Clipboard integration and copy-feedback helpers.
"""
import hashlib
from typing import Optional

from PySide6.QtCore import QByteArray, QMimeData, QObject, QTimer
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


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class ClipboardGuard(QObject):
    """
    Copies secrets and clears them again after a delay, but only if the clipboard
    still holds what we put there. Only a hash is kept, never the secret.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._token: Optional[str] = None
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.flush)

    def copy_sensitive(self, text: str, clear_after_s: int = 30) -> None:
        mime = QMimeData()
        mime.setText(text)
        # Windows, best effort: ask clipboard history (Win+V) and cloud clipboard to skip this entry.
        mime.setData("ExcludeClipboardContentFromMonitorProcessing", QByteArray(b"1"))
        mime.setData("CanIncludeInClipboardHistory", QByteArray(b"\x00\x00\x00\x00"))
        mime.setData("CanUploadToCloudClipboard", QByteArray(b"\x00\x00\x00\x00"))
        QGuiApplication.clipboard().setMimeData(mime)

        self._token = _digest(text)
        if clear_after_s > 0:
            self._timer.start(int(clear_after_s * 1000))
        else:
            self._timer.stop()

    def flush(self) -> None:
        """Clear the clipboard now if it still contains what we copied."""
        self._timer.stop()
        token, self._token = self._token, None
        if token is None:
            return
        clipboard = QGuiApplication.clipboard()
        if _digest(clipboard.text()) == token:
            clipboard.clear()
