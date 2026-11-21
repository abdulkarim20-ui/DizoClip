"""
Passphrase-protected export / import so data can move between PCs.

Format (.dizoclip): a JSON envelope {magic, version, kdf{...}, data}.
`data` is a Fernet token; the key comes from scrypt(passphrase, random salt).
"""
from __future__ import annotations

import base64
import json
import os
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

MAGIC = "dizoclip-export"
FORMAT_VERSION = 1
EXPORT_DATASETS = ("keys", "prompts", "ai_models", "links", "commands")
MIN_PASSPHRASE = 8
_N, _R, _P = 2**15, 8, 1


class ExportError(RuntimeError):
    pass


def _key(passphrase: str, salt: bytes, n: int, r: int, p: int) -> bytes:
    kdf = Scrypt(salt=salt, length=32, n=n, r=r, p=p)
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode("utf-8")))


def build_bundle(datasets: dict[str, Any], passphrase: str) -> bytes:
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
    try:
        env = json.loads(blob.decode("utf-8"))
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
        raise ExportError("Wrong passphrase, or the file is damaged.") from exc
    try:
        data = json.loads(plain.decode("utf-8"))
    except ValueError as exc:
        raise ExportError("The export content is damaged.") from exc
    if not isinstance(data, dict):
        raise ExportError("The export content is damaged.")
    return data


def _strip(item: dict) -> dict:
    return {k: v for k, v in item.items() if not k.startswith("_") and k != "masked"}


def clean_for_export(name: str, items: list) -> list:
    """Drop in-memory fields and records whose secret could not be decrypted."""
    return [
        _strip(i) for i in items
        if isinstance(i, dict) and not i.get("_decrypt_failed")
    ]


def clean_incoming(name: str, items: Any) -> list:
    """Sanitise imported records. Anything malformed is dropped, never repaired."""
    if not isinstance(items, list):
        return []
    out = []
    for item in items:
        if not isinstance(item, dict):
            continue
        item = _strip(item)
        if name == "keys" and not (isinstance(item.get("full_key"), str) and item["full_key"]):
            continue
        out.append(item)
    return out


def _canon(item: Any) -> str:
    return json.dumps(item, sort_keys=True, ensure_ascii=False)


def merge_into(current: list, incoming: list) -> int:
    """Append items not already present. Returns how many were added."""
    seen = {_canon(i) for i in current}
    added = 0
    for item in incoming:
        c = _canon(item)
        if c not in seen:
            current.append(item)
            seen.add(c)
            added += 1
    return added
