from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QAbstractButton,
    QComboBox,
    QFrame,
    QLineEdit,
    QPlainTextEdit,
    QSizePolicy,
    QTextEdit,
    QWidget,
)


class BaseCard(QFrame):
    """
    Base card container shared by every DizoClip item card.

    Provides:
    - unified hover lifecycle
    - responsive width
    - hold + drag signals for card reordering
    - automatic exclusion of interactive controls (copy, 3-dot, eye, dropdowns)
    """

    CARD_HEIGHT = 76

    drag_pressed = Signal(object, QPoint)
    drag_moved = Signal(object, QPoint)
    drag_released = Signal(object)

    def __init__(self, win, parent=None):
        super().__init__(parent)

        self.win = win
        self._hovered = False
        self._mouse_pressed = False

        self.setObjectName("Card")
        self.setFixedHeight(self.CARD_HEIGHT)
        self.setMinimumWidth(0)

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        self.setMouseTracking(True)

    # ------------------------------------------------------------------
    # Child Control Filtering
    # ------------------------------------------------------------------

    def _is_interactive_control(self, child: Optional[QWidget]) -> bool:
        """
        Return True if child or any of its ancestors up to self is an
        interactive control (buttons, text inputs, dropdown triggers, chips).
        """
        curr = child
        while curr is not None and curr is not self:
            if isinstance(curr, (QAbstractButton, QComboBox, QLineEdit, QTextEdit, QPlainTextEdit)):
                return True
            cls_name = curr.__class__.__name__
            if cls_name in ("LanguageDropdownTrigger", "ActionMenuPopup", "IconButton", "UrlLinkChip"):
                return True
            curr = curr.parentWidget()
        return False

    # ------------------------------------------------------------------
    # Drag events
    # ------------------------------------------------------------------

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint()
            child = self.childAt(pos)
            if not self._is_interactive_control(child):
                self._mouse_pressed = True
                self.drag_pressed.emit(
                    self,
                    pos,
                )

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._mouse_pressed:
            self.drag_moved.emit(
                self,
                event.position().toPoint(),
            )

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            was_pressed = self._mouse_pressed
            self._mouse_pressed = False
            if was_pressed:
                self.drag_released.emit(self)

        super().mouseReleaseEvent(event)

    # ------------------------------------------------------------------
    # Hover
    # ------------------------------------------------------------------

    def enterEvent(self, event):
        self._hovered = True
        self._refresh()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.rect().contains(
            self.mapFromGlobal(QCursor.pos())
        ):
            super().leaveEvent(event)
            return

        self._hovered = False
        self._refresh()

        super().leaveEvent(event)

    # ------------------------------------------------------------------
    # Extension point
    # ------------------------------------------------------------------

    def _refresh(self):
        """Override in subclasses to update hover-dependent UI."""
        pass
