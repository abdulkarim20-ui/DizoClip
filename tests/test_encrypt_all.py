import json
import pytest

from app.core.data_manager import DataManager
from app.core.security import protect_text

SECRET = "ghp_abcdefghijklmnopqrstuvwxyz0123456789"


def make_dm(tmp_path):
    return DataManager(tmp_path, backup_min_interval=0)


def test_prompts_commands_and_snippets_are_plain_text_on_disk(tmp_path):
    dm = make_dm(tmp_path)
    dm.load_all()
    dm.save("prompts", [{"id": "1", "name": "p", "prompt": f"use token {SECRET}"}])
    dm.save("commands", [{"id": "2", "title": "c", "command": f"curl -H 'Authorization: {SECRET}'"}])
    dm.save("ai_models", [{"id": "3", "name": "m", "snippets": {"Shell": f"export KEY={SECRET}"}}])

    for fname in ("DC_Prompts.json", "DC_Commands.json", "DC_AI_Models.json"):
        text = (tmp_path / fname).read_text(encoding="utf-8")
        assert SECRET in text, f"{fname} should store plain text readable JSON"


@pytest.mark.skipif(__import__("platform").system() != "Windows", reason="Windows DPAPI test")
def test_api_keys_are_encrypted_on_disk(tmp_path):
    dm = make_dm(tmp_path)
    dm.load_all()
    dm.save("keys", [{"id": "1", "name": "k", "full_key": SECRET}])

    text = (tmp_path / "DC_Keys.json").read_text(encoding="utf-8")
    assert SECRET not in text
    assert "dpapi:" in text


def test_round_trip_returns_the_original_text(tmp_path):
    dm = make_dm(tmp_path)
    dm.load_all()
    dm.save("prompts", [{"id": "1", "name": "p", "prompt": f"use token {SECRET}"}])
    dm.save("ai_models", [{"id": "3", "name": "m", "snippets": {"Shell": f"export KEY={SECRET}", "Python": "print(1)"}}])

    loaded = make_dm(tmp_path).load_all()
    assert loaded["prompts"][0]["prompt"] == f"use token {SECRET}"
    assert loaded["ai_models"][0]["snippets"] == {"Shell": f"export KEY={SECRET}", "Python": "print(1)"}


@pytest.mark.skipif(__import__("platform").system() != "Windows", reason="Windows DPAPI test")
def test_legacy_dzc1_prompts_are_auto_migrated_to_plain_text(tmp_path):
    enc_blob = protect_text("migrated prompt content")
    (tmp_path / "DC_Prompts.json").write_text(
        json.dumps([{"id": "1", "name": "p", "prompt": enc_blob}]), encoding="utf-8"
    )

    dm = make_dm(tmp_path)
    loaded = dm.load_all()
    assert loaded["prompts"][0]["prompt"] == "migrated prompt content"

    # Verify that the file on disk has been migrated to plain text
    disk_text = (tmp_path / "DC_Prompts.json").read_text(encoding="utf-8")
    assert "migrated prompt content" in disk_text
    assert "dzc1:" not in disk_text


def test_plaintext_prompt_that_starts_with_plain_is_not_mangled(tmp_path):
    dm = make_dm(tmp_path)
    dm.load_all()
    dm.save("prompts", [{"id": "1", "name": "p", "prompt": "plain: keep this exactly"}])
    assert make_dm(tmp_path).load_all()["prompts"][0]["prompt"] == "plain: keep this exactly"


def test_undecryptable_prompt_is_preserved_untouched(tmp_path):
    blob = "dzc1:dpapi:AAAA"
    (tmp_path / "DC_Prompts.json").write_text(
        json.dumps([{"id": "1", "name": "Locked", "prompt": blob}]), encoding="utf-8")
    dm = make_dm(tmp_path)
    prompts = dm.load_all()["prompts"]
    assert prompts[0]["_decrypt_failed"] is True

    prompts[0]["name"] = "Renamed"
    dm.save("prompts", prompts)

    saved = json.loads((tmp_path / "DC_Prompts.json").read_text(encoding="utf-8"))
    assert saved[0]["prompt"] == blob
    assert "_decrypt_failed" not in saved[0]
