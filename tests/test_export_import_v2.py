"""Selective export, plain JSON, import preview, and the bug fixes around them."""

import json
import sys
import pytest

from app.core import export_import as ei
from app.core.data_manager import DataError

PW = "correct horse battery"


# ------------------------------------------------------------------ helpers
@pytest.fixture
def win(tmp_path):
    from PySide6.QtWidgets import QApplication
    from app.core.data_manager import DataManager
    from app.window.main_window import MainWindow

    QApplication.instance() or QApplication(sys.argv)
    w = MainWindow(DataManager(tmp_path))
    w.settings["welcome_seen"] = True
    return w


def prompt(i, text="body", **kw):
    return {
        "id": f"prompt_{i}",
        "name": f"P{i}",
        "prompt": text,
        "color": "#e8794a",
        "createdAt": i,
        **kw,
    }


def link(i, url="a.com"):
    return {"id": f"link_{i}", "title": f"L{i}", "url": url, "color": "#4a7ce8", "createdAt": i}


# ------------------------------------------------------------------ plain JSON
def test_plain_export_is_readable_and_mapped(tmp_path):
    sel = {
        "keys": [{"label": "K", "full_key": "sk-1", "color": "#fff"}],
        "prompts": [prompt(1)],
    }
    path = tmp_path / "x.json"
    stats = ei.export_to_file(
        path, sel, plain=True, include_secrets=True, app_version="9.9.9"
    )
    text = path.read_text(encoding="utf-8")
    doc = json.loads(text)
    assert doc["magic"] == ei.MAGIC and doc["kind"] == "plain"
    assert doc["meta"]["app_version"] == "9.9.9"
    assert doc["meta"]["sections"]["prompts"] == {"label": "Prompts", "count": 1}
    assert doc["meta"]["api_key_secrets_included"] is True and "warning" in doc["meta"]
    assert list(doc["data"]) == ["keys", "prompts"]
    assert "\n  " in text  # indented, i.e. readable
    assert list(doc["data"]["prompts"][0])[:2] == ["id", "name"]  # natural field order
    assert stats.total == 2


def test_plain_export_can_leave_secrets_out(tmp_path):
    sel = {"keys": [{"label": "K", "full_key": "sk-secret-999"}], "links": [link(1)]}
    path = tmp_path / "x.json"
    ei.export_to_file(path, sel, plain=True, include_secrets=False)
    text = path.read_text(encoding="utf-8")
    assert "sk-secret-999" not in text and "full_key" not in text
    assert json.loads(text)["meta"]["api_key_secrets_included"] is False


def test_plain_file_round_trips_and_needs_no_passphrase(tmp_path):
    path = tmp_path / "x.json"
    ei.export_to_file(path, {"links": [link(1)]}, plain=True)
    blob = path.read_bytes()
    assert ei.is_encrypted_bundle(blob) is False
    assert ei.read_bundle(blob)["links"] == [link(1)]


def test_plain_file_saved_with_bom_by_an_editor_still_opens(tmp_path):
    path = tmp_path / "x.json"
    ei.export_to_file(path, {"links": [link(1)]}, plain=True)
    with_bom = b"\xef\xbb\xbf" + path.read_bytes()
    assert ei.read_bundle(with_bom)["links"] == [link(1)]


def test_only_chosen_sections_are_written(tmp_path):
    path = tmp_path / "x.dizoclip"
    ei.export_to_file(path, {"links": [link(1)], "prompts": []}, passphrase=PW)
    assert list(ei.read_bundle(path.read_bytes(), PW)) == ["links"]


def test_nothing_selected_is_an_error(tmp_path):
    with pytest.raises(ei.ExportError):
        ei.export_to_file(tmp_path / "x.json", {"links": []}, plain=True)


def test_short_passphrase_still_rejected_for_selective_export(tmp_path):
    with pytest.raises(ei.ExportError):
        ei.export_to_file(
            tmp_path / "x.dizoclip", {"links": [link(1)]}, passphrase="short"
        )


def test_export_write_is_atomic_and_leaves_no_temp_file(tmp_path):
    path = tmp_path / "x.json"
    ei.export_to_file(path, {"links": [link(1)]}, plain=True)
    assert path.exists() and not (tmp_path / "x.json.tmp").exists()


def test_version_1_encrypted_files_from_the_old_app_still_open():
    blob = ei.build_bundle({"keys": [{"label": "A", "full_key": "k"}]}, PW)
    env = json.loads(blob)
    assert set(env) == {"magic", "version", "kdf", "data"}  # envelope shape unchanged
    assert ei.read_bundle(blob, PW)["keys"][0]["label"] == "A"


def test_wrong_passphrase_is_a_distinct_but_compatible_error():
    blob = ei.build_bundle({"keys": []}, PW)
    with pytest.raises(ei.WrongPassphrase):
        ei.read_bundle(blob, "not the passphrase")
    assert issubclass(ei.WrongPassphrase, ei.ExportError)


def test_random_json_is_not_mistaken_for_an_export():
    with pytest.raises(ei.ExportError):
        ei.read_bundle(b'{"keys": [], "prompts": []}')
    with pytest.raises(ei.ExportError):
        ei.read_bundle(b"[1,2,3]")


# ------------------------------------------------------------------ BUG P4: locked items
def test_locked_items_are_skipped_and_counted_not_silent():
    sel = {
        "keys": [
            {"label": "ok", "full_key": "k"},
            {"label": "locked", "full_key": "dpapi:xx", "_decrypt_failed": True},
        ]
    }
    payload, stats = ei.prepare_export(sel)
    assert payload["keys"] == [{"label": "ok", "full_key": "k"}]
    assert stats.skipped_locked == 1


# ------------------------------------------------------------------ import planning
def test_plan_labels_new_same_and_changed():
    current = {
        "prompts": [prompt(1), prompt(2, "old")],
        "links": [link(1)],
    }
    incoming = {
        "prompts": [prompt(1), prompt(2, "edited elsewhere"), prompt(3)],
        "links": [link(1)],
    }
    plan = ei.plan_import(current, incoming)
    status = {(i.dataset, i.item["id"]): i.status for i in plan.items}
    assert status[("prompts", "prompt_1")] == ei.SAME
    assert status[("prompts", "prompt_2")] == ei.CHANGED
    assert status[("prompts", "prompt_3")] == ei.NEW
    assert status[("links", "link_1")] == ei.SAME
    changed = next(i for i in plan.items if i.status == ei.CHANGED)
    assert changed.existing["prompt"] == "old"


def test_keys_are_matched_by_secret_not_label():
    current = {"keys": [{"label": "Old name", "full_key": "sk-same"}]}
    plan = ei.plan_import(
        current,
        {
            "keys": [
                {"label": "Renamed", "full_key": "sk-same"},
                {"label": "Old name", "full_key": "sk-different"},
            ]
        },
    )
    assert [i.status for i in plan.items] == [ei.CHANGED, ei.NEW]


def test_duplicate_inside_the_file_is_only_added_once():
    plan = ei.plan_import({}, {"links": [link(1), link(1)]})
    assert [i.status for i in plan.items] == [ei.NEW, ei.SAME]
    new_lists, added = ei.apply_plan(plan, {})
    assert added["links"] == 1 and len(new_lists["links"]) == 1


def test_locked_current_items_are_never_matched():
    current = {
        "keys": [
            {"label": "L", "full_key": "dpapi:zz", "_decrypt_failed": True}
        ]
    }
    plan = ei.plan_import(
        current, {"keys": [{"label": "L", "full_key": "sk-real"}]}
    )
    assert plan.items[0].status == ei.NEW


def test_keys_exported_without_secrets_are_reported_not_imported():
    plan = ei.plan_import(
        {}, {"keys": [{"label": "A"}, {"label": "B"}], "links": [link(1)]}
    )
    assert plan.keys_without_secret == 2
    assert plan.invalid == 0
    assert [i.dataset for i in plan.items] == ["links"]


def test_apply_plan_never_touches_the_current_lists():
    current = {"links": [link(1)]}
    plan = ei.plan_import(current, {"links": [link(2)]})
    new_lists, added = ei.apply_plan(plan, current)
    assert added["links"] == 1
    assert len(current["links"]) == 1 and len(new_lists["links"]) == 2


def test_changed_item_is_imported_as_a_separate_copy_on_request():
    current = {"prompts": [prompt(2, "old")]}
    plan = ei.plan_import(current, {"prompts": [prompt(2, "new text")]})
    assert ei.apply_plan(plan, current)[1]["prompts"] == 0  # default: skipped
    new_lists, added = ei.apply_plan(plan, current, chosen={0})  # explicitly ticked
    assert added["prompts"] == 1
    original, copy_ = new_lists["prompts"]
    assert original["prompt"] == "old" and original["id"] == "prompt_2"  # untouched
    assert (
        copy_["prompt"] == "new text" and copy_["id"] != "prompt_2"
    )  # no duplicate id
    assert copy_["name"].endswith("(imported)")


def test_chosen_can_never_import_a_matched_item():
    current = {"links": [link(1)]}
    plan = ei.plan_import(current, {"links": [link(1)]})
    assert ei.apply_plan(plan, current, chosen={0})[1]["links"] == 0


# ------------------------------------------------------------------ BUG P2: malformed data
@pytest.mark.parametrize(
    "name,bad",
    [
        ("prompts", {"name": "X", "prompt": 123}),
        ("prompts", {"prompt": "no title"}),
        ("ai_models", {"name": "M", "snippets": "not a dict"}),
        ("ai_models", {"name": "M", "snippets": {"Python": 5}}),
        ("links", {"title": ["a"], "url": 5}),
        ("commands", {"title": "c", "command": {"a": 1}}),
        ("keys", {"label": 7, "full_key": "sk"}),
        ("links", {"id": "", "title": "t", "url": "u"}),
        ("links", {"title": "t", "url": "u", "color": None}),
        ("links", {"title": "t", "url": "u", "createdAt": "yesterday"}),
    ],
)
def test_malformed_records_are_dropped(name, bad):
    kept, dropped = ei.sanitize_incoming(name, [bad])
    assert kept == [] and dropped == 1


def test_valid_records_survive_and_private_fields_are_stripped():
    kept, dropped = ei.sanitize_incoming(
        "ai_models",
        [
            {
                "id": "model_1",
                "name": "M",
                "snippets": {"Python": "print(1)"},
                "_decrypt_failed": True,
            }
        ],
    )
    assert dropped == 0 and kept == [
        {"id": "model_1", "name": "M", "snippets": {"Python": "print(1)"}}
    ]


def test_damaged_ai_model_import_no_longer_breaks_the_tab(win, tmp_path):
    """Before: this import was saved and then crashed the AI Models tab."""
    path = tmp_path / "bad.dizoclip"
    path.write_bytes(
        ei.build_bundle({"ai_models": [{"name": "M", "snippets": "oops"}]}, PW)
    )
    assert sum(win.import_data(str(path), PW).values()) == 0
    win.list_view.select_tab("ai_model", animate=False)
    win.show_list_view(animate=False)  # would raise AttributeError before the fix


def test_search_and_card_survive_damaged_data_already_on_disk(win):
    """Hand-edited data files: a non-dict `snippets` must not crash search or the card."""
    from app.sections.registry import SECTION_REGISTRY

    win.ai_models.append(
        {"id": "m", "name": "Broken", "snippets": "oops", "color": "#fff"}
    )
    assert SECTION_REGISTRY["ai_model"]["match"](win.ai_models[0], "brok") is True
    win.list_view.select_tab("ai_model", animate=False)
    win.show_list_view(animate=False)


# ------------------------------------------------------------------ window level
def test_edited_item_is_not_duplicated_when_an_old_export_is_imported(win, tmp_path):
    """BUG P1: the old compare used the whole record, so an edit made a 'new' duplicate."""
    win.prompts.append(prompt(1, "old"))
    win.save_prompts()
    path = str(tmp_path / "a.dizoclip")
    win.export_data(path, PW)
    win.prompts[0]["prompt"] = "edited after export"
    win.save_prompts()
    assert sum(win.import_data(path, PW).values()) == 0
    assert [p["id"] for p in win.prompts] == ["prompt_1"]
    assert win.prompts[0]["prompt"] == "edited after export"


def test_import_save_failure_leaves_memory_and_disk_consistent(
    win, tmp_path, monkeypatch
):
    """BUG P3: a failed save used to leave unsaved items on screen and raise out of the UI."""
    path = tmp_path / "a.json"
    ei.export_to_file(path, {"links": [link(9)]}, plain=True)

    def boom(*a, **k):
        raise DataError("disk full")

    monkeypatch.setattr(win.data_manager, "save_all", boom)
    with pytest.raises(DataError):
        win.import_data(str(path))
    assert win.links == []


def test_import_updates_lists_in_place(win, tmp_path):
    held = win.links  # another view may hold this very list
    path = tmp_path / "a.json"
    ei.export_to_file(path, {"links": [link(1)]}, plain=True)
    win.import_data(str(path))
    assert held is win.links and len(held) == 1


def test_plain_json_round_trip_between_two_installs(win, tmp_path):
    win.keys.append({"label": "K", "full_key": "sk-777", "color": "#e8794a"})
    win.links.append(link(1))
    win.save_keys()
    win.save_links()
    path = str(tmp_path / "share.json")
    win.export_selected(
        path,
        {"keys": win.keys, "links": win.links},
        plain=True,
        include_secrets=True,
    )
    from app.core.data_manager import DataManager
    from app.window.main_window import MainWindow

    other = MainWindow(DataManager(tmp_path / "other"))
    other.settings["welcome_seen"] = True
    assert other.import_data(path) == {
        "keys": 1,
        "prompts": 0,
        "ai_models": 0,
        "links": 1,
        "commands": 0,
    }
    assert other.keys[0]["full_key"] == "sk-777"
    assert other.import_data(path) == {
        n: 0 for n in ei.EXPORT_DATASETS
    }  # idempotent


def test_old_import_data_signature_still_works_for_encrypted_files(win, tmp_path):
    win.links.append(link(1))
    win.save_links()
    path = str(tmp_path / "a.dizoclip")
    win.export_data(path, PW)  # original 2-argument call
    win.links.clear()
    assert win.import_data(path, PW)["links"] == 1


# ------------------------------------------------------------------ dialogs
def _tops(tree):
    """{'API Keys': <category row>, ...}"""
    res = {}
    for i in range(tree.topLevelItemCount()):
        item = tree.topLevelItem(i)
        t = item.text(0)
        res[t.split(" · ")[0].strip()] = item
        res[t.split(" ")[0]] = item
    return res


def _row_for(tree, plan_index):
    """The tree row that represents plan item `plan_index`."""
    from PySide6.QtCore import Qt

    for t in range(tree.topLevelItemCount()):
        top = tree.topLevelItem(t)
        for c in range(top.childCount()):
            if top.child(c).data(0, Qt.UserRole) == plan_index:
                return top.child(c)
    raise AssertionError("row not found")


def test_export_dialog_selection_follows_the_ticks(win):
    from PySide6.QtCore import Qt
    from app.components.dialogs.export_dialog import ExportDialog

    win.keys.extend(
        [{"label": "A", "full_key": "k1"}, {"label": "B", "full_key": "k2"}]
    )
    win.links.append(link(1))
    d = ExportDialog(win)
    assert d.count_lbl.text() == "3 of 3 selected"
    tops = _tops(d.tree)
    tops["API Keys"].child(1).setCheckState(0, Qt.Unchecked)  # untick key B
    assert [k["label"] for k in d.selection()["keys"]] == ["A"]
    assert tops["API Keys"].checkState(0) == Qt.PartiallyChecked
    tops["Links"].setCheckState(0, Qt.Unchecked)  # untick whole category
    assert "links" not in d.selection()
    d._set_all(Qt.Unchecked)
    assert d.selection() == {} and not d.export_btn.isEnabled()
    d._set_all(Qt.Checked)
    assert d.count_lbl.text() == "3 of 3 selected"


def test_export_dialog_locked_items_cannot_be_ticked(win):
    from app.components.dialogs.export_dialog import ExportDialog

    win.keys.extend(
        [
            {"label": "ok", "full_key": "k"},
            {"label": "locked", "full_key": "dpapi:x", "_decrypt_failed": True},
        ]
    )
    d = ExportDialog(win)
    assert [k["label"] for k in d.selection()["keys"]] == ["ok"]
    assert d.count_lbl.text() == "1 of 1 selected"


def test_export_dialog_rules_for_format_secrets_and_passphrase(win):
    from app.components.dialogs.export_dialog import ExportDialog

    win.keys.append({"label": "A", "full_key": "k"})
    d = ExportDialog(win)
    d.show()
    assert not d.is_plain() and d.include_secrets() and not d.export_btn.isEnabled()
    d.pw1.setText("short")
    d.pw2.setText("short")
    assert not d.export_btn.isEnabled()  # under 8 characters
    d.pw1.setText(PW)
    d.pw2.setText(PW + "x")
    assert not d.export_btn.isEnabled() and "match" in d.pw_error.text()
    d.pw2.setText(PW)
    assert d.export_btn.isEnabled()
    d.btn_plain.setChecked(True)
    assert not d.include_secrets()  # safe default for readable files
    assert (
        d.export_btn.isEnabled() and not d.secrets_warn.isVisible()
    )  # no passphrase needed
    d.secrets_box.setChecked(True)
    assert d.secrets_warn.isVisible()  # red warning appears


def test_import_dialog_defaults_to_new_items_only(win):
    from app.components.dialogs.import_dialog import ImportDialog

    win.prompts.extend([prompt(1), prompt(2, "old")])
    plan = ei.plan_import(
        {"prompts": win.prompts, "links": []},
        {"prompts": [prompt(1), prompt(2, "edited"), prompt(3)], "links": [link(1)]},
    )
    d = ImportDialog(win, plan, "file.dizoclip")
    status = {i: inc.status for i, inc in enumerate(plan.items)}
    assert {status[i] for i in d.chosen_indexes()} == {ei.NEW}
    assert len(d.chosen_indexes()) == 2 and d.import_btn.text() == "Import 2 items"
    changed_idx = next(i for i, s in status.items() if s == ei.CHANGED)
    from PySide6.QtCore import Qt

    _row_for(d.tree, changed_idx).setCheckState(
        0, Qt.Checked
    )  # user ticks the 'changed' row
    assert (
        changed_idx in d.chosen_indexes()
        and d.import_btn.text() == "Import 3 items"
    )


def test_import_dialog_with_only_matched_items_cannot_import(win):
    from app.components.dialogs.import_dialog import ImportDialog

    win.links.append(link(1))
    plan = ei.plan_import({"links": win.links}, {"links": [link(1)]})
    d = ImportDialog(win, plan)
    assert d.chosen_indexes() == set() and not d.import_btn.isEnabled()
    assert "1 matched" in d.summary.text()


# ------------------------------------------------------------------ the buttons in Settings, end to end
@pytest.fixture
def stub_ui(monkeypatch):
    """Replace OS file pickers and message boxes; collect what the user would have seen."""
    from PySide6.QtWidgets import QFileDialog, QMessageBox

    seen = {"boxes": []}
    for kind in ("information", "warning", "critical"):
        monkeypatch.setattr(
            QMessageBox,
            kind,
            staticmethod(
                lambda parent, title, text, *a, _k=kind, **k: seen["boxes"].append(
                    (_k, text)
                )
                or QMessageBox.Yes
            ),
        )
    seen["open"] = lambda p: monkeypatch.setattr(
        QFileDialog, "getOpenFileName", staticmethod(lambda *a, **k: (p, ""))
    )
    seen["save"] = lambda p: monkeypatch.setattr(
        QFileDialog, "getSaveFileName", staticmethod(lambda *a, **k: (p, ""))
    )
    return seen


def test_settings_import_button_encrypted_file_with_one_wrong_passphrase(
    win, tmp_path, stub_ui, monkeypatch
):
    from PySide6.QtWidgets import QDialog
    from app.components.dialogs.import_dialog import ImportDialog

    path = tmp_path / "a.dizoclip"
    ei.export_to_file(path, {"links": [link(1), link(2)]}, passphrase=PW)
    stub_ui["open"](str(path))
    answers = iter(
        ["wrong passphrase!", PW]
    )  # first try is wrong, second is right
    monkeypatch.setattr(
        win.settings_view, "_ask_passphrase", lambda *a: next(answers)
    )
    monkeypatch.setattr(
        ImportDialog, "exec", lambda self: QDialog.Accepted
    )  # user presses Import
    win.settings_view._on_import_clicked()
    assert [x["id"] for x in win.links] == ["link_1", "link_2"]
    kinds = [k for k, _ in stub_ui["boxes"]]
    assert kinds == [
        "warning",
        "information",
    ]  # one retry prompt, then success
    assert "Imported 2" in stub_ui["boxes"][-1][1]


def test_settings_import_button_cancel_changes_nothing(
    win, tmp_path, stub_ui, monkeypatch
):
    from PySide6.QtWidgets import QDialog
    from app.components.dialogs.import_dialog import ImportDialog

    path = tmp_path / "a.json"
    ei.export_to_file(path, {"links": [link(1)]}, plain=True)
    stub_ui["open"](str(path))
    monkeypatch.setattr(
        ImportDialog, "exec", lambda self: QDialog.Rejected
    )  # user presses Cancel
    win.settings_view._on_import_clicked()
    assert win.links == [] and stub_ui["boxes"] == []


def test_settings_import_button_rejects_a_foreign_file(win, tmp_path, stub_ui):
    path = tmp_path / "x.json"
    path.write_text('{"hello": "world"}', encoding="utf-8")
    stub_ui["open"](str(path))
    win.settings_view._on_import_clicked()
    assert (
        stub_ui["boxes"][0][0] == "critical"
        and "Import failed" in stub_ui["boxes"][0][1]
    )


def test_export_dialog_writes_a_plain_file_with_only_the_ticked_items(
    win, tmp_path, stub_ui
):
    from PySide6.QtCore import Qt
    from app.components.dialogs.export_dialog import ExportDialog

    win.keys.append({"label": "K", "full_key": "sk-top-secret"})
    win.prompts.extend([prompt(1), prompt(2)])
    d = ExportDialog(win)
    d.btn_plain.setChecked(True)  # secrets off by default for plain
    _tops(d.tree)["Prompts"].child(1).setCheckState(0, Qt.Unchecked)
    out = tmp_path / "share.json"
    stub_ui["save"](str(out))
    d._on_export()
    text = out.read_text(encoding="utf-8")
    assert "sk-top-secret" not in text  # key row exported without its secret
    doc = json.loads(text)
    assert [p["id"] for p in doc["data"]["prompts"]] == ["prompt_1"]
    assert (
        stub_ui["boxes"][-1][0] == "information"
        and "Exported 2" in stub_ui["boxes"][-1][1]
    )


def test_export_dialog_warns_before_writing_secrets_as_plain_text(
    win, tmp_path, stub_ui, monkeypatch
):
    from PySide6.QtWidgets import QMessageBox
    from app.components.dialogs.export_dialog import ExportDialog

    win.keys.append({"label": "K", "full_key": "sk-top-secret"})
    d = ExportDialog(win)
    d.btn_plain.setChecked(True)
    d.secrets_box.setChecked(True)
    out = tmp_path / "share.json"
    stub_ui["save"](str(out))
    monkeypatch.setattr(
        QMessageBox, "warning", staticmethod(lambda *a, **k: QMessageBox.No)
    )  # user says No to the warning
    d._on_export()
    assert not out.exists()  # nothing was written
