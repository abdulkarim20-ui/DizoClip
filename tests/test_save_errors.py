import sys

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from app.core.data_manager import DataError
from app.window.main_window import MainWindow


def test_failed_save_is_reported_not_swallowed(monkeypatch):
    QApplication.instance() or QApplication(sys.argv)
    win = MainWindow()
    shown = []
    monkeypatch.setattr(QMessageBox, "critical", lambda *a, **k: shown.append(a) or QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.Yes)

    def boom(*a, **k):
        raise DataError("disk full", dataset="links")

    real_save = win.data_manager.save
    monkeypatch.setattr(win.data_manager, "save", boom)
    try:
        assert win.save_links() is False
        assert shown
    finally:
        win.data_manager.save = real_save
        win.close()
