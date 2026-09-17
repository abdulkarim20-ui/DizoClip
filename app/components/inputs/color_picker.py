"""
Modular Custom Color Picker and Palette Bar component.
Provides:
- SaturationValueCanvas: 2D HSV saturation-value gradient with draggable reticle.
- HueSlider: 360° rainbow hue gradient slider.
- ColorPickerPopup: Modern floating popover matching reference design with eyedropper,
  real-time swatch preview, RGB/Hex inputs, and OK/Cancel confirmation.
- ColorSelectorBar: Modular color palette row with standard and saved custom colors,
  active white ring indicator, and dashed (+) add button.
"""

from typing import List, Optional

from PySide6.QtCore import QPoint, QPointF, QRectF, QTimer, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QGuiApplication,
    QLinearGradient,
    QPainter,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QColorDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.components.labels.animated_tooltip import attach_tooltip, set_tooltip
from app.config.constants import BADGE_COLORS
from app.core.icons import render_pixmap
from app.core.storage import add_custom_color_to_disk, load_custom_colors_from_disk
from app.utils.color_validator import validate_badge_color


class SaturationValueCanvas(QWidget):
    """2D Saturation / Value interactive gradient canvas."""
    color_changed = Signal(float, float)  # (sat 0..1, val 0..1)

    def __init__(self, hue: float = 0.0, sat: float = 1.0, val: float = 1.0, parent=None):
        super().__init__(parent)
        self._hue = hue
        self._sat = sat
        self._val = val
        self.setFixedSize(228, 126)
        self.setCursor(Qt.CrossCursor)

    def set_hsv(self, hue: float, sat: float, val: float):
        self._hue = hue
        self._sat = max(0.0, min(1.0, sat))
        self._val = max(0.0, min(1.0, val))
        self.update()

    def set_hue(self, hue: float):
        self._hue = hue
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._handle_mouse(event.position())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self._handle_mouse(event.position())
        super().mouseMoveEvent(event)

    def _handle_mouse(self, pos: QPointF):
        w = max(1.0, float(self.width()))
        h = max(1.0, float(self.height()))
        self._sat = max(0.0, min(1.0, pos.x() / w))
        self._val = max(0.0, min(1.0, 1.0 - (pos.y() / h)))
        self.color_changed.emit(self._sat, self._val)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = float(self.width()), float(self.height())
        rect = QRectF(0, 0, w, h)

        # 1. Base hue layer
        base_col = QColor.fromHsvF(max(0.0, min(359.9, self._hue)) / 360.0, 1.0, 1.0)
        p.fillRect(rect, base_col)

        # 2. Horizontal white gradient (Saturation)
        grad_h = QLinearGradient(0, 0, w, 0)
        grad_h.setColorAt(0.0, QColor(255, 255, 255, 255))
        grad_h.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.fillRect(rect, grad_h)

        # 3. Vertical black gradient (Value/Brightness)
        grad_v = QLinearGradient(0, 0, 0, h)
        grad_v.setColorAt(0.0, QColor(0, 0, 0, 0))
        grad_v.setColorAt(1.0, QColor(0, 0, 0, 255))
        p.fillRect(rect, grad_v)

        # 4. Circular draggable thumb
        tx = self._sat * w
        ty = (1.0 - self._val) * h

        # Outer black shadow ring
        p.setPen(QPen(QColor(0, 0, 0, 160), 2.5))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(tx, ty), 6.5, 6.5)

        # Inner white ring
        p.setPen(QPen(QColor(255, 255, 255, 255), 2.0))
        p.drawEllipse(QPointF(tx, ty), 5.5, 5.5)
        p.end()


class HueSlider(QWidget):
    """Horizontal 360° rainbow hue gradient slider."""
    hue_changed = Signal(float)  # hue 0..360

    def __init__(self, hue: float = 0.0, parent=None):
        super().__init__(parent)
        self._hue = hue
        self.setFixedHeight(14)
        self.setCursor(Qt.PointingHandCursor)

    def set_hue(self, hue: float):
        self._hue = max(0.0, min(360.0, hue))
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._handle_mouse(event.position())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self._handle_mouse(event.position())
        super().mouseMoveEvent(event)

    def _handle_mouse(self, pos: QPointF):
        w = max(1.0, float(self.width()))
        self._hue = max(0.0, min(360.0, (pos.x() / w) * 360.0))
        self.hue_changed.emit(self._hue)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = float(self.width()), float(self.height())

        # Rainbow bar track
        grad = QLinearGradient(0, 0, w, 0)
        grad.setColorAt(0.00, QColor(255, 0, 0))
        grad.setColorAt(0.17, QColor(255, 255, 0))
        grad.setColorAt(0.33, QColor(0, 255, 0))
        grad.setColorAt(0.50, QColor(0, 255, 255))
        grad.setColorAt(0.67, QColor(0, 0, 255))
        grad.setColorAt(0.83, QColor(255, 0, 255))
        grad.setColorAt(1.00, QColor(255, 0, 0))

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(grad))
        track_rect = QRectF(0, 2, w, h - 4)
        p.drawRoundedRect(track_rect, 5.0, 5.0)

        # Draggable circular thumb
        tx = max(5.0, min(w - 5.0, (self._hue / 360.0) * w))
        ty = h / 2.0

        p.setBrush(QBrush(QColor.fromHsvF(max(0.0, min(359.9, self._hue)) / 360.0, 1.0, 1.0)))
        p.setPen(QPen(QColor(255, 255, 255), 2.0))
        p.drawEllipse(QPointF(tx, ty), 6.0, 6.0)
        p.end()


class ColorPreviewCircle(QWidget):
    """Circular color swatch displaying active picked color."""
    def __init__(self, color: QColor, parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(26, 26)

    def set_color(self, color: QColor):
        self._color = color
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor(255, 255, 255, 50), 1.0))
        p.setBrush(QBrush(self._color))
        p.drawEllipse(1, 1, 24, 24)
        p.end()


class ColorWarningToast(QFrame):
    """Mini warning popup informing the user that a selected color is too dark / low-contrast."""
    def __init__(self, message: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("ColorWarningToast")
        self.setStyleSheet("""
            QFrame#ColorWarningToast {
                background-color: #27140f;
                border: 1px solid #f97316;
                border-radius: 6px;
            }
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(6)

        ico = QLabel()
        pm = render_pixmap("alert-triangle", (13, 13), color="#f97316")
        if pm is None:
            pm = render_pixmap("circle-alert", (13, 13), color="#f97316")
        if pm:
            ico.setPixmap(pm)
            ico.setFixedSize(13, 13)
            ico.setStyleSheet("background: transparent; border: none;")
            lay.addWidget(ico, 0, Qt.AlignTop)

        self.msg_lbl = QLabel(message)
        self.msg_lbl.setWordWrap(True)
        self.msg_lbl.setStyleSheet("color: #fed7aa; font-size: 10.5px; font-weight: 500; background: transparent; border: none; line-height: 1.25;")
        lay.addWidget(self.msg_lbl, 1, Qt.AlignVCenter)

    def set_message(self, message: str):
        self.msg_lbl.setText(message)


class ColorPickerPopup(QFrame):
    """
    Modern Custom Color Picker popover matching user reference image:
    - 2D Saturation / Value gradient canvas
    - Pipette / eyedropper tool
    - Color preview circular swatch
    - Rainbow Hue slider
    - R, G, B numeric inputs (and Hex mode toggle)
    - Cancel & OK action buttons
    """
    def __init__(
        self,
        initial_color: str = "#e8794a",
        on_ok=None,
        on_close=None,
        on_custom_added=None,
        parent=None,
    ):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._on_ok = on_ok
        self._on_close = on_close
        self._on_custom_added = on_custom_added

        self.current_color = QColor(initial_color)
        if not self.current_color.isValid():
            self.current_color = QColor("#e8794a")

        h_val = float(self.current_color.hueF() * 360.0)
        if h_val < 0:
            h_val = 0.0
        self._hue = h_val
        self._sat = float(self.current_color.saturationF())
        self._val = float(self.current_color.valueF())
        self._syncing_inputs = False

        card = QFrame(self)
        card.setObjectName("ColorPickerCard")
        card.setStyleSheet("""
            QFrame#ColorPickerCard {
                background-color: #171a24;
                border: 1px solid #364156;
                border-radius: 10px;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(card)

        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(10, 10, 10, 10)
        card_lay.setSpacing(10)

        # 1. 2D Saturation / Value Canvas
        self.canvas = SaturationValueCanvas(self._hue, self._sat, self._val, card)
        self.canvas.color_changed.connect(self._on_canvas_changed)
        card_lay.addWidget(self.canvas)

        # 2. Control Row: Eyedropper + Color Swatch + Hue Slider
        ctrl_row = QHBoxLayout()
        ctrl_row.setContentsMargins(0, 0, 0, 0)
        ctrl_row.setSpacing(8)

        self.pipette_btn = QPushButton()
        self.pipette_btn.setFixedSize(24, 24)
        self.pipette_btn.setCursor(Qt.PointingHandCursor)
        self.pipette_btn.setToolTip("Pick color from screen")
        self.pipette_btn.setStyleSheet("""
            QPushButton {
                background-color: #212635;
                border: 1px solid #2d3548;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2b3245;
                border-color: #3f4a63;
            }
        """)
        pip_pm = render_pixmap("pipette", (13, 13), color="#cbd5e1")
        if pip_pm:
            self.pipette_btn.setIcon(pip_pm)
        self.pipette_btn.clicked.connect(self._open_eyedropper)
        ctrl_row.addWidget(self.pipette_btn)

        self.swatch = ColorPreviewCircle(self.current_color, card)
        ctrl_row.addWidget(self.swatch)

        self.hue_slider = HueSlider(self._hue, card)
        self.hue_slider.hue_changed.connect(self._on_hue_slider_changed)
        ctrl_row.addWidget(self.hue_slider, 1)

        card_lay.addLayout(ctrl_row)

        # 3. Inputs Row: R, G, B boxes with labels below
        rgb_container = QWidget()
        rgb_container.setStyleSheet("background: transparent;")
        rgb_lay = QHBoxLayout(rgb_container)
        rgb_lay.setContentsMargins(0, 0, 0, 0)
        rgb_lay.setSpacing(6)

        def make_channel_col(name: str):
            col = QVBoxLayout()
            col.setContentsMargins(0, 0, 0, 0)
            col.setSpacing(3)
            inp = QLineEdit()
            inp.setFixedSize(44, 26)
            inp.setAlignment(Qt.AlignCenter)
            inp.setMaxLength(3)
            inp.setStyleSheet("""
                QLineEdit {
                    background-color: #12141c;
                    border: 1px solid #282f40;
                    border-radius: 5px;
                    color: #ffffff;
                    font-size: 11.5px;
                    font-weight: 600;
                }
                QLineEdit:focus {
                    border-color: #ff8c5a;
                }
            """)
            lbl = QLabel(name)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #7a8292; font-size: 10px; font-weight: 700;")
            col.addWidget(inp)
            col.addWidget(lbl)
            return col, inp

        col_r, self.r_input = make_channel_col("R")
        col_g, self.g_input = make_channel_col("G")
        col_b, self.b_input = make_channel_col("B")

        self.r_input.textChanged.connect(self._on_rgb_text_changed)
        self.g_input.textChanged.connect(self._on_rgb_text_changed)
        self.b_input.textChanged.connect(self._on_rgb_text_changed)

        rgb_lay.addLayout(col_r)
        rgb_lay.addLayout(col_g)
        rgb_lay.addLayout(col_b)

        # Hex representation input
        col_hex = QVBoxLayout()
        col_hex.setContentsMargins(0, 0, 0, 0)
        col_hex.setSpacing(3)
        self.hex_input = QLineEdit()
        self.hex_input.setFixedSize(68, 26)
        self.hex_input.setAlignment(Qt.AlignCenter)
        self.hex_input.setMaxLength(7)
        self.hex_input.setStyleSheet("""
            QLineEdit {
                background-color: #12141c;
                border: 1px solid #282f40;
                border-radius: 5px;
                color: #ffffff;
                font-size: 11px;
                font-weight: 600;
            }
            QLineEdit:focus {
                border-color: #ff8c5a;
            }
        """)
        self.hex_input.textChanged.connect(self._on_hex_text_changed)
        lbl_hex = QLabel("HEX")
        lbl_hex.setAlignment(Qt.AlignCenter)
        lbl_hex.setStyleSheet("color: #7a8292; font-size: 10px; font-weight: 700;")
        col_hex.addWidget(self.hex_input)
        col_hex.addWidget(lbl_hex)
        rgb_lay.addLayout(col_hex)

        card_lay.addWidget(rgb_container)

        # 4. Color Warning Mini Pop / Toast
        self.warning_box = ColorWarningToast(parent=card)
        self.warning_box.hide()
        card_lay.addWidget(self.warning_box)

        # 5. Action buttons: Cancel and OK
        act_row = QHBoxLayout()
        act_row.setContentsMargins(0, 2, 0, 0)
        act_row.setSpacing(8)

        act_row.addStretch(1)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedHeight(26)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #202534;
                border: 1px solid #2e364a;
                border-radius: 6px;
                color: #94a3b8;
                font-size: 11.5px;
                font-weight: 500;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: #272d3e;
                color: #ffffff;
            }
        """)
        self.cancel_btn.clicked.connect(self.close)
        act_row.addWidget(self.cancel_btn)

        self.ok_btn = QPushButton("OK")
        self.ok_btn.setFixedHeight(26)
        self.ok_btn.setCursor(Qt.PointingHandCursor)
        self.ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff8c5a;
                border: none;
                border-radius: 6px;
                color: #ffffff;
                font-size: 11.5px;
                font-weight: 700;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #ff9d71;
            }
            QPushButton:pressed {
                background-color: #e57c4c;
            }
        """)
        self.ok_btn.clicked.connect(self._commit_color)
        act_row.addWidget(self.ok_btn)

        card_lay.addLayout(act_row)

        self._sync_inputs_from_color()

    def _on_canvas_changed(self, sat: float, val: float):
        self._sat = sat
        self._val = val
        self._recompute_color()

    def _on_hue_slider_changed(self, hue: float):
        self._hue = hue
        self.canvas.set_hue(hue)
        self._recompute_color()

    def _recompute_color(self):
        h_frac = max(0.0, min(359.9, self._hue)) / 360.0
        self.current_color = QColor.fromHsvF(h_frac, self._sat, self._val)
        self.swatch.set_color(self.current_color)
        self._sync_inputs_from_color()
        if hasattr(self, "warning_box") and self.warning_box.isVisible():
            is_valid, _ = validate_badge_color(self.current_color)
            if is_valid:
                self._hide_warning()

    def _sync_inputs_from_color(self):
        self._syncing_inputs = True
        self.r_input.setText(str(self.current_color.red()))
        self.g_input.setText(str(self.current_color.green()))
        self.b_input.setText(str(self.current_color.blue()))
        self.hex_input.setText(self.current_color.name())
        self._syncing_inputs = False

    def _on_rgb_text_changed(self):
        if self._syncing_inputs:
            return
        try:
            r = int(self.r_input.text() or "0")
            g = int(self.g_input.text() or "0")
            b = int(self.b_input.text() or "0")
            col = QColor(max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
            if col.isValid():
                self._apply_external_color(col)
        except ValueError:
            pass

    def _on_hex_text_changed(self):
        if self._syncing_inputs:
            return
        txt = self.hex_input.text().strip()
        if not txt.startswith("#"):
            txt = "#" + txt
        col = QColor(txt)
        if col.isValid() and len(txt) == 7:
            self._apply_external_color(col)

    def _apply_external_color(self, col: QColor):
        self.current_color = col
        h_val = float(col.hueF() * 360.0)
        if h_val < 0:
            h_val = self._hue
        self._hue = h_val
        self._sat = float(col.saturationF())
        self._val = float(col.valueF())

        self.canvas.set_hsv(self._hue, self._sat, self._val)
        self.hue_slider.set_hue(self._hue)
        self.swatch.set_color(self.current_color)

    def _open_eyedropper(self):
        from app.components.inputs.screen_color_picker import ScreenColorPickerOverlay

        saved_pos = self.pos()
        saved_on_close = self._on_close
        self._on_close = None
        self.hide()

        overlay = ScreenColorPickerOverlay()

        def on_picked(col: QColor):
            try:
                overlay._finish()
            except Exception:
                pass

            is_valid, reason = validate_badge_color(col)
            if not is_valid:
                self.move(saved_pos)
                self.show()
                self._apply_external_color(col)
                self._show_warning_mini_pop(reason)
                return

            hex_val = col.name().lower()
            add_custom_color_to_disk(hex_val, max_count=8)

            cb = saved_on_close
            self._on_close = None

            if self._on_ok:
                try:
                    self._on_ok(hex_val)
                except Exception:
                    pass

            self.close()
            self.deleteLater()

            if cb:
                try:
                    cb()
                except Exception:
                    pass

        def on_cancelled():
            try:
                overlay._finish()
            except Exception:
                pass
            self._on_close = saved_on_close
            self.move(saved_pos)
            self.show()

        overlay.color_picked.connect(on_picked)
        overlay.cancelled.connect(on_cancelled)
        overlay.show()
        self._screen_overlay = overlay

    def _show_ok_feedback(self):
        """Display prominent visual feedback on the OK button that color was picked & added."""
        self.ok_btn.setText("✓ Added")
        self.ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                border: 2px solid #34d399;
                border-radius: 6px;
                color: #ffffff;
                font-size: 11.5px;
                font-weight: 700;
                padding: 0 14px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        QTimer.singleShot(1800, self._reset_ok_button)

    def _reset_ok_button(self):
        self.ok_btn.setText("OK")
        self.ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff8c5a;
                border: none;
                border-radius: 6px;
                color: #ffffff;
                font-size: 11.5px;
                font-weight: 700;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #ff9d71;
            }
            QPushButton:pressed {
                background-color: #e57c4c;
            }
        """)

    def _commit_color(self):
        is_valid, reason = validate_badge_color(self.current_color)
        if not is_valid:
            self._show_warning_mini_pop(reason)
            return

        hex_val = self.current_color.name()
        if self._on_ok:
            self._on_ok(hex_val)
        self.close()

    def _show_warning_mini_pop(self, message: str):
        self.warning_box.set_message(message)
        self.warning_box.show()
        self.layout().activate()
        sz = self.sizeHint()
        self.setFixedSize(max(248, sz.width()), sz.height())
        QTimer.singleShot(4500, self._hide_warning)

    def _hide_warning(self):
        if hasattr(self, "warning_box") and self.warning_box.isVisible():
            self.warning_box.hide()
            self.layout().activate()
            sz = self.sizeHint()
            self.setFixedSize(max(248, sz.width()), sz.height())

    def closeEvent(self, event):
        cb = self._on_close
        self._on_close = None
        if cb:
            try:
                cb()
            except Exception:
                pass
        super().closeEvent(event)

    def hideEvent(self, event):
        cb = self._on_close
        self._on_close = None
        if cb:
            try:
                cb()
            except Exception:
                pass
        super().hideEvent(event)


class DashedAddColorButton(QPushButton):
    """
    Circular dashed button rendering SVG plus icon from assets/plus.svg.
    When a custom color is added, displays the tick SVG from assets/check.svg
    with vibrant success styling for feedback before reverting.
    """
    def __init__(self, on_click=None, parent=None):
        super().__init__(parent)
        self.setFixedSize(22, 22)
        self.setCursor(Qt.PointingHandCursor)
        attach_tooltip(self, "Add custom color", placement="top")
        self._show_tick = False
        if on_click:
            self.clicked.connect(on_click)

    def show_tick_feedback(self):
        """Display the check / tick SVG icon feedback when a color is added."""
        self._show_tick = True
        set_tooltip(self, "Color added!", placement="top")
        self.update()
        QTimer.singleShot(1800, self._reset_tick)

    def _reset_tick(self):
        self._show_tick = False
        set_tooltip(self, "Add custom color", placement="top")
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        w, h = float(self.width()), float(self.height())

        is_hover = self.underMouse()

        if self._show_tick:
            border_col = QColor("#10b981")
            bg_col = QColor("#064e3b")
            icon_col = "#10b981"
            icon_name = "check"
            icon_size = (11, 11)
        else:
            border_col = QColor("#94a3b8") if is_hover else QColor("#3b475c")
            bg_col = QColor("#222a3b") if is_hover else QColor("#171c26")
            icon_col = "#ffffff" if is_hover else "#8f9db3"
            icon_name = "plus"
            icon_size = (10, 10)

        # 1. Background fill
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(bg_col))
        p.drawEllipse(QRectF(1.0, 1.0, w - 2.0, h - 2.0))

        # 2. Solid Circular border
        pen = QPen(border_col, 1.2, Qt.SolidLine)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QRectF(1.0, 1.0, w - 2.0, h - 2.0))

        # 3. SVG icon (check.svg or plus.svg)
        pm = render_pixmap(icon_name, icon_size, color=icon_col)
        if pm and not pm.isNull():
            dpr = pm.devicePixelRatio()
            pw = pm.width() / dpr
            ph = pm.height() / dpr
            ix = int((w - pw) / 2.0)
            iy = int((h - ph) / 2.0)
            p.drawPixmap(ix, iy, pm)

        p.end()


class ColorSelectorBar(QWidget):
    """
    Reusable modular color palette bar.
    Displays:
    - Row 1: 'Color:' label + 8 standard BADGE_COLORS + Dashed circular (+) button.
    - Row 2: Indented directly beneath column 1, showing up to 8 persistent custom colors.
    - Active color highlighted with a white selection ring across either row.
    - Shared across all modules via DC_Custom_Colors.json (capped to 8 custom colors).
    """
    color_changed = Signal(str)

    def __init__(
        self,
        initial_color: str = BADGE_COLORS[0],
        on_color_changed=None,
        win=None,
        show_label: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self.win = win
        self.show_label = show_label
        self.selected_color = initial_color.lower().strip()
        self._on_color_changed_cb = on_color_changed
        self._color_buttons = {}
        self._popover = None

        self.root_lay = QVBoxLayout(self)
        self.root_lay.setContentsMargins(0, 2, 0, 2)
        self.root_lay.setSpacing(5)

        self._refresh_palette()

    def get_color(self) -> str:
        return self.selected_color

    def set_color(self, color_hex: str):
        color_hex = color_hex.lower().strip()
        self.selected_color = color_hex

        # If not present in standard colors or disk, add it to custom colors
        standard_lower = [c.lower() for c in BADGE_COLORS]
        if color_hex not in standard_lower:
            custom_colors = load_custom_colors_from_disk()
            if color_hex not in custom_colors:
                add_custom_color_to_disk(color_hex, max_count=8)

        self._refresh_palette()

    def _refresh_palette(self):
        # Clear existing layout items
        while self.root_lay.count():
            item = self.root_lay.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()
        self._color_buttons.clear()

        LABEL_W = 46
        SPACING = 6
        BTN_SIZE = 22

        # ----------------- ROW 1: Standard Colors + (+) Button -----------------
        row1_widget = QWidget(self)
        row1_lay = QHBoxLayout(row1_widget)
        row1_lay.setContentsMargins(0, 0, 0, 0)
        row1_lay.setSpacing(SPACING)

        if self.show_label:
            lbl = QLabel("Color:")
            lbl.setStyleSheet("color: #8f9db3; font-size: 12px; font-weight: 500;")
            lbl.setFixedWidth(LABEL_W)
            row1_lay.addWidget(lbl, 0, Qt.AlignVCenter)

        for c in BADGE_COLORS:
            cl = c.lower()
            btn = QPushButton()
            btn.setCheckable(True)
            btn.setFixedSize(BTN_SIZE, BTN_SIZE)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {cl};
                    border: none;
                    border-radius: 11px;
                }}
                QPushButton:checked {{
                    border: 2px solid #ffffff;
                }}
            """)
            btn.setChecked(cl == self.selected_color)
            attach_tooltip(btn, cl.upper(), placement="top")
            btn.clicked.connect(lambda _=False, col=cl: self._select_color(col))
            row1_lay.addWidget(btn, 0, Qt.AlignVCenter)
            self._color_buttons[cl] = btn

        # Dashed Circular (+) Button with SVG plus icon from assets/plus.svg
        self.add_btn = DashedAddColorButton(on_click=self._open_color_picker, parent=self)
        attach_tooltip(self.add_btn, "Add custom color", placement="top")
        row1_lay.addWidget(self.add_btn, 0, Qt.AlignVCenter)
        row1_lay.addStretch(1)
        self.root_lay.addWidget(row1_widget)

        # ----------------- ROW 2: Custom Colors (Up to 8) -----------------
        custom_colors = load_custom_colors_from_disk()[:8]

        # If selected_color is not standard and not in custom_colors, show it
        standard_lower = [c.lower() for c in BADGE_COLORS]
        if self.selected_color not in standard_lower and self.selected_color not in custom_colors:
            custom_colors.insert(0, self.selected_color)
            custom_colors = custom_colors[:8]

        row2_widget = QWidget(self)
        row2_lay = QHBoxLayout(row2_widget)
        row2_lay.setContentsMargins(0, 0, 0, 0)
        row2_lay.setSpacing(SPACING)

        if self.show_label:
            indent = QWidget()
            indent.setFixedWidth(LABEL_W)
            row2_lay.addWidget(indent, 0, Qt.AlignVCenter)

        for c in custom_colors:
            cl = c.lower()
            btn = QPushButton()
            btn.setCheckable(True)
            btn.setFixedSize(BTN_SIZE, BTN_SIZE)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {cl};
                    border: none;
                    border-radius: 11px;
                }}
                QPushButton:checked {{
                    border: 2px solid #ffffff;
                }}
            """)
            btn.setChecked(cl == self.selected_color)
            attach_tooltip(btn, f"Custom: {cl.upper()}", placement="top")
            btn.clicked.connect(lambda _=False, col=cl: self._select_color(col))
            row2_lay.addWidget(btn, 0, Qt.AlignVCenter)
            self._color_buttons[cl] = btn

        row2_lay.addStretch(1)

        # Only show Row 2 if there are custom colors to display
        if custom_colors:
            row2_widget.setVisible(True)
            self.root_lay.addWidget(row2_widget)
        else:
            row2_widget.setVisible(False)
        self.row2_widget = row2_widget

    def _select_color(self, color_hex: str):
        self.selected_color = color_hex.lower()
        for c, btn in self._color_buttons.items():
            btn.setChecked(c == self.selected_color)
        self.color_changed.emit(self.selected_color)
        if self._on_color_changed_cb:
            self._on_color_changed_cb(self.selected_color)

    def _open_color_picker(self):
        if self._popover is not None:
            try:
                self._popover.close()
                self._popover.deleteLater()
            except Exception:
                pass
            self._popover = None

        top_win = self.window()
        self._popover = ColorPickerPopup(
            initial_color=self.selected_color,
            on_ok=self._on_custom_color_confirmed,
            on_close=self._on_popover_closed,
            parent=top_win,
        )
        self._popover.layout().activate()
        sz = self._popover.sizeHint()
        pop_w = max(248, sz.width())
        pop_h = sz.height()
        self._popover.setFixedSize(pop_w, pop_h)

        btn_pos = self.add_btn.mapToGlobal(self.add_btn.rect().topLeft())

        x = btn_pos.x() - (pop_w - self.add_btn.width())
        y = btn_pos.y() - pop_h - 6  # Open above palette bar

        if top_win:
            win_top = top_win.mapToGlobal(top_win.rect().topLeft()).y()
            if y < win_top + 8:
                y = btn_pos.y() + self.add_btn.height() + 6  # Flip below if needed

        self._popover.move(x, y)
        self._popover.show()

    def _on_custom_color_confirmed(self, color_hex: str):
        color_hex = color_hex.lower()
        add_custom_color_to_disk(color_hex, max_count=8)
        self.selected_color = color_hex
        self._refresh_palette()
        self.color_changed.emit(self.selected_color)
        if self._on_color_changed_cb:
            self._on_color_changed_cb(self.selected_color)
        if hasattr(self, "add_btn") and self.add_btn:
            self.add_btn.show_tick_feedback()

    def _on_custom_color_added_from_picker(self, color_hex: str):
        color_hex = color_hex.lower()
        self.selected_color = color_hex
        self._refresh_palette()
        self.color_changed.emit(self.selected_color)
        if self._on_color_changed_cb:
            self._on_color_changed_cb(self.selected_color)
        if hasattr(self, "add_btn") and self.add_btn:
            self.add_btn.show_tick_feedback()

    def _on_popover_closed(self):
        self._popover = None
