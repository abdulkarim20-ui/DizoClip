"""
Central DizoClip data service.

This is the integration point for all existing MainWindow save/load calls.
It preserves the existing public in-memory shapes:
    keys, prompts, ai_models, links, commands, settings, custom_colors

Important safety behavior:
- Never converts a corrupt JSON file into an empty dataset.
- Creates a backup before replacing an existing dataset.
- Writes atomically.
- Migrates legacy filenames.
- Adds schema metadata to settings without changing existing module data shapes.
- Encrypts API key ``full_key`` values on disk on Windows via DPAPI.
"""
from __future__ import annotations

import copy
import json
import os
import shutil
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
from app.core.backup_manager import BackupManager
from app.core.runtime import user_data_dir
from app.core.security import protect_key_record, unprotect_key_record


class DataError(RuntimeError):
    pass


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


class DataManager:
    def __init__(self, data_dir: Path | None = None, backup_count: int = 5):
        self.data_dir = Path(data_dir or user_data_dir())
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.backups = BackupManager(self.data_dir, max_backups=backup_count)

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

    def _read_json(self, path: Path) -> Any:
        try:
            with path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except json.JSONDecodeError as exc:
            raise DataError(
                f"Data file is corrupted or incomplete: {path.name}"
            ) from exc
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
        # Copy, do not delete legacy. This is intentionally non-destructive.
        self._write_atomic(target, data)
        return data

    def _load(self, name: str) -> Any:
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
        elif name == "keys":
            data = [unprotect_key_record(item) if isinstance(item, dict) else item for item in data]

        return data

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
        cfg["schema_version"] = SCHEMA_VERSION
        return cfg

    def load_all(self) -> dict[str, Any]:
        return {name: self._load(name) for name in DATASET_SPECS}

    def save(self, name: str, data: Any) -> None:
        self._validate(name, data)

        path = self.path_for(name)

        # Backup the exact current dataset before replacing it.
        if path.exists():
            try:
                self.backups.create_snapshot([path])
            except Exception as exc:
                # Saving must not silently proceed when backup is requested.
                # The caller can surface the error and retry.
                raise DataError(f"Backup failed; {name} was not changed.") from exc

        payload = copy.deepcopy(data)

        if name == "keys":
            payload = [
                protect_key_record(item) if isinstance(item, dict) else item
                for item in payload
            ]

        if name == "settings":
            payload = self._normalize_settings(payload)

        self._write_atomic(path, payload)

    def save_all(self, datasets: dict[str, Any]) -> None:
        # Validate everything before touching disk.
        for name, data in datasets.items():
            if name in DATASET_SPECS:
                self._validate(name, data)

        for name, data in datasets.items():
            if name in DATASET_SPECS:
                self.save(name, data)

    def open_data_folder(self) -> None:
        if os.name != "nt":
            raise DataError("Open data folder is currently implemented for Windows.")
        os.startfile(str(self.data_dir))  # type: ignore[attr-defined]

    def create_backup(self) -> Path:
        return self.backups.create_snapshot()

    def latest_backup(self) -> Path | None:
        snapshots = self.backups.list_snapshots()
        return snapshots[0] if snapshots else None
