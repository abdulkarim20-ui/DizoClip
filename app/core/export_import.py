"""
Export / import for DizoClip.
Pure Python: no Qt in here, so it is easy to test.

There is ONE file format: encrypted (.dizoclip)
  {magic, version, kdf{...}, data:<Fernet token>}
  `data` is a Fernet token; the key comes from scrypt(passphrase, salt).
  Files made by earlier versions of this format still open.

The decrypted `data` is a mapping:
  {"keys": [...], "prompts": [...], "ai_models": [...], "links": [...], "commands": [...]}
  (only the sections the user chose to share).

Plain JSON and .env files are deliberately NOT supported, in either direction: an export
would leave API keys on disk as readable text, and an import would trust a file nobody
protected.

Import never deletes or overwrites anything. Every incoming item is compared with
what is already stored and labelled NEW, SAME (already here) or CHANGED (same item,
different content).
"""
from __future__ import annotations

import base64
import copy
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

MAGIC = "dizoclip-export"
FORMAT_VERSION = 1
EXPORT_DATASETS = ("keys", "prompts", "ai_models", "links", "commands")
DATASET_LABELS = {
    "keys": "API Keys",
    "prompts": "Prompts",
    "ai_models": "AI Models",
    "links": "Links",
    "commands": "Commands",
}
MIN_PASSPHRASE = 8
MIN_PASSWORD = MIN_PASSPHRASE
MAX_IMPORT_BYTES = 25 * 1024 * 1024  # a real export is a few KB; this only stops accidents
_N, _R, _P = 2**15, 8, 1

NEW, SAME, CHANGED = "new", "same", "changed"

_TITLE_FIELDS = {
    "keys": ("label",),
    "prompts": ("name", "title"),
    "ai_models": ("name",),
    "links": ("title",),
    "commands": ("title",),
}
_ID_PREFIX = {"prompts": "prompt", "ai_models": "model", "links": "link", "commands": "cmd"}


class ExportError(RuntimeError):
    pass


class WrongPassphrase(ExportError):
    """Subclass of ExportError so existing `except ExportError` code keeps working."""


WrongPassword = WrongPassphrase


# ----------------------------------------------------------------------------- encryption
def _key(passphrase: str, salt: bytes, n: int, r: int, p: int) -> bytes:
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

    kdf = Scrypt(salt=salt, length=32, n=n, r=r, p=p)
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode("utf-8")))


def build_bundle(datasets: dict[str, Any], passphrase: str) -> bytes:
    from cryptography.fernet import Fernet

    if len(passphrase) < MIN_PASSPHRASE:
        raise ExportError(f"Use a password with at least {MIN_PASSPHRASE} characters.")
    salt = os.urandom(16)
    token = Fernet(_key(passphrase, salt, _N, _R, _P)).encrypt(
        json.dumps(datasets, ensure_ascii=False).encode("utf-8")
    )
    envelope = {
        "magic": MAGIC,
        "version": FORMAT_VERSION,
        "kdf": {"name": "scrypt", "n": _N, "r": _R, "p": _P,
                "salt": base64.b64encode(salt).decode("ascii")},
        "data": token.decode("ascii"),
    }
    return json.dumps(envelope, indent=2).encode("utf-8")


def open_bundle(blob: bytes, passphrase: str) -> dict[str, Any]:
    from cryptography.fernet import Fernet, InvalidToken

    try:
        env = json.loads(blob.decode("utf-8-sig"))
        if env.get("magic") != MAGIC or env.get("version") != FORMAT_VERSION:
            raise ExportError("This is not a DizoClip export file (or it is from a newer version).")
        kdf = env["kdf"]
        n, r, p = int(kdf["n"]), int(kdf["r"]), int(kdf["p"])
        if not (2**14 <= n <= 2**17 and 1 <= r <= 16 and 1 <= p <= 4):
            raise ExportError("Unsupported key-derivation settings.")
        salt = base64.b64decode(kdf["salt"])
        token = env["data"].encode("ascii")
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise ExportError("This file is not a valid DizoClip export.") from exc

    try:
        plain = Fernet(_key(passphrase, salt, n, r, p)).decrypt(token)
    except InvalidToken as exc:
        raise WrongPassphrase("Incorrect password, or the file is damaged.") from exc
    try:
        data = json.loads(plain.decode("utf-8"))
    except ValueError as exc:
        raise ExportError("The export content is damaged.") from exc
    if not isinstance(data, dict):
        raise ExportError("The export content is damaged.")
    return data


# ----------------------------------------------------------------------------- cleaning
def _strip(item: dict) -> dict:
    return {k: v for k, v in item.items() if not k.startswith("_") and k != "masked"}


def clean_for_export(name: str, items: list) -> list:
    """Drop in-memory fields and records whose secret could not be decrypted."""
    return [
        _strip(i) for i in items
        if isinstance(i, dict) and not i.get("_decrypt_failed")
    ]


def _is_str(v: Any) -> bool:
    return isinstance(v, str)


def _is_num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _valid(name: str, item: dict) -> bool:
    """Type-check one record. Malformed records are dropped, never 'repaired'."""
    if "id" in item and not (_is_str(item["id"]) and item["id"]):
        return False
    if "color" in item and not _is_str(item["color"]):
        return False
    for stamp in ("createdAt", "updatedAt"):
        if stamp in item and not _is_num(item[stamp]):
            return False

    if name == "keys":
        return _is_str(item.get("full_key")) and bool(item["full_key"]) \
            and _is_str(item.get("label", ""))
    if name == "prompts":
        has_title = _is_str(item.get("name")) or _is_str(item.get("title"))
        has_body = _is_str(item.get("prompt")) or _is_str(item.get("content"))
        return has_title and has_body
    if name == "ai_models":
        snippets = item.get("snippets", {})
        return (_is_str(item.get("name")) and isinstance(snippets, dict)
                and all(_is_str(k) and _is_str(v) for k, v in snippets.items()))
    if name == "links":
        return _is_str(item.get("title")) and _is_str(item.get("url"))
    if name == "commands":
        return _is_str(item.get("title")) and _is_str(item.get("command"))
    return False


def sanitize_incoming(name: str, items: Any) -> tuple[list, int]:
    """Return (valid records, number dropped)."""
    if items is None:
        return [], 0
    if not isinstance(items, list):
        return [], 1
    kept, dropped = [], 0
    for raw in items:
        if not isinstance(raw, dict):
            dropped += 1
            continue
        item = _strip(raw)
        if _valid(name, item):
            kept.append(item)
        else:
            dropped += 1
    return kept, dropped


def clean_incoming(name: str, items: Any) -> list:
    """Sanitise imported records. Anything malformed is dropped, never repaired."""
    return sanitize_incoming(name, items)[0]


def _canon(item: Any) -> str:
    return json.dumps(item, sort_keys=True, ensure_ascii=False)


def merge_into(current: list, incoming: list) -> int:
    """Append items not already present. Returns how many were added. (v1 helper, kept.)"""
    seen = {_canon(i) for i in current}
    added = 0
    for item in incoming:
        c = _canon(item)
        if c not in seen:
            current.append(item)
            seen.add(c)
            added += 1
    return added


# ----------------------------------------------------------------------------- titles
def item_title(name: str, item: Any) -> str:
    if isinstance(item, dict):
        for field_name in _TITLE_FIELDS.get(name, ()):
            value = item.get(field_name)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return "(untitled)"


# ----------------------------------------------------------------------------- export
@dataclass
class ExportStats:
    counts: dict[str, int] = field(default_factory=dict)
    skipped_locked: int = 0

    @property
    def total(self) -> int:
        return sum(self.counts.values())


def prepare_export(selection: dict[str, list]) -> tuple[dict, ExportStats]:
    """
    `selection` maps dataset name -> the records the user chose to share.
    Returns (payload, stats). Records locked to another Windows account are skipped and counted.
    """
    payload: dict[str, list] = {}
    stats = ExportStats()
    for name in EXPORT_DATASETS:
        items = selection.get(name)
        if not items:
            continue
        stats.skipped_locked += sum(
            1 for i in items if isinstance(i, dict) and i.get("_decrypt_failed")
        )
        cleaned = clean_for_export(name, items)
        if cleaned:
            payload[name] = cleaned
            stats.counts[name] = len(cleaned)
    return payload, stats


def write_bytes_atomic(path: str | Path, blob: bytes) -> None:
    """Write beside the target, fsync, then replace. A crash never leaves a half-written file."""
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    try:
        with open(tmp, "wb") as fh:
            fh.write(blob)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except OSError:
        tmp.unlink(missing_ok=True)
        raise


def export_to_file(
    path: str | Path,
    selection: dict[str, list],
    *,
    passphrase: str | None = None,
) -> ExportStats:
    """Write the chosen records to `path` as an encrypted .dizoclip file."""
    payload, stats = prepare_export(selection)
    if not payload:
        raise ExportError("Nothing selected to export.")
    blob = build_bundle(payload, passphrase or "")  # raises ExportError if too short
    write_bytes_atomic(path, blob)
    return stats


# ----------------------------------------------------------------------------- reading
def _parse_envelope(blob: bytes) -> dict:
    if len(blob) > MAX_IMPORT_BYTES:
        raise ExportError("This file is too large to be a DizoClip export.")
    try:
        env = json.loads(blob.decode("utf-8-sig"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise ExportError(
            "This file is not a valid DizoClip export. Only encrypted .dizoclip files can be imported."
        ) from exc
    if not isinstance(env, dict) or env.get("magic") != MAGIC:
        raise ExportError("This is not a DizoClip export file. Only encrypted .dizoclip files can be imported.")
    if env.get("version") != FORMAT_VERSION:
        raise ExportError("This export is from a newer version of DizoClip.")
    return env


def require_encrypted_bundle(blob: bytes) -> None:
    """Raise ExportError unless `blob` is an encrypted DizoClip export (.dizoclip)."""
    env = _parse_envelope(blob)  # not JSON / not ours / too new / too big -> ExportError
    if env.get("kind") == "plain" or "kdf" not in env or "data" not in env:
        raise ExportError(
            "Only encrypted DizoClip files (.dizoclip) can be imported. "
            "Plain JSON and .env files are not supported."
        )


def read_bundle(blob: bytes, passphrase: str | None = None) -> dict[str, Any]:
    """Return the {dataset: [records]} mapping from an encrypted .dizoclip file."""
    require_encrypted_bundle(blob)
    if not passphrase:
        raise WrongPassphrase("This file needs a password.")
    return open_bundle(blob, passphrase)


# ----------------------------------------------------------------------------- import planning
@dataclass
class IncomingItem:
    dataset: str
    item: dict
    status: str  # NEW | SAME | CHANGED
    title: str
    existing: dict | None = None  # the stored record a CHANGED item collides with


@dataclass
class ImportPlan:
    items: list[IncomingItem] = field(default_factory=list)
    invalid: int = 0             # malformed records that were dropped

    def count(self, status: str) -> int:
        return sum(1 for i in self.items if i.status == status)

    def by_dataset(self) -> dict[str, list[tuple[int, IncomingItem]]]:
        out: dict[str, list[tuple[int, IncomingItem]]] = {}
        for idx, inc in enumerate(self.items):
            out.setdefault(inc.dataset, []).append((idx, inc))
        return out


def _identity(name: str, item: dict) -> str:
    """What makes two records 'the same item'. Keys have no id, so the secret itself is the identity."""
    if name == "keys":
        return "s:" + item["full_key"]
    ident = item.get("id")
    if isinstance(ident, str) and ident:
        return "id:" + ident
    return "c:" + _canon(item)


def plan_import(current: dict[str, list], payload: dict[str, Any]) -> ImportPlan:
    """Compare an export with what is stored. Changes nothing."""
    plan = ImportPlan()
    for name in EXPORT_DATASETS:
        raw = payload.get(name)
        kept, dropped = sanitize_incoming(name, raw)
        plan.invalid += dropped

        index: dict[str, list[dict]] = {}
        for cur in current.get(name, []):
            if not isinstance(cur, dict) or cur.get("_decrypt_failed"):
                continue  # cannot be compared; never matched
            stored = _strip(cur)
            if not _valid(name, stored):
                continue
            index.setdefault(_identity(name, stored), []).append(stored)

        for item in kept:
            ident, canon = _identity(name, item), _canon(item)
            matches = index.get(ident)
            existing = None
            if not matches:
                status = NEW
                index[ident] = [item]  # a duplicate later in the same file will match this
            elif any(_canon(m) == canon for m in matches):
                status = SAME
            else:
                status, existing = CHANGED, matches[0]

            plan.items.append(IncomingItem(name, item, status, item_title(name, item), existing))

    return plan


def _as_copy(name: str, item: dict) -> dict:
    """A CHANGED item imported on request: a separate copy, so nothing existing is overwritten."""
    out = copy.deepcopy(item)
    if name in _ID_PREFIX:
        out["id"] = f"{_ID_PREFIX[name]}_{int(time.time() * 1000)}_{uuid.uuid4().hex[:5]}"
    for field_name in _TITLE_FIELDS[name]:
        if isinstance(out.get(field_name), str):
            out[field_name] = f"{out[field_name]} (imported)"
            break
    return out


def apply_plan(
    plan: ImportPlan,
    current: dict[str, list],
    chosen: Iterable[int] | None = None,
) -> tuple[dict[str, list], dict[str, int]]:
    """
    Build the new lists WITHOUT touching `current`. Returns (new_lists, added_per_dataset).
    chosen=None  -> import every NEW item (what the old one-click import did).
    chosen={...} -> import exactly those plan indexes (NEW as-is, CHANGED as a separate copy).
    """
    wanted = None if chosen is None else set(chosen)
    out = {name: list(current.get(name, [])) for name in EXPORT_DATASETS}
    added = {name: 0 for name in EXPORT_DATASETS}

    for idx, inc in enumerate(plan.items):
        if inc.status == SAME:
            continue
        if wanted is None:
            if inc.status != NEW:
                continue
        elif idx not in wanted:
            continue

        record = inc.item if inc.status == NEW else _as_copy(inc.dataset, inc.item)
        out[inc.dataset].append(copy.deepcopy(record))
        added[inc.dataset] += 1

    return out, added
