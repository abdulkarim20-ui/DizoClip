"""
Export dialog: tick exactly what to share, protect it with a passphrase.

There is one file type: encrypted (.dizoclip). It opens only in DizoClip.
Locked records (encrypted for another Windows account) are shown but cannot be ticked.
"""
from __future__ import annotations

import datetime

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QColor, QIcon
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

from app.components.inputs.check_style import GroupChecks, check_qss
from app.config.theme import (
    ACCENT,
    BG_INPUT,
    BG_MAIN,
    BORDER,
    DANGER,
    TEXT_DIM,
    TEXT_MAIN,
)
from app.core.export_import import (
    DATASET_LABELS,
    EXPORT_DATASETS,
    MIN_PASSPHRASE,
    ExportError,
    item_title,
)
from app.core.icons import load_icon, render_padded_pixmap
from app.core.window_utils import apply_dark_title_bar

TREE_QSS = f"""
QTreeWidget {{
    background: {BG_INPUT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 3px;
    outline: none;
    color: {TEXT_MAIN};
}}
QTreeWidget::item {{
    padding: 2px 2px;
    border-radius: 4px;
}}
QTreeWidget::item:hover {{
    background: #1a1e2b;
}}
QTreeWidget::item:selected {{
    background: transparent;
    color: {TEXT_MAIN};
}}
"""


class ExportDialog(QDialog):
    WIDTH, HEIGHT = 360, 405

    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.setWindowTitle("Export")
        self.setModal(True)
        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {BG_MAIN}; }}
            QLabel  {{ background: transparent; color: {TEXT_MAIN}; }}
            QLineEdit {{
                background: {BG_INPUT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 6px 10px;
                color: {TEXT_MAIN};
            }}
            QLineEdit:focus {{ border: 1px solid {ACCENT}; }}
            {TREE_QSS}
            {check_qss()}
        """)

        self._entries: list[tuple[str, dict]] = []  # index -> (dataset, record)
        self._busy = False

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(7)

        title = QLabel("Export")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #ffffff;")
        root.addWidget(title)

        sub = QLabel("Choose what to share. Only ticked items go into the file.")
        sub.setWordWrap(True)
        sub.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11.5px;")
        root.addWidget(sub)

        # selection header: count + All / None
        head = QHBoxLayout()
        head.setSpacing(4)
        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet(f"color: {ACCENT}; font-size: 11.5px; font-weight: 600;")
        head.addWidget(self.count_lbl)
        head.addStretch(1)

        for text, state in (("All", Qt.Checked), ("None", Qt.Unchecked)):
            b = QPushButton(text)
            b.setCursor(Qt.PointingHandCursor)
            b.setFlat(True)
            b.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {TEXT_DIM};
                    border: none;
                    padding: 2px 6px;
                    font-size: 11.5px;
                    font-weight: 600;
                }}
                QPushButton:hover {{ color: #ffffff; }}
            """)
            b.clicked.connect(lambda _=False, s=state: self._set_all(s))
            head.addWidget(b)
        root.addLayout(head)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(14)
        self.tree.setSelectionMode(QTreeWidget.NoSelection)
        self.tree.setFocusPolicy(Qt.NoFocus)
        self.tree.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tree.setFixedHeight(155)
        root.addWidget(self.tree)

        self.hint = QLabel(
            "• This password encrypts your file.<br/>"
            "• You’ll need it to unlock and import in DizoClip."
        )
        self.hint.setWordWrap(True)
        self.hint.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px;")
        root.addWidget(self.hint)

        self.pw1 = QLineEdit()
        self.pw1.setEchoMode(QLineEdit.Password)
        self.pw1.setPlaceholderText(f"Password ({MIN_PASSPHRASE}+ characters)")
        self.pw1.setFixedHeight(34)
        self.pw2 = self.pw1  # alias for backwards compatibility

        self._reveal_pw = False
        self.eye_action = QAction(self)
        self._update_eye_icon()
        self.eye_action.triggered.connect(self._toggle_pw_reveal)
        self.pw1.addAction(self.eye_action, QLineEdit.TrailingPosition)
        root.addWidget(self.pw1)

        self.pw_error = QLabel("")
        self.pw_error.setStyleSheet(f"color: {DANGER}; font-size: 11.5px;")
        root.addWidget(self.pw_error)

        row = QHBoxLayout()
        row.setSpacing(10)
        cancel = QPushButton("Cancel")
        cancel.setFixedHeight(34)
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.clicked.connect(self.reject)

        self.export_btn = QPushButton("Export")
        self.export_btn.setFixedHeight(34)
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.setDefault(True)
        self.export_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: #0b0d10;
                font-weight: 700;
                border-radius: 8px;
                border: none;
            }}
            QPushButton:hover {{ background: #d5693c; }}
            QPushButton:disabled {{ background: #3a2e2a; color: #7a6a62; }}
        """)
        self.export_btn.clicked.connect(self._on_export)
        pm_export = render_padded_pixmap("export", (14, 14), (17, 14), color="#0b0d10", pad_right=3)
        pm_export_dis = render_padded_pixmap("export", (14, 14), (17, 14), color="#7a6a62", pad_right=3)
        icon_export = QIcon()
        if pm_export:
            icon_export.addPixmap(pm_export, QIcon.Normal, QIcon.Off)
        if pm_export_dis:
            icon_export.addPixmap(pm_export_dis, QIcon.Disabled, QIcon.Off)
        if not icon_export.isNull():
            self.export_btn.setIcon(icon_export)
            self.export_btn.setIconSize(QSize(17, 14))
        row.addWidget(cancel)
        row.addWidget(self.export_btn)
        root.addLayout(row)

        self._fill_tree()
        self.groups = GroupChecks(self.tree)
        self.groups.sync_all()
        self.tree.itemChanged.connect(lambda *_: self._refresh())
        self.pw1.textChanged.connect(lambda *_: self._refresh())
        self._refresh()

    def _toggle_pw_reveal(self) -> None:
        self._reveal_pw = not self._reveal_pw
        self.pw1.setEchoMode(QLineEdit.Normal if self._reveal_pw else QLineEdit.Password)
        self._update_eye_icon()

    def _update_eye_icon(self) -> None:
        name = "eye_closed" if self._reveal_pw else "eye"
        ic = getattr(self.win, "icons", {}).get(name) if hasattr(self.win, "icons") else None
        if not ic:
            ic = load_icon("eye-closed" if self._reveal_pw else "eye", (16, 16), color=TEXT_DIM)
        if ic:
            self.eye_action.setIcon(ic)
        self.eye_action.setToolTip("Hide password" if self._reveal_pw else "Reveal password")

    def _fill_tree(self) -> None:
        self.tree.blockSignals(True)
        has_any_items = False
        for name in EXPORT_DATASETS:
            items = list(getattr(self.win, name))
            if not items:
                continue
            has_any_items = True
            label = DATASET_LABELS[name]
            top = QTreeWidgetItem(self.tree, [f"{label} · {len(items)}"])
            top.setData(0, Qt.UserRole, name)
            top.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            top.setCheckState(0, Qt.Checked)
            for rec in items:
                locked = isinstance(rec, dict) and bool(rec.get("_decrypt_failed"))
                text = item_title(name, rec) + (" · locked" if locked else "")
                child = QTreeWidgetItem(top, [text])
                if locked:
                    child.setFlags(Qt.ItemIsEnabled)
                    child.setForeground(0, QColor(TEXT_DIM))
                    child.setToolTip(0, "Encrypted for a different Windows account, so it can't be exported here.")
                else:
                    child.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
                    child.setCheckState(0, Qt.Checked)
                    child.setData(0, Qt.UserRole, len(self._entries))
                    self._entries.append((name, rec))
            top.setExpanded(False)

        if not has_any_items:
            empty_item = QTreeWidgetItem(self.tree, ["No items saved yet to export"])
            empty_item.setFlags(Qt.ItemIsEnabled)
            empty_item.setForeground(0, QColor(TEXT_DIM))

        self.tree.blockSignals(False)

    def _checked_indexes(self) -> list[int]:
        out = []
        for t in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(t)
            for c in range(top.childCount()):
                child = top.child(c)
                idx = child.data(0, Qt.UserRole)
                if idx is not None and child.checkState(0) == Qt.Checked:
                    out.append(int(idx))
        return out

    def selection(self) -> dict[str, list]:
        """{dataset: [records]} for everything ticked, in the order shown."""
        sel: dict[str, list] = {}
        for idx in self._checked_indexes():
            name, rec = self._entries[idx]
            sel.setdefault(name, []).append(rec)
        return sel

    def _set_all(self, state) -> None:
        self.groups.set_all(state)
        self._refresh()

    def _refresh(self) -> None:
        picked = self._checked_indexes()
        total = len(self._entries)
        self.count_lbl.setText(f"{len(picked)} of {total} selected")

        a = self.pw1.text()
        error = ""
        if a and len(a) < MIN_PASSPHRASE:
            error = f"Use at least {MIN_PASSPHRASE} characters."
        self.pw_error.setText(error)
        self.pw_error.setVisible(bool(error))

        ok = bool(picked) and len(a) >= MIN_PASSPHRASE
        self.export_btn.setEnabled(ok and not self._busy)

    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_title_bar(self, BG_MAIN, TEXT_MAIN)

    def _on_export(self) -> None:
        sel = self.selection()
        default = f"DizoClip-export-{datetime.date.today():%Y-%m-%d}.dizoclip"
        path, _ = QFileDialog.getSaveFileName(
            self, "Export DizoClip data", default, "DizoClip export (*.dizoclip)"
        )
        if not path:
            return

        self._busy = True
        self.export_btn.setEnabled(False)
        try:
            stats = self.win.export_selected(path, sel, passphrase=self.pw1.text())
        except (ExportError, OSError) as exc:
            self._busy = False
            self._refresh()
            QMessageBox.critical(self, "DizoClip", f"Export failed:\n\n{exc}")
            return

        msg = f"Exported {stats.total} item(s)."
        if stats.skipped_locked:
            msg += (f"\n\n{stats.skipped_locked} locked item(s) were skipped "
                    "(encrypted for a different Windows account).")
        msg += "\n\nKeep the file and the password safe."
        QMessageBox.information(self, "DizoClip", msg)
        self.accept()
