"""
Screen color picker / eyedropper.

Interaction:
1. The color picker opens the screen sampling mode.
2. The click button cursor (Qt.PointingHandCursor) is displayed everywhere the user hovers.
3. The floating preview follows the cursor and shows the sampled HEX color.
4. Left-click commits the color immediately.
5. The eyedropper mode closes, the cursor override is restored, and the color
   is automatically saved into custom colors and applied to ColorPickerPopup.
6. The OK button shows visual feedback ("✓ Added") and ColorSelectorBar refreshes.
7. Right-click or Escape cancels and restores the normal picker state.

The screen preview is a separate transparent-for-input top-level window,
so it never steals the click from the fullscreen sampling overlay.
"""

from typing import List, Tuple

from PySide6.QtCore import QByteArray, QPoint, QRect, QTimer, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QFont,
    QGuiApplication,
    QImage,
    QPainter,
    QPen,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QWidget

from app.config.paths import ASSETS_DIR
from app.core.icons import render_pixmap


class ScreenColorPreview(QWidget):
    """Small top-level color preview that follows the global cursor."""

    WIDTH = 108
    HEIGHT = 28
    OFFSET = 14

    def __init__(self):
        super().__init__(
            None,
            Qt.Tool
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.NoDropShadowWindowHint,
        )

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setWindowFlag(Qt.WindowDoesNotAcceptFocus, True)
        self.setWindowFlag(Qt.WindowTransparentForInput, True)
        self.setFixedSize(self.WIDTH, self.HEIGHT)

        self._color = QColor("#ffffff")

    def mousePressEvent(self, event):
        event.ignore()

    def mouseReleaseEvent(self, event):
        event.ignore()

    def mouseMoveEvent(self, event):
        event.ignore()

    def set_color(self, color: QColor) -> None:
        if color == self._color:
            return

        self._color = QColor(color)
        self.update()

    def follow_cursor(self, global_pos: QPoint) -> None:
        """Keep the preview beside the cursor without covering its hotspot."""
        screen = QGuiApplication.screenAt(global_pos)

        if screen is None:
            self.move(
                global_pos.x() + self.OFFSET,
                global_pos.y() + self.OFFSET,
            )
            return

        area = screen.availableGeometry()

        x = global_pos.x() + self.OFFSET
        y = global_pos.y() + self.OFFSET

        # Flip horizontally when there is not enough room on the right.
        if x + self.width() > area.right() + 1:
            x = global_pos.x() - self.width() - self.OFFSET

        # Flip vertically when there is not enough room below.
        if y + self.height() > area.bottom() + 1:
            y = global_pos.y() - self.height() - self.OFFSET

        x = max(area.left(), min(x, area.right() - self.width() + 1))
        y = max(area.top(), min(y, area.bottom() - self.height() + 1))

        self.move(x, y)

    def update_preview(self, color: QColor, global_pos: QPoint) -> None:
        self.set_color(color)
        self.follow_cursor(global_pos)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        rect = QRect(0, 0, self.width() - 1, self.height() - 1)

        painter.setPen(QPen(QColor("#2d3548"), 1.0))
        painter.setBrush(QBrush(QColor("#131622")))
        painter.drawRoundedRect(rect, 5.0, 5.0)

        swatch = QRect(7, 6, 16, 16)
        painter.setPen(QPen(QColor(255, 255, 255, 65), 1.0))
        painter.setBrush(QBrush(self._color))
        painter.drawRoundedRect(swatch, 3.0, 3.0)

        font = QFont("Consolas", 9, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QPen(QColor("#ffffff")))
        painter.drawText(
            QRect(28, 6, self.width() - 34, 16),
            Qt.AlignVCenter | Qt.AlignLeft,
            self._color.name().upper(),
        )

        painter.end()


class ScreenColorPickerOverlay(QWidget):
    """
    Fullscreen eyedropper input layer.

    The locate.svg cursor is the active picker cursor. It is only applied
    while this overlay is active and is removed immediately after selection
    or cancellation.
    """

    color_picked = Signal(QColor)
    cancelled = Signal()

    CURSOR_UPDATE_MS = 16

    def __init__(self, parent=None):
        super().__init__(
            parent,
            Qt.Window
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool,
        )

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMouseTracking(True)

        self._current_color = QColor("#ffffff")
        self._cursor_pos = QCursor.pos()
        self._last_cursor_pos = QPoint(self._cursor_pos)
        self._screen_snapshots: List[Tuple[QRect, QImage, float]] = []
        self._closing = False

        self.preview = ScreenColorPreview()

        self._cursor_timer = QTimer(self)
        self._cursor_timer.setTimerType(Qt.PreciseTimer)
        self._cursor_timer.setInterval(self.CURSOR_UPDATE_MS)
        self._cursor_timer.timeout.connect(self._track_cursor)

        self._setup_geometry()
        self._capture_screens()
        self._set_click_cursor()

        # Immediately sample the color under the cursor when picker opens.
        self._update_from_cursor(self._cursor_pos)

    def _set_click_cursor(self) -> None:
        """Apply the click button cursor (pointing hand) across the application and overlay."""
        while QGuiApplication.overrideCursor() is not None:
            QGuiApplication.restoreOverrideCursor()
        QGuiApplication.setOverrideCursor(QCursor(Qt.PointingHandCursor))
        self.setCursor(Qt.PointingHandCursor)

    def _clear_click_cursor(self) -> None:
        """Restore previous cursor override when eyedropper completes or cancels."""
        while QGuiApplication.overrideCursor() is not None:
            QGuiApplication.restoreOverrideCursor()
        self.unsetCursor()

    def _setup_geometry(self) -> None:
        """Cover the complete virtual desktop across all connected screens."""
        screens = QGuiApplication.screens()

        if not screens:
            self.setGeometry(0, 0, 1920, 1080)
            return

        geometry = screens[0].geometry()

        for screen in screens[1:]:
            geometry = geometry.united(screen.geometry())

        self.setGeometry(geometry)

    def _capture_screens(self) -> None:
        """
        Capture each display once for fast pixel sampling.

        QScreen.grabWindow(0) captures screen pixels, while the cursor itself
        is generally not included in the grab. This lets the locate cursor
        remain visible without contaminating the sampled color.
        """
        self._screen_snapshots.clear()

        for screen in QGuiApplication.screens():
            geometry = screen.geometry()
            pixmap = screen.grabWindow(0)

            if pixmap.isNull():
                continue

            image = pixmap.toImage()
            dpr = float(image.devicePixelRatio())

            if dpr <= 0:
                dpr = float(screen.devicePixelRatio()) or 1.0

            self._screen_snapshots.append((geometry, image, dpr))

    def _sample_color_at(self, global_pos: QPoint) -> QColor:
        """Return the captured pixel directly under the locate cursor."""
        for geometry, image, dpr in self._screen_snapshots:
            if not geometry.contains(global_pos):
                continue

            x = int(round((global_pos.x() - geometry.x()) * dpr))
            y = int(round((global_pos.y() - geometry.y()) * dpr))

            x = max(0, min(image.width() - 1, x))
            y = max(0, min(image.height() - 1, y))

            color = image.pixelColor(x, y)

            if color.isValid():
                return color

        return self._current_color

    def _update_from_cursor(self, global_pos: QPoint) -> None:
        """Sample the hovered pixel and move the preview to the cursor."""
        self._cursor_pos = QPoint(global_pos)

        if self._cursor_pos != self._last_cursor_pos:
            self._last_cursor_pos = QPoint(self._cursor_pos)
            self._current_color = self._sample_color_at(self._cursor_pos)

        self.preview.update_preview(
            self._current_color,
            self._cursor_pos,
        )

    def _track_cursor(self) -> None:
        """Continuously track the real OS cursor between mouse events."""
        if self._closing:
            return

        pos = QCursor.pos()

        if pos == self._last_cursor_pos:
            return

        self._update_from_cursor(pos)

    def showEvent(self, event) -> None:
        super().showEvent(event)

        self._closing = False
        self.activateWindow()
        self.raise_()

        self._set_click_cursor()

        pos = QCursor.pos()
        self._update_from_cursor(pos)

        self.preview.show()
        self.preview.raise_()
        self._cursor_timer.start()

    def mouseMoveEvent(self, event) -> None:
        """
        Use globalPosition() for immediate sampling.

        Qt specifically recommends globalPosition() when a widget is moved
        in response to a mouse event to avoid shaking/jitter.
        """
        pos = event.globalPosition().toPoint()
        self._update_from_cursor(pos)
        event.accept()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            # Commit exactly the color currently under the locate cursor.
            pos = event.globalPosition().toPoint()
            self._update_from_cursor(pos)
            color = QColor(self._current_color)

            # Picker mode ends immediately after the click.
            self._finish()
            self.color_picked.emit(color)
            return

        if event.button() == Qt.RightButton:
            self._finish()
            self.cancelled.emit()
            return

        event.ignore()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Escape:
            self._finish()
            self.cancelled.emit()
            return

        super().keyPressEvent(event)

    def _finish(self) -> None:
        """
        Stop eyedropper mode.

        Restores previous cursor, closes floating preview, hides overlay, and stops cursor tracking.
        """
        if self._closing:
            return

        self._closing = True
        self._cursor_timer.stop()
        self._clear_click_cursor()
        try:
            self.preview.hide()
            self.preview.close()
        except Exception:
            pass
        self.hide()
        self.close()
        self.deleteLater()

    def closeEvent(self, event) -> None:
        self._finish()
        super().closeEvent(event)

    def hideEvent(self, event) -> None:
        self._finish()
        super().hideEvent(event)

    def paintEvent(self, event) -> None:
        # Fill with imperceptible 1/255 alpha so Windows DWM treats the entire virtual screen
        # as a solid hit-testable surface. This locks the cursor and prevents underlying apps
        # from receiving hover events or changing cursor styles.
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))
        painter.end()
