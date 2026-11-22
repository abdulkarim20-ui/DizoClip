"""Selective export, import preview, and the bug fixes around them.

DizoClip has ONE file format: encrypted .dizoclip. Plain JSON and .env are not supported.
"""

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


# ------------------------------------------------------------------ one format: encrypted only
def test_export_is_always_an_encrypted_envelope_with_secrets_inside(tmp_path):
    sel = {"keys": [{"label": "K", "full_key": "sk-secret-999", "color": "#fff"}], "links": [link(1)]}
    path = tmp_path / "x.dizoclip"
    stats = ei.export_to_file(path, sel, passphrase=PW)
    blob = path.read_bytes()
    assert set(json.loads(blob)) == {"magic", "version", "kdf", "data"}
    assert b"sk-secret-999" not in blob  # never readable on disk
    assert ei.read_bundle(blob, PW)["keys"][0]["full_key"] == "sk-secret-999"  # but it is in there
    assert stats.total == 2


def test_export_without_a_passphrase_is_refused_and_writes_nothing(tmp_path):
    path = tmp_path / "x.dizoclip"
    with pytest.raises(ei.ExportError):
        ei.export_to_file(path, {"links": [link(1)]})
    assert not path.exists()


def test_plain_json_files_are_rejected_on_import():
    plain = json.dumps(
        {"magic": ei.MAGIC, "version": ei.FORMAT_VERSION, "kind": "plain", "meta": {}, "data": {"links": [link(1)]}}
    ).encode()
    for fn in (ei.require_encrypted_bundle, ei.read_bundle):
        with pytest.raises(ei.ExportError, match=r"\.dizoclip"):
            fn(plain)
    with pytest.raises(ei.ExportError):
        ei.read_bundle(plain, PW)  # a passphrase does not make it importable


def test_env_files_are_rejected_on_import():
    env = b"OPENAI_API_KEY=sk-123\nGROQ_API_KEY=gsk-456\n"
    with pytest.raises(ei.ExportError, match=r"\.dizoclip"):
        ei.require_encrypted_bundle(env)
    with pytest.raises(ei.ExportError, match=r"\.dizoclip"):
        ei.read_bundle(env, PW)


def test_the_removed_plaintext_helpers_are_really_gone():
    for name in ("build_plain", "build_env_text", "parse_env_text", "is_env_bundle", "is_encrypted_bundle"):
        assert not hasattr(ei, name), name


def test_only_chosen_sections_are_written(tmp_path):
    path = tmp_path / "x.dizoclip"
    ei.export_to_file(path, {"links": [link(1)], "prompts": []}, passphrase=PW)
    assert list(ei.read_bundle(path.read_bytes(), PW)) == ["links"]


def test_nothing_selected_is_an_error(tmp_path):
    with pytest.raises(ei.ExportError):
        ei.export_to_file(tmp_path / "x.dizoclip", {"links": []}, passphrase=PW)


def test_short_passphrase_still_rejected_for_selective_export(tmp_path):
    with pytest.raises(ei.ExportError):
        ei.export_to_file(
            tmp_path / "x.dizoclip", {"links": [link(1)]}, passphrase="short"
        )


def test_export_write_is_atomic_and_leaves_no_temp_file(tmp_path):
    path = tmp_path / "x.dizoclip"
    ei.export_to_file(path, {"links": [link(1)]}, passphrase=PW)
    assert path.exists() and not (tmp_path / "x.dizoclip.tmp").exists()


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


def test_keys_without_a_secret_are_dropped_as_damaged():
    plan = ei.plan_import(
        {}, {"keys": [{"label": "A"}, {"label": "B"}], "links": [link(1)]}
    )
    assert plan.invalid == 2
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
    path = tmp_path / "a.dizoclip"
    ei.export_to_file(path, {"links": [link(9)]}, passphrase=PW)

    def boom(*a, **k):
        raise DataError("disk full")

    monkeypatch.setattr(win.data_manager, "save_all", boom)
    with pytest.raises(DataError):
        win.import_data(str(path), PW)
    assert win.links == []


def test_import_updates_lists_in_place(win, tmp_path):
    held = win.links  # another view may hold this very list
    path = tmp_path / "a.dizoclip"
    ei.export_to_file(path, {"links": [link(1)]}, passphrase=PW)
    win.import_data(str(path), PW)
    assert held is win.links and len(held) == 1


def test_encrypted_round_trip_between_two_installs(win, tmp_path):
    win.keys.append({"label": "K", "full_key": "sk-777", "color": "#e8794a"})
    win.links.append(link(1))
    win.save_keys()
    win.save_links()
    path = str(tmp_path / "share.dizoclip")
    win.export_selected(path, {"keys": win.keys, "links": win.links}, passphrase=PW)
    from app.core.data_manager import DataManager
    from app.window.main_window import MainWindow

    other = MainWindow(DataManager(tmp_path / "other"))
    other.settings["welcome_seen"] = True
    assert other.import_data(path, PW) == {
        "keys": 1,
        "prompts": 0,
        "ai_models": 0,
        "links": 1,
        "commands": 0,
    }
    assert other.keys[0]["full_key"] == "sk-777"
    assert other.import_data(path, PW) == {
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


def test_export_dialog_hides_empty_sections(win):
    from app.components.dialogs.export_dialog import ExportDialog

    d_empty = ExportDialog(win)
    assert d_empty.tree.topLevelItemCount() == 1
    assert "No items" in d_empty.tree.topLevelItem(0).text(0)

    win.keys.append({"label": "A", "full_key": "k"})
    d = ExportDialog(win)
    assert d.tree.topLevelItemCount() == 1
    assert d.tree.topLevelItem(0).text(0).startswith("API Keys")


def test_export_dialog_rules_for_passphrase(win):
    from PySide6.QtWidgets import QLineEdit
    from app.components.dialogs.export_dialog import ExportDialog

    win.keys.append({"label": "A", "full_key": "k"})
    d = ExportDialog(win)
    d.show()
    assert not d.export_btn.isEnabled()  # no password yet
    d.pw1.setText("short")
    assert not d.export_btn.isEnabled()  # under 8 characters
    assert "8 characters" in d.pw_error.text()
    d.pw1.setText(PW)
    assert d.export_btn.isEnabled()

    # Test eye reveal toggling
    assert d.pw1.echoMode() == QLineEdit.Password
    d.eye_action.trigger()
    assert d.pw1.echoMode() == QLineEdit.Normal
    d.eye_action.trigger()
    assert d.pw1.echoMode() == QLineEdit.Password


def test_export_dialog_has_no_plaintext_options(win):
    from app.components.dialogs.export_dialog import ExportDialog

    d = ExportDialog(win)
    for gone in ("btn_plain", "btn_env", "btn_enc", "secrets_box", "secrets_warn"):
        assert not hasattr(d, gone), gone


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

    path = tmp_path / "a.dizoclip"
    ei.export_to_file(path, {"links": [link(1)]}, passphrase=PW)
    stub_ui["open"](str(path))
    monkeypatch.setattr(win.settings_view, "_ask_passphrase", lambda *a: PW)
    monkeypatch.setattr(
        ImportDialog, "exec", lambda self: QDialog.Rejected
    )  # user presses Cancel
    win.settings_view._on_import_clicked()
    assert win.links == [] and stub_ui["boxes"] == []


@pytest.mark.parametrize(
    "name, content",
    [
        ("plain.json", json.dumps({"magic": ei.MAGIC, "version": 1, "kind": "plain", "meta": {}, "data": {"links": [{"id": "l", "title": "t", "url": "u"}]}})),
        ("keys.env", "OPENAI_API_KEY=sk-123\n"),
    ],
)
def test_settings_import_button_rejects_json_and_env_without_asking_for_a_passphrase(
    win, tmp_path, stub_ui, monkeypatch, name, content
):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    stub_ui["open"](str(path))

    def must_not_ask(*a):
        raise AssertionError("asked for a passphrase for a file that can never be imported")

    monkeypatch.setattr(win.settings_view, "_ask_passphrase", must_not_ask)
    win.settings_view._on_import_clicked()
    kind, text = stub_ui["boxes"][0]
    assert kind == "critical" and "Import failed" in text
    assert win.links == [] and win.keys == []


def test_settings_import_button_rejects_a_foreign_file(win, tmp_path, stub_ui):
    path = tmp_path / "x.json"
    path.write_text('{"hello": "world"}', encoding="utf-8")
    stub_ui["open"](str(path))
    win.settings_view._on_import_clicked()
    assert (
        stub_ui["boxes"][0][0] == "critical"
        and "Import failed" in stub_ui["boxes"][0][1]
    )


def test_export_dialog_writes_an_encrypted_file_with_only_the_ticked_items(
    win, tmp_path, stub_ui
):
    from PySide6.QtCore import Qt
    from app.components.dialogs.export_dialog import ExportDialog

    win.keys.append({"label": "K", "full_key": "sk-top-secret"})
    win.prompts.extend([prompt(1), prompt(2)])
    d = ExportDialog(win)
    d.pw1.setText(PW)
    d.pw2.setText(PW)
    _tops(d.tree)["Prompts"].child(1).setCheckState(0, Qt.Unchecked)
    out = tmp_path / "share.dizoclip"
    stub_ui["save"](str(out))
    d._on_export()
    blob = out.read_bytes()
    assert b"sk-top-secret" not in blob  # never readable in the file
    data = ei.read_bundle(blob, PW)
    assert [p["id"] for p in data["prompts"]] == ["prompt_1"]  # only the ticked prompt
    assert data["keys"][0]["full_key"] == "sk-top-secret"  # the key travels, encrypted
    assert (
        stub_ui["boxes"][-1][0] == "information"
        and "Exported 2" in stub_ui["boxes"][-1][1]
    )
