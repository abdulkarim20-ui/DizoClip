"""
Central DizoClip data service.

Public in-memory shapes are unchanged:
    keys, prompts, ai_models, links, commands, settings, custom_colors

Safety rules:
- A corrupt JSON file is never turned into an empty dataset (DataError, with .dataset set).
- The current file is backed up (per dataset) before it is replaced.
- Writes are atomic (temp file + fsync + replace).
- Saves that change nothing are skipped (no rewrite, no backup).
- Legacy filenames are migrated without deleting the originals.
- API key `full_key` values are encrypted on disk with Windows DPAPI.
- The old plaintext `masked` fragment is removed from key records (one-time migration).
- Prompts, commands, and AI snippets can be protected on disk with Windows DPAPI (dzc1:).
"""
from __future__ import annotations

import copy
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any

from app.config.constants import (
    DEFAULT_SEED_AI_MODELS,
    DEFAULT_SEED_COMMANDS,
    DEFAULT_SEED_KEYS,
    DEFAULT_SEED_LINKS,
    DEFAULT_SEED_PROMPTS,
    DEFAULT_SETTINGS,
)
from app.core.backup_manager import BackupEntry, BackupError, BackupManager
from app.core.runtime import user_data_dir
from app.core.security import (
    SecretProtectionError,
    map_text,
    protect_key_record,
    unprotect_key_record,
    unprotect_text,
)

log = logging.getLogger(__name__)


class DataError(RuntimeError):
    """Data could not be read or written safely. `dataset` names the failing dataset."""

    def __init__(self, message: str, dataset: str | None = None):
        super().__init__(message)
        self.dataset = dataset


SCHEMA_VERSION = 2

DATASET_SPECS = {
    "keys": ("DC_Keys.json", "keys.json", DEFAULT_SEED_KEYS, list),
    "prompts": ("DC_Prompts.json", "prompts.json", DEFAULT_SEED_PROMPTS, list),
    "ai_models": ("DC_AI_Models.json", "ai_models.json", DEFAULT_SEED_AI_MODELS, list),
    "links": ("DC_Links.json", "links.json", DEFAULT_SEED_LINKS, list),
    "commands": ("DC_Commands.json", "commands.json", DEFAULT_SEED_COMMANDS, list),
    "settings": ("DC_Settings.json", "settings.json", DEFAULT_SETTINGS, dict),
    "custom_colors": ("DC_Custom_Colors.json", "custom_colors.json", [], list),
}
_STEM_TO_NAME = {Path(spec[0]).stem: name for name, spec in DATASET_SPECS.items()}

ENCRYPTED_FIELDS = {
    "prompts": ("prompt", "content"),
    "commands": ("command",),
    "ai_models": ("snippets",),
}


def _key_needs_migration(item: Any) -> bool:
    """True for key records that still carry `masked` or hold a plaintext secret."""
    if not isinstance(item, dict):
        return False
    if "masked" in item:
        return True
    secret = item.get("full_key")
    return isinstance(secret, str) and bool(secret) and not secret.startswith(("dpapi:", "plain:"))


class DataManager:
    def __init__(
        self,
        data_dir: Path | None = None,
        backup_count: int = 10,
        backup_min_interval: float = 30.0,
    ):
        self.data_dir = Path(data_dir or user_data_dir())
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.backups = BackupManager(
            self.data_dir, keep_recent=backup_count, min_interval=backup_min_interval
        )
        self._fingerprints: dict[str, str] = {}

    # ------------------------------------------------------------ helpers
    def path_for(self, name: str) -> Path:
        try:
            filename = DATASET_SPECS[name][0]
        except KeyError as exc:
            raise DataError(f"Unknown dataset: {name}") from exc
        return self.data_dir / filename

    def _legacy_path_for(self, name: str) -> Path:
        return self.data_dir / DATASET_SPECS[name][1]

    def _default_for(self, name: str):
        return copy.deepcopy(DATASET_SPECS[name][2])

    def _expected_type(self, name: str):
        return DATASET_SPECS[name][3]

    @staticmethod
    def _fingerprint(data: Any) -> str:
        blob = json.dumps(data, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def _read_json(self, path: Path) -> Any:
        try:
            with path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except json.JSONDecodeError as exc:
            raise DataError(f"Data file is corrupted or incomplete: {path.name}") from exc
        except OSError as exc:
            raise DataError(f"Could not read {path}: {exc}") from exc

    def _validate(self, name: str, data: Any) -> Any:
        expected = self._expected_type(name)
        if name == "custom_colors" and isinstance(data, dict):
            data = data.get("colors", [])
        if not isinstance(data, expected):
            raise DataError(
                f"Invalid data structure in {self.path_for(name).name}: "
                f"expected {expected.__name__}."
            )
        return data

    def _write_atomic(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        try:
            with tmp.open("w", encoding="utf-8", newline="\n") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
                fh.write("\n")
                fh.flush()
                os.fsync(fh.fileno())
            tmp.replace(path)
        except OSError as exc:
            tmp.unlink(missing_ok=True)
            raise DataError(f"Could not save {path.name}: {exc}") from exc

    def _migrate_legacy(self, name: str) -> Any | None:
        target = self.path_for(name)
        legacy = self._legacy_path_for(name)
        if target.exists() or not legacy.exists():
            return None

        data = self._validate(name, self._read_json(legacy))
        # Copy, do not delete the legacy file. This is intentionally non-destructive.
        self._write_atomic(target, data)
        return data

    def _unprotect_records(self, name: str, items: list) -> list:
        fields = ENCRYPTED_FIELDS[name]
        out = []
        for rec in items:
            if not isinstance(rec, dict):
                out.append(rec)
                continue
            rec = dict(rec)
            for field in fields:
                if field in rec:
                    try:
                        rec[field] = map_text(rec[field], unprotect_text)
                    except SecretProtectionError:
                        rec["_decrypt_failed"] = True  # keep the encrypted values as they are
            out.append(rec)
        return out

    # ------------------------------------------------------------ loading
    def _load(self, name: str) -> Any:
        try:
            return self._load_inner(name)
        except DataError as exc:
            if exc.dataset is None:
                exc.dataset = name
            raise

    def _load_inner(self, name: str) -> Any:
        target = self.path_for(name)
        migrated = self._migrate_legacy(name)
        if migrated is not None:
            data = migrated
        elif target.exists():
            data = self._validate(name, self._read_json(target))
        else:
            data = self._default_for(name)
            self._write_atomic(target, data)

        if name == "settings":
            data = self._normalize_settings(data)
        elif name in ENCRYPTED_FIELDS:
            had_encrypted = any(
                isinstance(rec, dict) and any(
                    isinstance(rec.get(f), str) and rec[f].startswith("dzc1:")
                    or (isinstance(rec.get(f), dict) and any(isinstance(v, str) and v.startswith("dzc1:") for v in rec[f].values()))
                    for f in ENCRYPTED_FIELDS[name]
                )
                for rec in data if isinstance(rec, dict)
            )
            data = self._unprotect_records(name, data)
            if had_encrypted:
                try:
                    self.save(name, data, force=True)
                    log.info("Migrated %s to plaintext JSON", target.name)
                except DataError:
                    log.warning("Could not migrate %s to plaintext", target.name, exc_info=True)
        elif name == "keys":
            needs_migration = any(_key_needs_migration(i) for i in data)
            data = [unprotect_key_record(i) if isinstance(i, dict) else i for i in data]
            if needs_migration:
                self._migrate_keys_file(data)

        self._fingerprints[name] = self._fingerprint(data)
        return data

    def _migrate_keys_file(self, data: list) -> None:
        """One-time upgrade: drop plaintext `masked` fragments and encrypt legacy plaintext keys."""
        try:
            self.save("keys", data, force=True)  # snapshots the old file, writes the clean one
            self._scrub_key_backups()            # old snapshots still hold the same fragments
            log.info("Migrated DC_Keys.json: removed masked fragments, secrets protected")
        except DataError:
            log.warning("Key migration failed; it will be retried on next launch", exc_info=True)

    def _scrub_key_backups(self) -> None:
        folder = self.backups.backup_dir / self.path_for("keys").stem
        for snap in folder.glob("*.json"):
            try:
                raw = json.loads(snap.read_text(encoding="utf-8"))
                if not isinstance(raw, list):
                    continue
                cleaned = [protect_key_record(i) if isinstance(i, dict) else i for i in raw]
                if cleaned != raw:
                    self._write_atomic(snap, cleaned)
            except Exception:
                log.warning("Could not scrub backup %s", snap.name, exc_info=True)

    def _normalize_settings(self, data: dict) -> dict:
        cfg = copy.deepcopy(DEFAULT_SETTINGS)
        cfg.update(data)

        # Preserve existing DizoClip section migration behavior.
        order = ["ai_model" if x == "sparkles-2" else x for x in cfg.get("section_order", [])]
        if "ai_model" not in order:
            if "prompt" in order:
                order.insert(order.index("prompt") + 1, "ai_model")
            else:
                order.append("ai_model")
        cfg["section_order"] = order

        enabled = ["ai_model" if x == "sparkles-2" else x for x in cfg.get("enabled_sections", [])]
        if "ai_model" not in enabled:
            enabled.append("ai_model")
        cfg["enabled_sections"] = enabled

        if cfg.get("startup_module") == "sparkles-2":
            cfg["startup_module"] = "ai_model"

        cfg.setdefault("schema_version", SCHEMA_VERSION)
        cfg.setdefault("welcome_seen", False)
        cfg.setdefault("backup_on_save", True)
        cfg.setdefault("auto_clear_clipboard", True)
        cfg["schema_version"] = SCHEMA_VERSION
        return cfg

    def load_all(self) -> dict[str, Any]:
        return {name: self._load(name) for name in DATASET_SPECS}

    # ------------------------------------------------------------- saving
    def save(self, name: str, data: Any, *, force: bool = False) -> None:
        """
        Save one dataset.
        force=True skips the "nothing changed" shortcut and always takes a backup.
        """
        self._validate(name, data)
        fingerprint = self._fingerprint(data)
        path = self.path_for(name)

        if not force and path.exists() and self._fingerprints.get(name) == fingerprint:
            return  # nothing changed: no rewrite, no backup

        if path.exists():
            try:
                self.backups.snapshot_file(path, force=force)
            except BackupError as exc:
                raise DataError(
                    f"Backup failed; {path.name} was not changed. ({exc})", dataset=name
                ) from exc

        payload = copy.deepcopy(data)

        if name == "keys":
            payload = [
                protect_key_record(item) if isinstance(item, dict) else item
                for item in payload
            ]
        elif name == "settings":
            payload = self._normalize_settings(payload)
        elif name in ENCRYPTED_FIELDS:
            # Prompts, commands, ai_models: saved as clean plain JSON on disk.
            # In-memory-only fields (e.g. _decrypt_failed) are never written to disk.
            payload = [
                {k: v for k, v in rec.items() if not k.startswith("_")} if isinstance(rec, dict) else rec
                for rec in payload
            ]

        self._write_atomic(path, payload)
        self._fingerprints[name] = fingerprint

    def save_all(self, datasets: dict[str, Any], force: bool = False) -> None:
        # Validate everything before touching disk.
        for name, data in datasets.items():
            if name in DATASET_SPECS:
                self._validate(name, data)

        for name, data in datasets.items():
            if name in DATASET_SPECS:
                self.save(name, data, force=force)

    # ------------------------------------------------------------ backups
    def backups_for(self, name: str) -> list[BackupEntry]:
        """Backups for one dataset name ('keys', 'links', ...), newest first."""
        return self.backups.list_backups(self.path_for(name).stem)

    def create_backup(self) -> list[Path]:
        """Snapshot every data file right now (ignores the debounce)."""
        made = []
        for name in DATASET_SPECS:
            path = self.path_for(name)
            if path.exists():
                snap = self.backups.snapshot_file(path, force=True)
                if snap:
                    made.append(snap)
        return made

    def restore_backup(self, entry: BackupEntry) -> Path:
        """Restore one backup. Validates its shape first; backs up (or quarantines) the current file."""
        name = _STEM_TO_NAME.get(entry.dataset)
        if name is None:
            raise BackupError(f"Unknown dataset: {entry.dataset}")
        target = self.backups.restore(entry, validate=lambda raw: self._validate(name, raw))
        self._fingerprints.clear()
        return target

    def open_data_folder(self) -> None:
        if os.name != "nt":
            raise DataError("Open data folder is currently implemented for Windows.")
        os.startfile(str(self.data_dir))  # type: ignore[attr-defined]
