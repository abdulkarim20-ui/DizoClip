"""
Windows DPAPI protection for DizoClip API keys.

No third-party crypto dependency is required on Windows.
If DPAPI is unavailable (for example, non-Windows development), the
manager can still operate, but callers should treat stored secrets as
plain JSON and should not advertise them as encrypted.
"""
from __future__ import annotations

import base64
import ctypes
import json
import os
import platform
from ctypes import wintypes


class SecretProtectionError(RuntimeError):
    pass


if platform.system() == "Windows":
    class _DATA_BLOB(ctypes.Structure):
        _fields_ = [
            ("cbData", wintypes.DWORD),
            ("pbData", ctypes.POINTER(ctypes.c_ubyte)),
        ]

    _crypt32 = ctypes.windll.crypt32
    _kernel32 = ctypes.windll.kernel32

    _crypt32.CryptProtectData.argtypes = [
        ctypes.POINTER(_DATA_BLOB),
        wintypes.LPCWSTR,
        ctypes.POINTER(_DATA_BLOB),
        wintypes.LPVOID,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(_DATA_BLOB),
    ]
    _crypt32.CryptProtectData.restype = wintypes.BOOL

    _crypt32.CryptUnprotectData.argtypes = [
        ctypes.POINTER(_DATA_BLOB),
        ctypes.POINTER(wintypes.LPWSTR),
        ctypes.POINTER(_DATA_BLOB),
        wintypes.LPVOID,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(_DATA_BLOB),
    ]
    _crypt32.CryptUnprotectData.restype = wintypes.BOOL

    _kernel32.LocalFree.argtypes = [wintypes.HLOCAL]
    _kernel32.LocalFree.restype = wintypes.HLOCAL


def dpapi_available() -> bool:
    return platform.system() == "Windows"


def _blob_from_bytes(data: bytes):
    buf = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
    blob = _DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte)))
    return blob, buf


def _protect_windows(value: str) -> str:
    raw = value.encode("utf-8")
    in_blob, _ = _blob_from_bytes(raw)
    out_blob = _DATA_BLOB()

    if not _crypt32.CryptProtectData(
        ctypes.byref(in_blob), "DizoClip API Key", None, None, None, 0,
        ctypes.byref(out_blob)
    ):
        raise SecretProtectionError("Windows DPAPI encryption failed.")

    try:
        encrypted = ctypes.string_at(out_blob.pbData, out_blob.cbData)
        return "dpapi:" + base64.b64encode(encrypted).decode("ascii")
    finally:
        _kernel32.LocalFree(out_blob.pbData)


def _unprotect_windows(value: str) -> str:
    try:
        encrypted = base64.b64decode(value.removeprefix("dpapi:"), validate=True)
    except Exception as exc:
        raise SecretProtectionError("Invalid DPAPI value.") from exc

    in_blob, _ = _blob_from_bytes(encrypted)
    out_blob = _DATA_BLOB()
    description = wintypes.LPWSTR()

    if not _crypt32.CryptUnprotectData(
        ctypes.byref(in_blob), ctypes.byref(description), None, None, None, 0,
        ctypes.byref(out_blob)
    ):
        raise SecretProtectionError(
            "Windows DPAPI could not decrypt this key under the current Windows account."
        )

    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData).decode("utf-8")
    finally:
        _kernel32.LocalFree(out_blob.pbData)
        if description:
            _kernel32.LocalFree(description)


def protect_secret(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("Secret must be a string.")
    if dpapi_available():
        return _protect_windows(value)
    # Explicit fallback marker: never pretend this is encryption.
    return "plain:" + value


def unprotect_secret(value: str) -> str:
    if not isinstance(value, str):
        return str(value)
    if value.startswith("dpapi:"):
        if not dpapi_available():
            raise SecretProtectionError("DPAPI secret can only be opened on Windows.")
        return _unprotect_windows(value)
    if value.startswith("plain:"):
        return value[6:]
    # Backward compatibility with existing DizoClip JSON.
    return value


def protect_key_record(record: dict) -> dict:
    out = dict(record)
    if "full_key" in out and isinstance(out["full_key"], str):
        value = out["full_key"]
        if not value.startswith(("dpapi:", "plain:")):
            out["full_key"] = protect_secret(value)
    return out


def unprotect_key_record(record: dict) -> dict:
    out = dict(record)
    if "full_key" in out and isinstance(out["full_key"], str):
        out["full_key"] = unprotect_secret(out["full_key"])
    return out
