import sys

import pytest
from PySide6.QtWidgets import QApplication

from app.core.clipboard import ClipboardGuard


@pytest.fixture
def app():
    return QApplication.instance() or QApplication(sys.argv)


def test_flush_clears_only_what_we_put_there(app):
    guard = ClipboardGuard()
    guard.copy_sensitive("my-secret", clear_after_s=0)
    guard.flush()
    assert QApplication.clipboard().text() == ""


def test_flush_leaves_the_clipboard_alone_if_the_user_copied_something_else(app):
    guard = ClipboardGuard()
    guard.copy_sensitive("my-secret", clear_after_s=0)
    QApplication.clipboard().setText("something the user copied later")
    guard.flush()
    assert QApplication.clipboard().text() == "something the user copied later"
