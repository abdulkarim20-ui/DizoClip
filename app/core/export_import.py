"""
Export / import for DizoClip.
Pure Python: no Qt in here, so it is easy to test.

Two file formats share one envelope {magic, version, ...}:
  * Encrypted (.dizoclip)  {magic, version, kdf{...}, data:<Fernet token>}
    Unchanged from v1. `data` is a Fernet token; the key comes from scrypt(passphrase, salt).
  * Plain JSON (.json)     {magic, version, kind:"plain", meta{...}, data{...}}
    Readable and editable in VS Code. Nothing is encrypted.

Both carry the same `data` mapping:
  {"keys": [...], "prompts": [...], "ai_models": [...], "links": [...], "commands": [...]}
  (only the sections the user chose to share).

Import never deletes or overwrites anything. Every incoming item is compared with
what is already stored and labelled NEW, SAME (already here) or CHANGED (same item,
different content).
"""
from __future__ import annotations

import base64
import copy
import datetime
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

# Field order in plain JSON, so a record reads naturally top to bottom.
_FIELD_ORDER = (
    "id", "label", "name", "title", "url", "command", "prompt", "content",
    "full_key", "snippets", "color", "createdAt", "updatedAt"
)


class ExportError(RuntimeError):
    pass


class WrongPassphrase(ExportError):
    """Subclass of ExportError so existing `except ExportError` code keeps working."""


# ----------------------------------------------------------------------------- encryption
def _key(passphrase: str, salt: bytes, n: int, r: int, p: int) -> bytes:
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

    kdf = Scrypt(salt=salt, length=32, n=n, r=r, p=p)
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode("utf-8")))


def build_bundle(datasets: dict[str, Any], passphrase: str) -> bytes:
    from cryptography.fernet import Fernet

    if len(passphrase) < MIN_PASSPHRASE:
        raise ExportError(f"Use a passphrase with at least {MIN_PASSPHRASE} characters.")
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
        raise WrongPassphrase("Wrong passphrase, or the file is damaged.") from exc
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
    secrets_included: bool = True

    @property
    def total(self) -> int:
        return sum(self.counts.values())


def _ordered(item: dict) -> dict:
    first = {k: item[k] for k in _FIELD_ORDER if k in item}
    rest = {k: item[k] for k in sorted(item) if k not in first}
    return {**first, **rest}


def prepare_export(selection: dict[str, list], include_secrets: bool = True) -> tuple[dict, ExportStats]:
    """
    `selection` maps dataset name -> the records the user chose to share.
    Returns (payload, stats). Records locked to another Windows account are skipped and counted.
    """
    payload: dict[str, list] = {}
    stats = ExportStats(secrets_included=include_secrets)
    for name in EXPORT_DATASETS:
        items = selection.get(name)
        if not items:
            continue
        stats.skipped_locked += sum(
            1 for i in items if isinstance(i, dict) and i.get("_decrypt_failed")
        )
        cleaned = clean_for_export(name, items)
        if name == "keys" and not include_secrets:
            cleaned = [{k: v for k, v in i.items() if k != "full_key"} for i in cleaned]
        if cleaned:
            payload[name] = cleaned
            stats.counts[name] = len(cleaned)
    return payload, stats


def build_plain(payload: dict[str, list], stats: ExportStats, app_version: str = "") -> bytes:
    """Readable JSON for VS Code. Same section names as DizoClip uses internally."""
    secrets_in_file = stats.secrets_included and bool(payload.get("keys"))
    meta: dict[str, Any] = {
        "app": "DizoClip",
        "app_version": app_version,
        "exported_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "api_key_secrets_included": secrets_in_file,
        "sections": {
            name: {"label": DATASET_LABELS[name], "count": len(items)}
            for name, items in payload.items()
        },
    }
    if secrets_in_file:
        meta["warning"] = "This file contains API key secrets as readable text. Do not share or commit it."

    envelope = {
        "magic": MAGIC,
        "version": FORMAT_VERSION,
        "kind": "plain",
        "meta": meta,
        "data": {name: [_ordered(i) for i in items] for name, items in payload.items()},
    }
    return (json.dumps(envelope, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def build_env_text(keys: list[dict]) -> str:
    """Build clean KEY=VALUE environment file content without any metadata."""
    lines = [
        "# DizoClip API Keys Export",
        f"# Exported on {datetime.date.today().isoformat()}",
        "",
    ]
    for k in keys:
        if not isinstance(k, dict):
            continue
        label = str(k.get("label", "")).strip()
        secret = str(k.get("full_key", "")).strip()
        if not label and not secret:
            continue
        var_name = "".join(c if c.isalnum() or c == "_" else "_" for c in label).strip("_")
        var_name = var_name.upper() if var_name else "API_KEY"
        if " " in secret or "\n" in secret or "#" in secret or '"' in secret or "'" in secret:
            escaped = secret.replace('"', '\\"')
            lines.append(f'{var_name}="{escaped}"')
        else:
            lines.append(f"{var_name}={secret}")
    lines.append("")
    return "\n".join(lines)


def parse_env_text(text: str) -> list[dict]:
    """Parse .env / text file into DizoClip key records."""
    keys = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        var_name, val = line.split("=", 1)
        var_name = var_name.strip()
        val = val.strip()
        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            val = val[1:-1]
            val = val.replace('\\"', '"').replace("\\'", "'")
        if var_name and val:
            keys.append({
                "label": var_name,
                "full_key": val,
                "color": "#e8794a",
                "createdAt": int(time.time() * 1000),
            })
    return keys


def is_env_bundle(blob: bytes) -> bool:
    """True if blob appears to be an .env file rather than JSON or encrypted binary."""
    try:
        text = blob.decode("utf-8-sig").strip()
        if not text or text.startswith("{") or text.startswith("["):
            return False
        lines = [l.strip() for l in text.splitlines() if l.strip() and not l.strip().startswith("#")]
        if not lines:
            return False
        env_lines = sum(1 for l in lines if "=" in l and not l.startswith("="))
        return env_lines > 0 and env_lines >= len(lines) * 0.7
    except UnicodeDecodeError:
        return False


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
    plain: bool = False,
    env: bool = False,
    include_secrets: bool = True,
    app_version: str = "",
) -> ExportStats:
    payload, stats = prepare_export(selection, include_secrets)
    if not payload:
        raise ExportError("Nothing selected to export.")
    if env:
        keys = payload.get("keys", [])
        if not keys:
            raise ExportError("No API keys selected to export as an .env file.")
        blob = build_env_text(keys).encode("utf-8")
    elif plain:
        blob = build_plain(payload, stats, app_version)
    else:
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
        raise ExportError("This file is not a valid DizoClip export.") from exc
    if not isinstance(env, dict) or env.get("magic") != MAGIC:
        raise ExportError("This is not a DizoClip export file.")
    if env.get("version") != FORMAT_VERSION:
        raise ExportError("This export is from a newer version of DizoClip.")
    return env


def is_encrypted_bundle(blob: bytes) -> bool:
    """True if a passphrase is needed. Raises ExportError if the file is not a DizoClip export."""
    if is_env_bundle(blob):
        return False
    env = _parse_envelope(blob)
    if env.get("kind") == "plain":
        if not isinstance(env.get("data"), dict):
            raise ExportError("This file is not a valid DizoClip export.")
        return False
    if "kdf" not in env:
        raise ExportError("This file is not a valid DizoClip export.")
    return True


def read_bundle(blob: bytes, passphrase: str | None = None) -> dict[str, Any]:
    """Return the {dataset: [records]} mapping from either file format."""
    if is_env_bundle(blob):
        keys = parse_env_text(blob.decode("utf-8-sig"))
        return {"keys": keys}
    if is_encrypted_bundle(blob):
        if not passphrase:
            raise WrongPassphrase("This file needs a passphrase.")
        return open_bundle(blob, passphrase)
    return _parse_envelope(blob)["data"]


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
    keys_without_secret: int = 0 # keys from a "no secrets" export

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
        if name == "keys" and isinstance(raw, list):
            plan.keys_without_secret = sum(
                1 for r in raw
                if isinstance(r, dict) and not (_is_str(r.get("full_key")) and r.get("full_key"))
            )
        kept, dropped = sanitize_incoming(name, raw)
        plan.invalid += dropped
        if name == "keys":
            plan.invalid -= plan.keys_without_secret  # reported separately, not as "invalid"

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

    plan.invalid = max(plan.invalid, 0)
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
