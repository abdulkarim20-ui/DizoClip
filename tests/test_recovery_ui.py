import sys

import pytest
from PySide6.QtWidgets import QApplication

from app.components.dialogs.restore_backup import RestoreBackupDialog
from app.core.data_manager import DataManager
from app.window.main_window import MainWindow


@pytest.fixture
def app():
    return QApplication.instance() or QApplication(sys.argv)


def test_main_window_accepts_preloaded_data(app):
    dm = DataManager(backup_min_interval=0)
    datasets = dm.load_all()
    datasets["links"].append({"id": "1", "title": "T", "url": "https://x.example", "color": "#e8794a"})
    win = MainWindow(data_manager=dm, datasets=datasets)
    assert win.links[0]["title"] == "T"
    win.close()


def test_reload_data_after_restore(app):
    dm = DataManager(backup_min_interval=0)
    win = MainWindow(data_manager=dm)
    win.links.insert(0, {"id": "a", "title": "A", "url": "https://a.example", "color": "#e8794a"})
    win.save_links()
    win.links.insert(0, {"id": "b", "title": "B", "url": "https://b.example", "color": "#e8794a"})
    win.save_links()

    dm.restore_backup(dm.backups_for("links")[0])  # back to "only A"
    assert win.reload_data() is True
    assert [x["title"] for x in win.links] == ["A"]
    win.close()


def test_restore_dialog_lists_backups(app):
    dm = DataManager(backup_min_interval=0)
    win = MainWindow(data_manager=dm)
    win.links.insert(0, {"id": "a", "title": "A", "url": "https://a.example", "color": "#e8794a"})
    win.save_links()
    win.links.insert(0, {"id": "b", "title": "B", "url": "https://b.example", "color": "#e8794a"})
    win.save_links()

    dlg = RestoreBackupDialog(win)
    assert dlg.combo.count() >= 1
    assert dlg.list.count() >= 1
    win.close()
