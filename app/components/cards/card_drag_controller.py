from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import QObject, QPoint, QTimer, Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QLayout, QScrollArea, QWidget


class CardDragController(QObject):
    """
    Reusable vertical card reorder controller.

    Responsibilities:
    - starts a drag after a short hold (HOLD_DELAY_MS)
    - tracks vertical mouse movement
    - auto-scrolls the container when dragging near top/bottom edges
    - reorders widgets in the target layout
    - keeps the underlying data list synchronized
    - persists the new order after drop

    The controller is generic and does not know anything about Keys, Prompts,
    AI Models, Links, or Commands.
    """

    HOLD_DELAY_MS = 140
    MOVE_THRESHOLD_PX = 6
    AUTO_SCROLL_INTERVAL_MS = 25
    SCROLL_ZONE_PX = 40
    BASE_SCROLL_STEP = 5
    MAX_SCROLL_STEP = 15

    def __init__(
        self,
        parent: QObject,
        layout: QLayout,
        data_provider: Callable[[], list],
        save_callback: Callable[[], None],
        scroll_area: Optional[QScrollArea] = None,
    ):
        super().__init__(parent)

        self.layout = layout
        self.data_provider = data_provider
        self.save_callback = save_callback
        self.scroll_area = scroll_area

        self._card: Optional[QWidget] = None
        self._pressed_pos = QPoint()
        self._dragging = False
        self._pending = False

        self._hold_timer = QTimer(self)
        self._hold_timer.setSingleShot(True)
        self._hold_timer.setInterval(self.HOLD_DELAY_MS)
        self._hold_timer.timeout.connect(self._begin_drag)

        self._auto_scroll_timer = QTimer(self)
        self._auto_scroll_timer.setInterval(self.AUTO_SCROLL_INTERVAL_MS)
        self._auto_scroll_timer.timeout.connect(self._handle_auto_scroll)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def attach(self, card: QWidget) -> None:
        """
        Attach drag handling to a card.

        BaseCard provides these signals:
            drag_pressed
            drag_moved
            drag_released
        """
        card.drag_pressed.connect(self._on_pressed)
        card.drag_moved.connect(self._on_moved)
        card.drag_released.connect(self._on_released)

    # ------------------------------------------------------------------
    # Mouse lifecycle
    # ------------------------------------------------------------------

    def _on_pressed(self, card: QWidget, pos: QPoint) -> None:
        if self._dragging:
            return

        self._card = card
        self._pressed_pos = QPoint(pos)
        self._pending = True

        self._hold_timer.start()

    def _begin_drag(self) -> None:
        if not self._pending or self._card is None:
            return

        self._pending = False
        self._dragging = True

        self._card.setProperty("dragging", True)
        self._card.style().unpolish(self._card)
        self._card.style().polish(self._card)
        self._card.update()

        self._card.setCursor(Qt.ClosedHandCursor)

        if self.scroll_area is not None:
            self._auto_scroll_timer.start()

    def _on_moved(self, card: QWidget, pos: QPoint) -> None:
        if card is not self._card:
            return

        if not self._dragging:
            if abs(pos.y() - self._pressed_pos.y()) > self.MOVE_THRESHOLD_PX:
                self._hold_timer.stop()
                self._pending = False
            return

        self._move_card(card)
        if self.scroll_area is not None and not self._auto_scroll_timer.isActive():
            self._auto_scroll_timer.start()

    def _on_released(self, card: QWidget) -> None:
        if card is not self._card:
            return

        self._hold_timer.stop()
        self._pending = False

        if not self._dragging:
            self._reset()
            return

        self._dragging = False

        card.setProperty("dragging", False)
        card.unsetCursor()
        card.style().unpolish(card)
        card.style().polish(card)
        card.update()

        self.save_callback()
        self._reset()

    # ------------------------------------------------------------------
    # Reordering
    # ------------------------------------------------------------------

    def _move_card(self, card: QWidget) -> None:
        index = self.layout.indexOf(card)
        if index < 0:
            return

        target_index = self._target_index(card)
        if target_index < 0 or target_index == index:
            return

        data = self.data_provider()
        if not data or index >= len(data):
            return

        # Layout may contain stretch/spacer items. Identify valid card positions.
        card_indexes = [
            i
            for i in range(self.layout.count())
            if self.layout.itemAt(i).widget() is not None
        ]

        if index not in card_indexes:
            return

        current_data_index = card_indexes.index(index)
        target_data_index = min(target_index, len(data) - 1)

        if current_data_index == target_data_index:
            return

        item = data.pop(current_data_index)
        data.insert(target_data_index, item)

        self._reinsert_card(card, target_data_index)

    def _target_index(self, dragged_card: QWidget) -> int:
        cursor_y = QCursor.pos().y()

        widgets = []
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if widget is None or widget is dragged_card or not widget.isVisible():
                continue
            widgets.append(widget)

        if not widgets:
            return -1

        target = 0
        for widget in widgets:
            center = widget.mapToGlobal(widget.rect().center())
            if cursor_y > center.y():
                target += 1

        return target

    def _reinsert_card(
        self,
        card: QWidget,
        data_index: int,
    ) -> None:
        # Remove only the widget without deleting or recreating it
        self.layout.removeWidget(card)

        widgets = []
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if widget is not None:
                widgets.append(widget)

        insert_at = min(data_index, len(widgets))
        self.layout.insertWidget(insert_at, card)

    def _handle_auto_scroll(self) -> None:
        """Auto-scroll the parent scroll area when dragging near top or bottom edges."""
        if not self._dragging or self._card is None or self.scroll_area is None:
            self._auto_scroll_timer.stop()
            return

        v_bar = self.scroll_area.verticalScrollBar()
        if v_bar is None or not v_bar.isVisible():
            return

        viewport = self.scroll_area.viewport()
        if viewport is None:
            return

        cursor_global = QCursor.pos()
        local_pos = viewport.mapFromGlobal(cursor_global)
        local_y = local_pos.y()
        v_height = viewport.height()

        scroll_step = 0
        if local_y < self.SCROLL_ZONE_PX:
            # Dragging near or above the top edge
            dist = max(1, self.SCROLL_ZONE_PX - local_y)
            ratio = min(1.0, dist / float(self.SCROLL_ZONE_PX))
            scroll_step = -int(self.BASE_SCROLL_STEP + ratio * (self.MAX_SCROLL_STEP - self.BASE_SCROLL_STEP))
        elif local_y > v_height - self.SCROLL_ZONE_PX:
            # Dragging near or below the bottom edge
            dist = max(1, local_y - (v_height - self.SCROLL_ZONE_PX))
            ratio = min(1.0, dist / float(self.SCROLL_ZONE_PX))
            scroll_step = int(self.BASE_SCROLL_STEP + ratio * (self.MAX_SCROLL_STEP - self.BASE_SCROLL_STEP))

        if scroll_step != 0:
            old_val = v_bar.value()
            new_val = max(v_bar.minimum(), min(v_bar.maximum(), old_val + scroll_step))
            if new_val != old_val:
                v_bar.setValue(new_val)
                self._move_card(self._card)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def cancel(self) -> None:
        self._hold_timer.stop()
        self._auto_scroll_timer.stop()

        if self._card is not None:
            self._card.setProperty("dragging", False)
            self._card.unsetCursor()
            self._card.style().unpolish(self._card)
            self._card.style().polish(self._card)
            self._card.update()

        self._reset()

    def _reset(self) -> None:
        self._auto_scroll_timer.stop()
        self._card = None
        self._pressed_pos = QPoint()
        self._pending = False
        self._dragging = False
