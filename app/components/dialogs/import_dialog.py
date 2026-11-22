"""
Import preview: shows what an export file holds BEFORE anything is added.

  New      not in DizoClip yet       ticked by default
  Matched  already here, identical   nothing to do
  Changed  same item, different      unticked; ticking adds it as a separate copy

Nothing is deleted or overwritten.
"""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

from app.components.dialogs.export_dialog import TREE_QSS
from app.components.inputs.check_style import GroupChecks, check_qss
from app.config.theme import ACCENT, BG_INPUT, BG_MAIN, BORDER, SUCCESS, TEXT_DIM, TEXT_MAIN
from app.core.export_import import CHANGED, DATASET_LABELS, EXPORT_DATASETS, NEW, SAME, ImportPlan
from app.core.icons import render_padded_pixmap
from app.core.window_utils import apply_dark_title_bar

_STATUS = {
    NEW: ("New", SUCCESS, "Not in DizoClip yet."),
    SAME: ("Matched", TEXT_DIM, "Already in DizoClip and identical. Nothing to do."),
    CHANGED: ("Changed", ACCENT,
              "The same item exists here, but its content is different.\n"
              "Tick it to add the file's version as a separate copy (your current one is kept)."),
}


class ImportDialog(QDialog):
    WIDTH, HEIGHT = 340, 500

    def __init__(self, win, plan: ImportPlan, source_name: str = ""):
        super().__init__(win)
        self.plan = plan
        self.setWindowTitle("Import")
        self.setModal(True)
        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {BG_MAIN}; }}
            QLabel  {{ background: transparent; color: {TEXT_MAIN}; }}
            {TREE_QSS}
            {check_qss()}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(8)

        title = QLabel("Import")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #ffffff;")
        root.addWidget(title)

        if source_name:
            src = QLabel(source_name)
            src.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11.5px;")
            src.setTextInteractionFlags(Qt.NoTextInteraction)
            root.addWidget(src)

        n_new, n_same, n_changed = plan.count(NEW), plan.count(SAME), plan.count(CHANGED)
        self.summary = QLabel(
            f'<span style="color:{SUCCESS}; font-weight:700;">{n_new} new</span>'
            f'&nbsp;&nbsp;·&nbsp;&nbsp;'
            f'<span style="color:{TEXT_DIM}; font-weight:700;">{n_same} matched</span>'
            f'&nbsp;&nbsp;·&nbsp;&nbsp;'
            f'<span style="color:{ACCENT}; font-weight:700;">{n_changed} changed</span>'
        )
        self.summary.setTextFormat(Qt.RichText)
        self.summary.setStyleSheet("font-size: 12px;")
        root.addWidget(self.summary)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(14)
        self.tree.setSelectionMode(QTreeWidget.NoSelection)
        self.tree.setFocusPolicy(Qt.NoFocus)
        self.tree.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        head = self.tree.header()
        head.setStretchLastSection(False)
        head.setSectionResizeMode(0, QHeaderView.Stretch)
        head.setSectionResizeMode(1, QHeaderView.Fixed)
        self.tree.setColumnWidth(1, 76)
        root.addWidget(self.tree, 1)

        self._fill_tree()

        notes = []
        if plan.invalid:
            notes.append(f"{plan.invalid} damaged item(s) were skipped.")
        if notes:
            note = QLabel(" ".join(notes))
            note.setWordWrap(True)
            note.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11.5px;")
            root.addWidget(note)

        foot = QLabel("Nothing is deleted or overwritten. Your data is backed up first.")
        foot.setWordWrap(True)
        foot.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11.5px;")
        root.addWidget(foot)

        row = QHBoxLayout()
        row.setSpacing(10)
        cancel = QPushButton("Cancel")
        cancel.setFixedHeight(34)
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.clicked.connect(self.reject)

        self.import_btn = QPushButton("Import")
        self.import_btn.setFixedHeight(34)
        self.import_btn.setCursor(Qt.PointingHandCursor)
        self.import_btn.setDefault(True)
        self.import_btn.setStyleSheet(f"""
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
        self.import_btn.clicked.connect(self.accept)
        pm_import = render_padded_pixmap("import", (14, 14), (17, 14), color="#0b0d10", pad_right=3)
        pm_import_dis = render_padded_pixmap("import", (14, 14), (17, 14), color="#7a6a62", pad_right=3)
        icon_import = QIcon()
        if pm_import:
            icon_import.addPixmap(pm_import, QIcon.Normal, QIcon.Off)
        if pm_import_dis:
            icon_import.addPixmap(pm_import_dis, QIcon.Disabled, QIcon.Off)
        if not icon_import.isNull():
            self.import_btn.setIcon(icon_import)
            self.import_btn.setIconSize(QSize(17, 14))
        row.addWidget(cancel)
        row.addWidget(self.import_btn)
        root.addLayout(row)

        self.groups = GroupChecks(self.tree)
        self.groups.sync_all()
        self.tree.itemChanged.connect(lambda *_: self._refresh())
        self._refresh()

    def _fill_tree(self) -> None:
        self.tree.blockSignals(True)
        grouped = self.plan.by_dataset()
        for name in EXPORT_DATASETS:
            rows = grouped.get(name)
            if not rows:
                continue
            actionable = any(inc.status != SAME for _, inc in rows)
            top = QTreeWidgetItem(self.tree, [f"{DATASET_LABELS[name]} · {len(rows)}", ""])
            if actionable:
                top.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
                top.setCheckState(0, Qt.Unchecked)
            else:
                top.setFlags(Qt.ItemIsEnabled)
                top.setForeground(0, QColor(TEXT_DIM))
            for idx, inc in rows:
                label, color, tip = _STATUS[inc.status]
                child = QTreeWidgetItem(top, [inc.title, label])
                child.setForeground(1, QColor(color))
                child.setTextAlignment(1, Qt.AlignRight | Qt.AlignVCenter)
                child.setToolTip(0, tip)
                child.setToolTip(1, tip)
                child.setData(0, Qt.UserRole, idx)
                if inc.status == SAME:
                    child.setFlags(Qt.ItemIsEnabled)
                    child.setForeground(0, QColor(TEXT_DIM))
                else:
                    child.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
                    child.setCheckState(0, Qt.Checked if inc.status == NEW else Qt.Unchecked)
            top.setExpanded(actionable)
        self.tree.blockSignals(False)

    def chosen_indexes(self) -> set[int]:
        out: set[int] = set()
        for t in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(t)
            for c in range(top.childCount()):
                child = top.child(c)
                idx = child.data(0, Qt.UserRole)
                if idx is not None and (child.flags() & Qt.ItemIsUserCheckable) \
                   and child.checkState(0) == Qt.Checked:
                    out.add(int(idx))
        return out

    def _refresh(self) -> None:
        n = len(self.chosen_indexes())
        self.import_btn.setText(f"Import {n} item{'s' if n != 1 else ''}" if n else "Import")
        self.import_btn.setEnabled(n > 0)

    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_title_bar(self, BG_MAIN, TEXT_MAIN)
