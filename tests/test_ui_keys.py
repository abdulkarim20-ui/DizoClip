import sys

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from app.window.main_window import MainWindow


@pytest.fixture
def win():
    QApplication.instance() or QApplication(sys.argv)
    w = MainWindow()
    yield w
    w.close()


def test_edit_form_never_falls_back_to_the_mask(win):
    win.form_view.edit({"label": "Old", "masked": "sk-" + "*" * 20 + "xyz", "color": "#e8794a"})
    assert win.form_view.key_edit.text() == ""
    assert not win.form_view.hint.isHidden()  # user is told to re-enter the key


def test_form_refuses_to_save_a_mask_as_a_key(win):
    win.form_view.edit(None)
    win.form_view.name_edit.setText("X")
    win.form_view.key_edit.setText("sk-" + "*" * 20 + "xyz")
    win.form_view._save()
    assert win.keys == []
    assert not win.form_view.hint.isHidden()


def test_saved_key_has_no_masked_field(win):
    win.form_view.edit(None)
    win.form_view.name_edit.setText("OpenAI")
    win.form_view.key_edit.setText("sk-real-secret-value-1234567890")
    win.form_view._save()
    assert "masked" not in win.keys[0]
    assert win.keys[0]["full_key"] == "sk-real-secret-value-1234567890"


def test_copy_key_refuses_when_the_secret_is_missing(win, monkeypatch):
    shown = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: shown.append(a) or QMessageBox.Ok)
    QApplication.clipboard().setText("untouched")

    win.copy_key({"label": "Old", "masked": "sk-****"})

    assert QApplication.clipboard().text() == "untouched"
    assert shown, "user must be told why nothing was copied"
