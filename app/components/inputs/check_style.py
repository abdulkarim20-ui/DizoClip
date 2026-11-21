"""
Checkbox look for dialogs, in DizoClip's colors.

The three indicator states are drawn once with QPainter and written to the
temp folder as small PNGs, because Qt style sheets can only theme a checkmark
through an image file.
"""
from __future__ import annotations

import os
import tempfile

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

from app.config.theme import ACCENT, BG_INPUT, TEXT_MAIN

_PATHS: dict[str, str] = {}


def _draw(state: str, px: int, path: str) -> None:
    scale = px / 16.0
    pm = QPixmap(px, px)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.scale(scale, scale)

    box = QRectF(1, 1, 14, 14)
    if state == "off":
        p.setPen(QPen(QColor("#3a4256"), 1.2))
        p.setBrush(QColor(BG_INPUT))
        p.drawRoundedRect(box, 4, 4)
    else:
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(ACCENT))
        p.drawRoundedRect(box, 4, 4)
        p.setPen(QPen(QColor("#0b0d10"), 1.9, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        if state == "on":
            p.drawPolyline([QPointF(4.4, 8.3), QPointF(6.9, 10.7), QPointF(11.7, 5.5)])
        else:  # partial
            p.drawLine(QPointF(4.8, 8.0), QPointF(11.2, 8.0))
    p.end()
    pm.save(path, "PNG")


def _icon_paths() -> dict[str, str]:
    if _PATHS:
        return _PATHS
    folder = os.path.join(tempfile.gettempdir(), f"dizoclip_ui_{ACCENT.lstrip('#')}")
    os.makedirs(folder, exist_ok=True)
    for state in ("off", "on", "part"):
        base = os.path.join(folder, f"check_{state}.png")
        if not os.path.exists(base):
            _draw(state, 16, base)
        retina = os.path.join(folder, f"check_{state}@2x.png")
        if not os.path.exists(retina):
            _draw(state, 32, retina)
        _PATHS[state] = base.replace("\\", "/")
    return _PATHS


def check_qss() -> str:
    """Style sheet fragment for QCheckBox and checkable QTreeView rows."""
    i = _icon_paths()
    return f"""
QCheckBox {{
    color: {TEXT_MAIN};
    spacing: 8px;
    background: transparent;
}}
QCheckBox::indicator, QTreeView::indicator {{
    width: 16px;
    height: 16px;
}}
QCheckBox::indicator:unchecked, QTreeView::indicator:unchecked {{
    image: url({i['off']});
}}
QCheckBox::indicator:checked, QTreeView::indicator:checked {{
    image: url({i['on']});
}}
QCheckBox::indicator:indeterminate, QTreeView::indicator:indeterminate {{
    image: url({i['part']});
}}
"""


class GroupChecks:
    """
    Category rows for a QTreeWidget: ticking a category ticks its tickable children,
    and the category shows a dash when only some are ticked.
    (Qt's built-in auto-tristate hides the category's box whenever a child cannot
    be ticked, e.g. a locked or already-matched row.)
    """
    def __init__(self, tree: QTreeWidget):
        self.tree = tree
        self._busy = False
        tree.itemChanged.connect(self._on_changed)

    @staticmethod
    def _tickable(item: QTreeWidgetItem) -> bool:
        return bool(item.flags() & Qt.ItemIsUserCheckable)

    def _kids(self, top: QTreeWidgetItem) -> list[QTreeWidgetItem]:
        return [top.child(i) for i in range(top.childCount()) if self._tickable(top.child(i))]

    def _sync(self, top: QTreeWidgetItem) -> None:
        kids = self._kids(top)
        if not kids or not self._tickable(top):
            return
        states = {k.checkState(0) for k in kids}
        if states == {Qt.Checked}:
            top.setCheckState(0, Qt.Checked)
        elif states == {Qt.Unchecked}:
            top.setCheckState(0, Qt.Unchecked)
        else:
            top.setCheckState(0, Qt.PartiallyChecked)

    def _on_changed(self, item: QTreeWidgetItem, column: int) -> None:
        if column != 0 or self._busy:
            return
        self._busy = True
        try:
            parent = item.parent()
            if parent is None:
                state = item.checkState(0)
                if state != Qt.PartiallyChecked:
                    for kid in self._kids(item):
                        kid.setCheckState(0, state)
            else:
                self._sync(parent)
        finally:
            self._busy = False

    def sync_all(self) -> None:
        self._busy = True
        try:
            for i in range(self.tree.topLevelItemCount()):
                self._sync(self.tree.topLevelItem(i))
        finally:
            self._busy = False

    def set_all(self, state) -> None:
        self._busy = True
        try:
            for i in range(self.tree.topLevelItemCount()):
                top = self.tree.topLevelItem(i)
                for kid in self._kids(top):
                    kid.setCheckState(0, state)
                self._sync(top)
        finally:
            self._busy = False
