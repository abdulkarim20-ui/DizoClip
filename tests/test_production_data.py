from pathlib import Path
import pytest

from app.core.data_manager import DataError, DataManager
from app.core.runtime import RuntimeMode


def test_new_data_is_seeded(tmp_path: Path):
    dm = DataManager(tmp_path)
    data = dm.load_all()

    assert isinstance(data["keys"], list)
    assert isinstance(data["prompts"], list)
    assert isinstance(data["settings"], dict)
    assert (tmp_path / "DC_Settings.json").exists()


def test_legacy_file_is_migrated_without_deleting_source(tmp_path: Path):
    legacy = tmp_path / "keys.json"
    legacy.write_text('[{"label":"Legacy","masked":"****","full_key":"abc"}]', encoding="utf-8")

    dm = DataManager(tmp_path)
    keys = dm.load_all()["keys"]

    assert keys[0]["label"] == "Legacy"
    assert (tmp_path / "DC_Keys.json").exists()
    assert legacy.exists()


def test_corrupt_json_does_not_become_empty(tmp_path: Path):
    target = tmp_path / "DC_Links.json"
    target.write_text("{broken", encoding="utf-8")

    dm = DataManager(tmp_path)

    with pytest.raises(DataError):
        dm.load_all()


def test_existing_dataset_is_backed_up_before_save(tmp_path: Path):
    dm = DataManager(tmp_path, backup_min_interval=0)
    dm.load_all()

    dm.save("links", [{"title": "One", "url": "https://example.com"}])
    dm.save("links", [{"title": "Two", "url": "https://example.org"}])

    assert dm.backups_for("links")


def test_atomic_save_round_trip(tmp_path: Path):
    dm = DataManager(tmp_path)
    value = [{"title": "Round trip", "url": "https://example.com"}]

    dm.save("links", value)

    assert dm._load("links") == value
    assert not (tmp_path / "DC_Links.json.tmp").exists()


@pytest.mark.skipif(__import__("platform").system() != "Windows", reason="Windows DPAPI test")
def test_api_key_is_protected_on_disk(tmp_path: Path):
    dm = DataManager(tmp_path)
    dm.save("keys", [{
        "label": "OpenAI",
        "masked": "sk-****",
        "full_key": "secret-value",
    }])

    raw = (tmp_path / "DC_Keys.json").read_text(encoding="utf-8")
    assert "secret-value" not in raw

    loaded = dm.load_all()["keys"]
    assert loaded[0]["full_key"] == "secret-value"


def test_custom_colors_persistence(tmp_path: Path):
    dm = DataManager(tmp_path)
    data = dm.load_all()
    assert isinstance(data["custom_colors"], list)

    dm.save("custom_colors", ["#e8794a", "#4a7ce8"])
    reloaded = dm.load_all()
    assert reloaded["custom_colors"] == ["#e8794a", "#4a7ce8"]


def test_smooth_window_startup():
    """Verify MainWindow initializes without active resize animations and with native attributes."""
    import sys
    from PySide6.QtWidgets import QApplication
    from app.window.main_window import MainWindow

    app = QApplication.instance() or QApplication(sys.argv)
    win = MainWindow()

    assert getattr(win, "_native_transition_prepared", False) is True
    assert win._resize_anim is None
    assert win.stack.graphicsEffect() is None
    win.close()


def test_integrated_welcome_view():
    """Verify fresh launch displays the integrated WelcomeView, and Get Started transitions to ListView."""
    import sys
    from PySide6.QtWidgets import QApplication
    from app.window.main_window import MainWindow

    app = QApplication.instance() or QApplication(sys.argv)
    win = MainWindow()
    win.settings["welcome_seen"] = False

    # Simulate fresh launch
    win.show_welcome_view(animate=False)
    assert win.stack.currentWidget() == win.welcome_view
    assert win.height() == win.WINDOW_H_WELCOME

    # User clicks Get Started
    win.on_welcome_get_started()
    assert win.settings["welcome_seen"] is True
    assert win.stack.currentWidget() == win.list_view
    win.close()


