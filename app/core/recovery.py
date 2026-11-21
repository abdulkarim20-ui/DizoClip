"""
Startup recovery for unreadable data files.

Never deletes or overwrites anything without an explicit click.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from PySide6.QtWidgets import QMessageBox

from app.core.backup_manager import BackupError
from app.core.data_manager import DataError, DataManager

log = logging.getLogger(__name__)


def _ask(dm: DataManager, exc: DataError, can_restore: bool) -> str:
    """Return 'restore', 'retry' or 'quit'."""
    while True:
        box = QMessageBox()
        box.setIcon(QMessageBox.Critical)
        box.setWindowTitle("DizoClip: data problem")
        box.setText("DizoClip could not safely read one of your data files.")
        box.setInformativeText(
            f"{exc}\n\n"
            "Nothing has been deleted or overwritten.\n"
            + ("You can restore the most recent automatic backup of the affected file. "
               "The damaged file is kept in the 'Corrupt' folder."
               if can_restore else "No automatic backup is available for this file.")
        )
        restore = box.addButton("Restore latest backup", QMessageBox.AcceptRole) if can_restore else None
        retry = box.addButton("Retry", QMessageBox.ActionRole)
        folder = box.addButton("Open data folder", QMessageBox.ActionRole)
        quit_btn = box.addButton("Quit", QMessageBox.RejectRole)
        box.exec()

        clicked = box.clickedButton()
        if clicked is folder:
            try:
                dm.open_data_folder()
            except (DataError, OSError):
                log.warning("Could not open data folder", exc_info=True)
            continue  # show the dialog again
        if clicked is restore:
            return "restore"
        if clicked is retry:
            return "retry"
        if clicked is quit_btn:
            return "quit"
        return "quit"


def _restore_latest(dm: DataManager, dataset: str) -> bool:
    for entry in dm.backups_for(dataset):  # newest first
        try:
            dm.restore_backup(entry)
            log.info("Restored %s from backup %s", dataset, entry.path.name)
            return True
        except BackupError:
            log.warning("Skipping unusable backup %s", entry.path.name, exc_info=True)
    return False


def load_with_recovery(dm: DataManager) -> Optional[dict[str, Any]]:
    """Load all datasets. Returns None if the user chose to quit."""
    while True:
        try:
            return dm.load_all()
        except DataError as exc:
            log.error("Data load failed (%s): %s", exc.dataset, exc)
            can_restore = bool(exc.dataset and dm.backups_for(exc.dataset))
            action = _ask(dm, exc, can_restore)
            if action == "quit":
                return None
            if action == "restore" and not _restore_latest(dm, exc.dataset):
                QMessageBox.warning(
                    None, "DizoClip", "None of the backups for this file could be used."
                )
