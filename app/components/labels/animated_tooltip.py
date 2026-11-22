"""
Modular animated tooltip component with smooth slide-up and fade-in transitions.
Matches UI theme: #141722 background, #282f42 border, #e2e8f0 text, 6px radius.
"""

from typing import Optional

from PySide6.QtCore import (
    QEasingCurve,
    QEvent,
    QObject,
    QPoint,
    QPropertyAnimation,
    Qt,
    QTimer,
)
from PySide6.QtGui import QColor, QCursor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QWidget,
)

from app.config.theme import FONT_UI, TEXT_MAIN, font_css


class CustomTooltipPopup(QFrame):
    """Floating styled tooltip popup matching the application UI theme."""
    def __init__(self, text: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent, Qt.ToolTip | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        # Card container with UI theme background & border
        self.card = QFrame(self)
        self.card.setObjectName("CustomTooltipCard")
        self.card.setStyleSheet("""
            QFrame#CustomTooltipCard {
                background-color: #141722;
                border: 1px solid #282f42;
                border-radius: 6px;
            }
        """)

        # Drop shadow: modern soft elevation
        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(14)
        shadow.setColor(QColor(0, 0, 0, 70))
        shadow.setOffset(0, 3)
        self.card.setGraphicsEffect(shadow)

        root = QHBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.addWidget(self.card)

        card_lay = QHBoxLayout(self.card)
        card_lay.setContentsMargins(8, 4, 8, 4)
        card_lay.setSpacing(0)

        self.label = QLabel(text)
        self.label.setStyleSheet(f"""
            color: {TEXT_MAIN};
            font-family: {FONT_UI};
            {font_css("subtext")}
            background: transparent;
            border: none;
        """)
        card_lay.addWidget(self.label)

        self._anim_pos: Optional[QPropertyAnimation] = None
        self.destroyed.connect(self._on_destroyed)

    def _on_destroyed(self) -> None:
        self._anim_pos = None

    def setText(self, text: str) -> None:
        self.label.setText(text)
        self.adjustSize()

    def show_animated(self, target_pos: QPoint, slide_up: bool = True) -> None:
        """Slide and display smoothly into target position."""
        self.adjustSize()
        start_offset = 4 if slide_up else -4
        start_pos = QPoint(target_pos.x(), target_pos.y() + start_offset)
        self.move(start_pos)
        self.show()

        if self._anim_pos is not None:
            try:
                self._anim_pos.stop()
            except RuntimeError:
                pass
            self._anim_pos = None

        animation = QPropertyAnimation(self, b"pos", self)
        animation.setDuration(120)
        animation.setStartValue(start_pos)
        animation.setEndValue(target_pos)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        self._anim_pos = animation
        animation.start()

    def hide_animated(self) -> None:
        """Close tooltip."""
        if self._anim_pos is not None:
            try:
                self._anim_pos.stop()
            except RuntimeError:
                pass
            self._anim_pos = None
        try:
            self.hide()
        except RuntimeError:
            pass


_SHARED_POPUP: Optional[CustomTooltipPopup] = None


def _acquire_popup(text: str, owner, window) -> CustomTooltipPopup:
    """
    One tooltip window for the whole app, reused by every widget.

    Before: every widget that was ever hovered kept its own native ToolTip window (+ drop-shadow
    effect + stylesheet) alive, parented to the main window, so they piled up and survived the
    cards that created them (cards are rebuilt on every list refresh).
    """
    global _SHARED_POPUP
    popup = _SHARED_POPUP
    if popup is not None:
        try:
            popup.setText(text)
        except RuntimeError:          # its parent window was deleted
            popup = None
    if popup is None:
        popup = CustomTooltipPopup(text, parent=window)
        _SHARED_POPUP = popup
    popup._owner = owner
    return popup


class TooltipFilter(QObject):
    """Event filter that manages animated tooltip display for a target widget."""
    def __init__(self, target_widget: QWidget, text: str, placement: str = "auto"):
        super().__init__(target_widget)
        self.target = target_widget
        self.text = text
        self.placement = placement
        self._tooltip_popup: Optional[CustomTooltipPopup] = None

        self._show_timer = QTimer(self)
        self._show_timer.setSingleShot(True)
        self._show_timer.setInterval(120)
        self._show_timer.timeout.connect(self._do_show)

        try:
            self.target.destroyed.connect(self._cleanup)
        except Exception:
            pass

    def _on_popup_destroyed(self) -> None:
        self._tooltip_popup = None

    def setText(self, text: str) -> None:
        """Dynamically update tooltip text."""
        self.text = text
        popup = self._tooltip_popup
        if popup is not None:
            try:
                if popup.isVisible() and getattr(popup, "_owner", None) is self:
                    popup.setText(text)
            except RuntimeError:
                self._tooltip_popup = None

    def _cleanup(self) -> None:
        """Safely stop tooltip activity when the target widget is destroyed."""
        self._show_timer.stop()

        popup = self._tooltip_popup
        self._tooltip_popup = None

        if popup is not None:
            try:
                if getattr(popup, "_owner", None) is self:
                    popup.hide()
            except RuntimeError:
                # Underlying Qt object has already been deleted.
                pass

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched == self.target:
            if event.type() == QEvent.Enter:
                self._show_timer.start()
            elif event.type() in (QEvent.Leave, QEvent.MouseButtonPress, QEvent.Hide):
                # Verify if cursor truly left the target bounding rect
                if event.type() == QEvent.Leave:
                    try:
                        if self.target.rect().contains(self.target.mapFromGlobal(QCursor.pos())):
                            return super().eventFilter(watched, event)
                    except RuntimeError:
                        pass
                self._show_timer.stop()
                self._do_hide()
        return super().eventFilter(watched, event)

    def _do_show(self) -> None:
        try:
            if not self.target.isVisible() or not self.text:
                return
            if not self.target.rect().contains(self.target.mapFromGlobal(QCursor.pos())):
                return
        except RuntimeError:
            return

        try:
            win = self.target.window() if self.target is not None else None
            self._tooltip_popup = _acquire_popup(self.text, self, win)
        except RuntimeError:
            self._tooltip_popup = None
            return

        try:
            self._tooltip_popup.adjustSize()
            target_rect = self.target.rect()
            global_center = self.target.mapToGlobal(target_rect.center())

            popup_w = self._tooltip_popup.sizeHint().width()
            popup_h = self._tooltip_popup.sizeHint().height()

            x = int(global_center.x() - popup_w / 2.0)

            # Bounds clamping with main window
            win = self.target.window()
            if win is not None:
                win_global_x = win.mapToGlobal(QPoint(0, 0)).x()
                win_w = win.width()
                x = max(win_global_x + 6, min(x, win_global_x + win_w - popup_w - 6))

            # Determine vertical position
            slide_up = True
            if self.placement == "bottom":
                y = self.target.mapToGlobal(target_rect.bottomLeft()).y() + 4
                slide_up = True
            elif self.placement == "top":
                y = self.target.mapToGlobal(target_rect.topLeft()).y() - popup_h - 4
                slide_up = False
            else:  # "auto"
                local_y = self.target.mapTo(win, QPoint(0, 0)).y() if win is not None else 100
                if local_y < 90:
                    y = self.target.mapToGlobal(target_rect.bottomLeft()).y() + 4
                    slide_up = True
                else:
                    y = self.target.mapToGlobal(target_rect.topLeft()).y() - popup_h - 4
                    slide_up = False

            self._tooltip_popup.show_animated(QPoint(x, y), slide_up=slide_up)
        except RuntimeError:
            self._tooltip_popup = None

    def _do_hide(self) -> None:
        popup = self._tooltip_popup
        if popup is not None:
            try:
                if popup.isVisible() and getattr(popup, "_owner", None) is self:
                    popup.hide_animated()
            except RuntimeError:
                self._tooltip_popup = None



def attach_tooltip(widget: QWidget, text: str, placement: str = "auto") -> TooltipFilter:
    """Attach a modular, animated custom tooltip matching the UI theme."""
    QWidget.setToolTip(widget, "")  # Clear native tooltip via QWidget base class directly
    tf = getattr(widget, "_custom_tooltip_filter", None)
    if tf is not None:
        tf.setText(text)
        tf.placement = placement
        return tf

    tf = TooltipFilter(widget, text, placement)
    widget._custom_tooltip_filter = tf
    widget.installEventFilter(tf)
    return tf


def set_tooltip(widget: QWidget, text: str, placement: str = "auto") -> Optional[TooltipFilter]:
    """Dynamically set or update modular custom tooltip text on any widget."""
    if not text:
        tf = getattr(widget, "_custom_tooltip_filter", None)
        if tf is not None:
            tf.setText("")
            tf._do_hide()
        QWidget.setToolTip(widget, "")
        return None
    return attach_tooltip(widget, text, placement)


