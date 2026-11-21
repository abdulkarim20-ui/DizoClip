import pytest

from app.core.export_import import (
    ExportError,
    build_bundle,
    clean_for_export,
    clean_incoming,
    merge_into,
    open_bundle,
)

PW = "correct horse battery"


def test_round_trip_and_secret_not_visible_in_file():
    payload = {"keys": [{"label": "A", "full_key": "sk-visible-check-123"}], "prompts": []}
    blob = build_bundle(payload, PW)
    assert b"sk-visible-check-123" not in blob
    assert open_bundle(blob, PW) == payload


def test_wrong_passphrase_is_rejected():
    blob = build_bundle({"keys": []}, PW)
    with pytest.raises(ExportError):
        open_bundle(blob, "not the passphrase")


def test_garbage_file_is_rejected():
    with pytest.raises(ExportError):
        open_bundle(b"not json at all", PW)


def test_short_passphrase_is_rejected():
    with pytest.raises(ExportError):
        build_bundle({"keys": []}, "short")


def test_merge_is_additive_and_idempotent():
    current = [{"title": "A", "url": "u"}]
    incoming = clean_incoming("links", [{"title": "A", "url": "u"}, {"title": "B", "url": "u2"}])
    assert merge_into(current, incoming) == 1
    assert merge_into(current, incoming) == 0
    assert [x["title"] for x in current] == ["A", "B"]


def test_incoming_data_is_sanitised():
    cleaned = clean_incoming("keys", [
        {"label": "A", "full_key": "k", "masked": "x", "_decrypt_failed": True},
        {"label": "no secret"},
        "junk",
    ])
    assert cleaned == [{"label": "A", "full_key": "k"}]


def test_export_skips_undecryptable_and_strips_private_fields():
    out = clean_for_export("keys", [
        {"label": "ok", "full_key": "k", "masked": "m"},
        {"label": "locked", "full_key": "dpapi:xx", "_decrypt_failed": True},
    ])
    assert out == [{"label": "ok", "full_key": "k"}]
