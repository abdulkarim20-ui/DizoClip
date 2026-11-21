import json
from pathlib import Path

import pytest

from app.core.backup_manager import BackupError, BackupManager
from app.core.data_manager import DataError, DataManager


def make_dm(tmp_path: Path, **kw) -> DataManager:
    kw.setdefault("backup_min_interval", 0)  # tests control debounce explicitly
    return DataManager(tmp_path, **kw)


# ---------------------------------------------------------------- #3 backups
def test_settings_saves_do_not_evict_key_backups(tmp_path):
    dm = make_dm(tmp_path, backup_count=3)
    dm.load_all()
    dm.save("keys", [{"label": "A", "full_key": "k1"}])
    dm.save("keys", [{"label": "B", "full_key": "k2"}])
    before = len(dm.backups_for("keys"))
    assert before >= 1

    settings = dm.load_all()["settings"]
    for i in range(20):
        settings["tick"] = i
        dm.save("settings", settings)

    assert len(dm.backups_for("keys")) == before
    assert len(dm.backups_for("settings")) <= 4


def test_backups_are_pruned_per_dataset(tmp_path):
    dm = make_dm(tmp_path, backup_count=3)
    dm.load_all()
    for i in range(12):
        dm.save("links", [{"title": str(i), "url": "https://example.com"}])
    assert 1 <= len(dm.backups_for("links")) <= 4


def test_a_burst_of_saves_creates_one_backup(tmp_path):
    dm = make_dm(tmp_path, backup_min_interval=60)
    dm.load_all()
    for i in range(6):
        dm.save("links", [{"title": str(i), "url": "https://example.com"}])
    assert len(dm.backups_for("links")) == 1


def test_unchanged_save_is_a_no_op(tmp_path):
    dm = make_dm(tmp_path)
    links = dm.load_all()["links"]
    dm.save("links", links)
    assert dm.backups_for("links") == []


def test_existing_dataset_is_backed_up_before_save(tmp_path):
    dm = make_dm(tmp_path)
    dm.load_all()
    dm.save("links", [{"title": "One", "url": "https://example.com"}])
    dm.save("links", [{"title": "Two", "url": "https://example.org"}])
    assert dm.backups_for("links")


def test_legacy_backup_layout_is_migrated(tmp_path):
    old = tmp_path / "Backups" / "20260101-000000-000000"
    old.mkdir(parents=True)
    (old / "DC_Links.json").write_text("[]", encoding="utf-8")

    mgr = BackupManager(tmp_path)

    assert len(mgr.list_backups("DC_Links")) == 1
    assert not old.exists()


# ---------------------------------------------------------------- #4 (data half) restore
def test_restore_round_trip(tmp_path):
    dm = make_dm(tmp_path)
    dm.load_all()
    state_a = [{"title": "A", "url": "https://a.example"}]
    dm.save("links", state_a)
    dm.save("links", [{"title": "B", "url": "https://b.example"}])

    newest = dm.backups_for("links")[0]  # snapshot of state A
    dm.restore_backup(newest)

    assert dm.load_all()["links"] == state_a


def test_corrupt_file_raises_with_dataset_name_and_can_be_restored(tmp_path):
    dm = make_dm(tmp_path)
    dm.load_all()
    dm.save("links", [{"title": "A", "url": "https://a.example"}])
    dm.save("links", [{"title": "B", "url": "https://b.example"}])
    (tmp_path / "DC_Links.json").write_text("{broken", encoding="utf-8")

    with pytest.raises(DataError) as exc:
        dm.load_all()
    assert exc.value.dataset == "links"

    dm.restore_backup(dm.backups_for("links")[0])
    assert dm.load_all()["links"][0]["title"] == "A"
    # the broken file is set aside, never mixed into the backup history
    assert list((tmp_path / "Corrupt").glob("DC_Links-*.json"))
    for entry in dm.backups_for("links"):
        json.loads(entry.path.read_text(encoding="utf-8"))


def test_restore_rejects_a_backup_with_the_wrong_shape(tmp_path):
    dm = make_dm(tmp_path)
    dm.load_all()
    dm.save("links", [{"title": "A", "url": "u"}])
    dm.save("links", [{"title": "B", "url": "u"}])
    bad = dm.backups.backup_dir / "DC_Links" / "20990101-000000-000000.json"
    bad.write_text("{}", encoding="utf-8")  # valid JSON, but a dict instead of a list

    newest = dm.backups_for("links")[0]
    assert newest.path == bad
    with pytest.raises(BackupError):
        dm.restore_backup(newest)


# ---------------------------------------------------------------- #1 masked on disk
def test_masked_is_never_written_to_disk(tmp_path):
    dm = make_dm(tmp_path)
    dm.load_all()
    dm.save("keys", [{
        "label": "OpenAI",
        "masked": "sk-" + "*" * 20 + "xyz",
        "full_key": "sk-secret-value-1234",
    }])
    raw = (tmp_path / "DC_Keys.json").read_text(encoding="utf-8")
    assert "masked" not in raw
    assert "*" * 8 not in raw


def test_old_masked_fragments_are_scrubbed_from_file_and_backups(tmp_path):
    legacy = [{"label": "Old", "masked": "sk-" + "*" * 20 + "xyz",
               "full_key": "sk-plain-legacy-secret", "color": "#e8794a"}]
    (tmp_path / "DC_Keys.json").write_text(json.dumps(legacy), encoding="utf-8")

    dm = make_dm(tmp_path)
    keys = dm.load_all()["keys"]

    assert keys[0]["full_key"] == "sk-plain-legacy-secret"
    assert "masked" not in keys[0]
    assert "masked" not in (tmp_path / "DC_Keys.json").read_text(encoding="utf-8")
    for snap in (tmp_path / "Backups" / "DC_Keys").glob("*.json"):
        assert "masked" not in snap.read_text(encoding="utf-8")


def test_migration_runs_once(tmp_path):
    legacy = [{"label": "Old", "masked": "sk-****", "full_key": "sk-plain-legacy-secret"}]
    (tmp_path / "DC_Keys.json").write_text(json.dumps(legacy), encoding="utf-8")

    make_dm(tmp_path).load_all()
    count = len(list((tmp_path / "Backups" / "DC_Keys").glob("*.json")))
    make_dm(tmp_path).load_all()  # second launch
    assert len(list((tmp_path / "Backups" / "DC_Keys").glob("*.json"))) == count


def test_undecryptable_key_is_preserved_untouched(tmp_path):
    blob = "dpapi:AAAA"  # valid base64, but not a real DPAPI blob
    (tmp_path / "DC_Keys.json").write_text(
        json.dumps([{"label": "Locked", "full_key": blob, "color": "#e8794a"}]),
        encoding="utf-8",
    )
    dm = make_dm(tmp_path)
    keys = dm.load_all()["keys"]
    assert keys[0]["_decrypt_failed"] is True

    keys[0]["label"] = "Renamed"
    dm.save("keys", keys)

    saved = json.loads((tmp_path / "DC_Keys.json").read_text(encoding="utf-8"))
    assert saved[0]["full_key"] == blob          # blob survived
    assert saved[0]["label"] == "Renamed"
    assert "_decrypt_failed" not in saved[0]     # in-memory flag never reaches disk


@pytest.mark.skipif(__import__("platform").system() != "Windows", reason="Windows DPAPI test")
def test_secret_is_not_readable_on_disk(tmp_path):
    dm = make_dm(tmp_path)
    dm.load_all()
    dm.save("keys", [{"label": "OpenAI", "full_key": "sk-super-secret-value"}])
    assert "sk-super-secret-value" not in (tmp_path / "DC_Keys.json").read_text(encoding="utf-8")
    assert dm.load_all()["keys"][0]["full_key"] == "sk-super-secret-value"
