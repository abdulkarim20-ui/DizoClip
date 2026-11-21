"""
Per-dataset rolling backups for DizoClip user data (local only).

Layout:  User_Data/Backups/<DatasetStem>/<YYYYmmdd-HHMMSS-ffffff>.json

Retention is per dataset, so saving Settings can never push API-key backups out.
Policy: keep the newest `keep_recent` snapshots, plus the newest snapshot of each
of the last `keep_daily` calendar days.
A snapshot is skipped when the previous one is younger than `min_interval` seconds
(bursts such as drag-reordering) or is byte-identical to the file being backed up.
"""
from __future__ import annotations

import json
import logging
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

log = logging.getLogger(__name__)

_STAMP_FMT = "%Y%m%d-%H%M%S-%f"
_LEGACY_DIR = re.compile(r"^\d{8}-\d{6}-\d{6}(_\d+)?$")


class BackupError(RuntimeError):
    pass


@dataclass(frozen=True)
class BackupEntry:
    dataset: str   # file stem, e.g. "DC_Keys"
    path: Path
    created: datetime
    size: int


def _is_valid_json(path: Path) -> bool:
    try:
        json.loads(path.read_text(encoding="utf-8"))
        return True
    except (OSError, ValueError):
        return False


class BackupManager:
    def __init__(
        self,
        data_dir: Path,
        keep_recent: int = 10,
        keep_daily: int = 14,
        min_interval: float = 30.0,
    ):
        self.data_dir = Path(data_dir)
        self.backup_dir = self.data_dir / "Backups"
        self.keep_recent = max(1, int(keep_recent))
        self.keep_daily = max(0, int(keep_daily))
        self.min_interval = max(0.0, float(min_interval))
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._migrate_legacy_layout()

    # ------------------------------------------------------------ listing
    def _entries_for(self, dataset: str) -> list[BackupEntry]:
        folder = self.backup_dir / dataset
        if not folder.is_dir():
            return []
        entries: list[BackupEntry] = []
        for path in folder.glob("*.json"):
            try:
                created = datetime.strptime(path.stem.split("_")[0], _STAMP_FMT)
                entries.append(BackupEntry(dataset, path, created, path.stat().st_size))
            except (ValueError, OSError):
                continue
        entries.sort(key=lambda e: (e.created, e.path.name), reverse=True)
        return entries

    def list_backups(self, dataset: Optional[str] = None) -> list[BackupEntry]:
        """Newest first. `dataset` is a file stem such as 'DC_Keys' (None = all)."""
        if dataset:
            return self._entries_for(dataset)
        found: list[BackupEntry] = []
        for folder in self.backup_dir.iterdir():
            if folder.is_dir():
                found.extend(self._entries_for(folder.name))
        found.sort(key=lambda e: (e.created, e.path.name), reverse=True)
        return found

    # ----------------------------------------------------------- snapshot
    def snapshot_file(self, source: Path, force: bool = False) -> Optional[Path]:
        """Copy `source` into its dataset folder. Returns None when skipped."""
        source = Path(source)
        if not source.is_file():
            return None

        dataset = source.stem
        existing = self._entries_for(dataset)
        if existing and not force:
            newest = existing[0]
            age = (datetime.now() - newest.created).total_seconds()
            if self.min_interval and age < self.min_interval:
                return None
            try:
                if newest.path.read_bytes() == source.read_bytes():
                    return None
            except OSError:
                pass

        folder = self.backup_dir / dataset
        stamp = datetime.now().strftime(_STAMP_FMT)
        target = folder / f"{stamp}.json"
        n = 1
        while target.exists():
            target = folder / f"{stamp}_{n}.json"
            n += 1

        tmp = target.with_suffix(".json.tmp")
        try:
            folder.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, tmp)
            tmp.replace(target)
        except OSError as exc:
            tmp.unlink(missing_ok=True)
            raise BackupError(f"Could not back up {source.name}: {exc}") from exc

        self._prune(dataset)
        return target

    def _prune(self, dataset: str) -> None:
        entries = self._entries_for(dataset)  # newest first
        keep = {e.path for e in entries[: self.keep_recent]}
        days: set = set()
        for e in entries:  # newest snapshot of each recent day
            day = e.created.date()
            if day not in days and len(days) < self.keep_daily:
                days.add(day)
                keep.add(e.path)
        for e in entries:
            if e.path not in keep:
                try:
                    e.path.unlink()
                except OSError:
                    log.warning("Could not remove old backup %s", e.path.name)

    # ------------------------------------------------------------ restore
    def restore(
        self,
        entry: BackupEntry,
        validate: Optional[Callable[[Any], Any]] = None,
    ) -> Path:
        """
        Put `entry` back as the live data file.
        The current file is snapshotted first (or set aside in Corrupt/ if it is damaged).
        """
        src = entry.path
        if src.parent.parent.resolve() != self.backup_dir.resolve() or not src.is_file():
            raise BackupError("Invalid backup entry.")
        try:
            raw = json.loads(src.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise BackupError(f"This backup is damaged: {exc}") from exc
        if validate is not None:
            try:
                validate(raw)
            except Exception as exc:
                raise BackupError(f"This backup has an unexpected format: {exc}") from exc

        target = self.data_dir / f"{entry.dataset}.json"
        tmp = target.with_suffix(".json.restore.tmp")
        try:
            # Copy first: snapshotting the current file below may prune `entry`.
            shutil.copyfile(src, tmp)
            if target.exists():
                if _is_valid_json(target):
                    self.snapshot_file(target, force=True)
                else:
                    self._quarantine(target)
            tmp.replace(target)
        except (OSError, BackupError) as exc:
            tmp.unlink(missing_ok=True)
            raise BackupError(f"Could not restore {target.name}: {exc}") from exc
        return target

    def _quarantine(self, target: Path) -> None:
        folder = self.data_dir / "Corrupt"
        folder.mkdir(parents=True, exist_ok=True)
        dest = folder / f"{target.stem}-{datetime.now().strftime(_STAMP_FMT)}.json"
        shutil.move(str(target), str(dest))

    # ------------------------------------------------------ legacy layout
    def _migrate_legacy_layout(self) -> None:
        """Move old Backups/<stamp>/DC_*.json snapshots into Backups/<Dataset>/<stamp>.json."""
        try:
            children = list(self.backup_dir.iterdir())
        except OSError:
            return
        for legacy in children:
            if not (legacy.is_dir() and _LEGACY_DIR.match(legacy.name)):
                continue
            try:
                for src in legacy.glob("*.json"):
                    dest_dir = self.backup_dir / src.stem
                    dest_dir.mkdir(exist_ok=True)
                    dest = dest_dir / f"{legacy.name}.json"
                    if not dest.exists():
                        shutil.move(str(src), str(dest))
                legacy.rmdir()  # only succeeds when empty, so nothing is ever deleted
            except OSError:
                log.warning("Could not fully migrate legacy backup folder %s", legacy.name)
