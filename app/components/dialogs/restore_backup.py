"""Pick a dataset and a backup time, then restore it. The current file is backed up first."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app.config.theme import ACCENT, BG_INPUT, BG_MAIN, BORDER, CARD_BORDER, TEXT_DIM, TEXT_MAIN
from app.core.backup_manager import BackupError
from app.core.data_manager import DataError
from app.core.window_utils import apply_dark_title_bar

DATASET_LABELS = {
    "DC_Keys": "API Keys",
    "DC_Prompts": "Prompts",
    "DC_AI_Models": "AI Models",
    "DC_Links": "Links",
    "DC_Commands": "Commands",
    "DC_Settings": "Settings",
    "DC_Custom_Colors": "Custom colors",
}


class RestoreBackupDialog(QDialog):
    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.dm = win.data_manager
        self.setWindowTitle("Restore from Backup")
        self.setModal(True)
        self.setFixedSize(330, 380)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {BG_MAIN}; }}
            QLabel {{ background: transparent; color: {TEXT_MAIN}; }}
            QComboBox {{
                background: {BG_INPUT}; border: 1px solid {BORDER};
                border-radius: 8px; padding: 6px 10px; color: {TEXT_MAIN};
            }}
            QListWidget {{
                background: {BG_INPUT}; border: 1px solid {BORDER};
                border-radius: 8px; padding: 4px; outline: none; color: {TEXT_MAIN};
            }}
            QListWidget::item {{ padding: 7px 8px; border-radius: 6px; }}
            QListWidget::item:selected {{ background: #202433; color: #ffffff; }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(8)

        title = QLabel("Restore from Backup")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #ffffff;")
        root.addWidget(title)

        sub = QLabel("Choose a data file and the time to go back to. "
                     "Your current data is backed up first.")
        sub.setWordWrap(True)
        sub.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11.5px;")
        root.addWidget(sub)

        self.combo = QComboBox()
        self.combo.currentIndexChanged.connect(self._fill_list)
        root.addWidget(self.combo)

        self.list = QListWidget()
        root.addWidget(self.list, 1)

        self.empty_lbl = QLabel("No backups yet. They appear after you change something.")
        self.empty_lbl.setWordWrap(True)
        self.empty_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11.5px;")
        root.addWidget(self.empty_lbl)

        row = QHBoxLayout()
        row.setSpacing(10)
        cancel = QPushButton("Cancel")
        cancel.setFixedHeight(34)
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        self.restore_btn = QPushButton("Restore selected")
        self.restore_btn.setFixedHeight(34)
        self.restore_btn.setCursor(Qt.PointingHandCursor)
        self.restore_btn.setStyleSheet(f"""
            QPushButton {{ background: {ACCENT}; color: #0b0d10; font-weight: 700;
                           border-radius: 8px; border: none; }}
            QPushButton:disabled {{ background: #3a2e2a; color: #7a6a62; }}
        """)
        self.restore_btn.clicked.connect(self._on_restore)
        row.addWidget(cancel)
        row.addWidget(self.restore_btn)
        root.addLayout(row)

        for stem, label in DATASET_LABELS.items():
            if self.dm.backups.list_backups(stem):
                self.combo.addItem(label, stem)
        has_any = self.combo.count() > 0
        self.combo.setVisible(has_any)
        self.list.setVisible(has_any)
        self.empty_lbl.setVisible(not has_any)
        self.restore_btn.setEnabled(has_any)
        if has_any:
            self._fill_list()

    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_title_bar(self, BG_MAIN, TEXT_MAIN)

    def _fill_list(self):
        self.list.clear()
        stem = self.combo.currentData()
        if not stem:
            return
        for entry in self.dm.backups.list_backups(stem):
            item = QListWidgetItem(f"{entry.created:%d %b %Y, %H:%M:%S}   ·   {entry.size / 1024:.1f} KB")
            item.setData(Qt.UserRole, entry)
            self.list.addItem(item)
        if self.list.count():
            self.list.setCurrentRow(0)

    def _on_restore(self):
        item = self.list.currentItem()
        if item is None:
            return
        entry = item.data(Qt.UserRole)
        label = self.combo.currentText()
        when = f"{entry.created:%d %b %Y, %H:%M:%S}"
        answer = QMessageBox.question(
            self,
            "Restore backup",
            f"Replace your current {label} with the backup from {when}?\n\n"
            f"Your current {label} will be backed up first.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        try:
            self.dm.restore_backup(entry)
        except (BackupError, DataError) as exc:
            QMessageBox.critical(self, "DizoClip", f"Could not restore this backup:\n\n{exc}")
            return
        if not self.win.reload_data():
            return
        if entry.dataset == "DC_Settings":
            QMessageBox.information(self, "DizoClip", "Restart DizoClip to fully apply the restored settings.")
        self.accept()
