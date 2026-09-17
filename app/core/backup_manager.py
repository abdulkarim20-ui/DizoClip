"""
Small, deterministic backup manager for DizoClip user data.

Backups are local only. A rolling set of snapshots is retained.
"""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path


class BackupError(RuntimeError):
    pass


class BackupManager:
    def __init__(self, data_dir: Path, max_backups: int = 5):
        self.data_dir = Path(data_dir)
        self.backup_dir = self.data_dir / "Backups"
        self.max_backups = max(1, int(max_backups))
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_snapshot(self, files: list[Path] | None = None) -> Path:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        target = self.backup_dir / timestamp
        counter = 1
        while target.exists():
            target = self.backup_dir / f"{timestamp}_{counter}"
            counter += 1
        target.mkdir(parents=True, exist_ok=True)

        source_files = files or [
            p for p in self.data_dir.iterdir()
            if p.is_file() and p.suffix.lower() == ".json"
        ]

        try:
            for src in source_files:
                if src.exists() and src.is_file():
                    shutil.copy2(src, target / src.name)
        except OSError as exc:
            shutil.rmtree(target, ignore_errors=True)
            raise BackupError(f"Could not create backup: {exc}") from exc

        self.prune()
        return target

    def list_snapshots(self) -> list[Path]:
        return sorted(
            [p for p in self.backup_dir.iterdir() if p.is_dir()],
            key=lambda p: p.name,
            reverse=True,
        )

    def prune(self) -> None:
        snapshots = self.list_snapshots()
        for old in snapshots[self.max_backups:]:
            shutil.rmtree(old, ignore_errors=True)

    def restore_snapshot(self, snapshot: Path) -> list[Path]:
        snapshot = Path(snapshot)
        if not snapshot.is_dir() or snapshot.parent.resolve() != self.backup_dir.resolve():
            raise BackupError("Invalid backup snapshot.")

        restored: list[Path] = []
        for src in snapshot.glob("*.json"):
            target = self.data_dir / src.name
            tmp = target.with_suffix(target.suffix + ".restore.tmp")
            try:
                shutil.copy2(src, tmp)
                tmp.replace(target)
                restored.append(target)
            except OSError as exc:
                tmp.unlink(missing_ok=True)
                raise BackupError(f"Could not restore {src.name}: {exc}") from exc
        return restored
