from PySide6.QtCore import QPoint, QPointF, QRectF, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QPushButton

from app.components.labels.animated_tooltip import attach_tooltip
from app.config.theme import ACCENT, TEXT_DIM, TEXT_MAIN
from app.core.icons import render_pixmap


class NavTabButton(QPushButton):
    """
    Top navigation tab button with dynamic icon tinting, active accent bar,
    animated tooltip, and hold-and-drag reordering (no triple-click needed).
    """
    drag_moved = Signal(object, int)  # (self, delta_x)
    drag_released = Signal(object)    # (self)

    HOLD_DELAY_MS = 140
    MOVE_THRESHOLD_PX = 6

    def __init__(self, icon_name: str, is_active: bool = False, tooltip: str = "", is_fixed: bool = False, parent=None):
        super().__init__(parent)
        self.icon_name = icon_name
        self.is_active = is_active
        self.is_fixed = is_fixed  # Fixed buttons (like Settings) cannot be reordered or dragged
        self.hovered = False
        self.is_dragging = False

        self.setFixedSize(28, 28)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("background: transparent; border: none;")

        self._pixmap_cache = {}
        self._tooltip_filter = None
        if tooltip:
            self._tooltip_filter = attach_tooltip(self, tooltip, placement="bottom")

        # Hold + Drag state tracking
        self._drag_start_pos = QPoint()
        self._drag_start_x = 0
        self._pending_hold = False

        self._hold_timer = QTimer(self)
        self._hold_timer.setSingleShot(True)
        self._hold_timer.setInterval(self.HOLD_DELAY_MS)
        self._hold_timer.timeout.connect(self._begin_drag)

    def set_active(self, active: bool):
        if self.is_active != active:
            self.is_active = active
            self.update()

    def _begin_drag(self):
        if not self._pending_hold or self.is_fixed:
            return
        self._pending_hold = False
        self.is_dragging = True
        self.setCursor(Qt.ClosedHandCursor)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self.is_fixed:
                self._drag_start_pos = event.position().toPoint()
                self._drag_start_x = int(event.globalPosition().x())
                self._pending_hold = True
                self._hold_timer.start()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self.is_dragging:
            if self._pending_hold:
                pos = event.position().toPoint()
                dx = abs(pos.x() - self._drag_start_pos.x())
                dy = abs(pos.y() - self._drag_start_pos.y())
                if dx > self.MOVE_THRESHOLD_PX or dy > self.MOVE_THRESHOLD_PX:
                    self._hold_timer.stop()
                    self._pending_hold = False
        else:
            current_x = int(event.globalPosition().x())
            dx = current_x - self._drag_start_x
            self.drag_moved.emit(self, dx)
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._hold_timer.stop()
            self._pending_hold = False

            if self.is_dragging:
                self.is_dragging = False
                self.setCursor(Qt.PointingHandCursor)
                self.update()
                self.drag_released.emit(self)
                event.accept()
                return

        super().mouseReleaseEvent(event)

    def enterEvent(self, event):
        self.hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered = False
        self.update()
        super().leaveEvent(event)

    def _get_pm(self, color_str: str):
        if color_str not in self._pixmap_cache:
            self._pixmap_cache[color_str] = render_pixmap(self.icon_name, (16, 16), color_str)
        return self._pixmap_cache[color_str]

    def paintEvent(self, event):
        p = QPainter(self)
        if not p.isActive():
            return
        p.setRenderHint(QPainter.Antialiasing)

        # Draw active dragging indicator (dashed accent border)
        if self.is_dragging and not self.is_fixed:
            pen = QPen(QColor(ACCENT), 1.4, Qt.DashLine)
            p.setPen(pen)
            p.setBrush(QColor(255, 140, 90, 35))
            p.drawRoundedRect(QRectF(1.0, 1.0, self.width() - 2.0, self.height() - 2.0), 5.0, 5.0)

        color_str = TEXT_MAIN if (self.is_active or self.hovered or self.is_dragging) else TEXT_DIM
        pm = self._get_pm(color_str)

        if pm and not pm.isNull():
            x = (self.width() - 16) / 2.0
            y = (self.height() - 16) / 2.0 - (1.0 if self.is_active else 0.0)
            p.drawPixmap(QPointF(x, y), pm)

        # Bottom active indicator: 14px centered line with 2px height and 1px radius
        if self.is_active and not self.is_dragging:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(ACCENT))
            p.drawRoundedRect(QRectF((self.width() - 14) / 2.0, self.height() - 2.0, 14.0, 2.0), 1.0, 1.0)

        p.end()
