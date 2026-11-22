"""
Window show/hide helpers.

Launch feel: the window is prepared (DWM dark title bar, rounded corners, WS_POPUP cleared) BEFORE
the first show(), then shown immediately. Windows 11 plays its own native open animation for a
standard overlapped window, so no Qt-side fade is needed (and none is the default).

Why no QGraphicsOpacityEffect on the top-level window:
  an effect forces the whole window to be painted into an off-screen pixmap and keeps it on that
  slower path for as long as it stays attached. The old code never detached it after the fade, so
  every repaint went through it for the whole life of the app. A fade, if wanted, uses
  windowOpacity instead (native layered window, no off-screen copy) and is removed when done.
"""
from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt


def prepare_window_for_native_transition(
    window,
    bg_hex: str = "#0f111a",
    text_hex: str = "#e2e8f0",
    border_hex: str = "#2a2f3d",
) -> bool:
    """Prepare native window appearance before show."""
    from app.core.window_utils import apply_dark_title_bar
    apply_dark_title_bar(window, bg_hex, text_hex, border_hex)
    window.setAttribute(Qt.WA_OpaquePaintEvent, True)
    window.setAttribute(Qt.WA_NoSystemBackground, True)
    window.setAutoFillBackground(True)
    window._native_transition_prepared = True
    return True


def _activate(window) -> None:
    window.show()
    window.raise_()
    window.activateWindow()


def show_prepared_window(window, duration: int = 0, on_finished=None) -> None:
    """
    Show the prepared window right now. duration=0 (default) lets Windows/DWM do the transition.
    duration>0 adds a cheap windowOpacity fade (no graphics effect, nothing left attached).
    """
    if duration <= 0:
        _activate(window)
        if on_finished:
            on_finished()
        return

    window.setWindowOpacity(0.0)
    _activate(window)
    anim = QPropertyAnimation(window, b"windowOpacity", window)
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.OutCubic)

    def _done():
        window.setWindowOpacity(1.0)
        if on_finished:
            on_finished()

    anim.finished.connect(_done)
    anim.start(QPropertyAnimation.DeleteWhenStopped)


def hide_window_with_animation(window, duration: int = 0, on_finished=None) -> None:
    """Hide the window; DWM plays the native close transition. Calls on_finished right after."""
    window.hide()
    if on_finished:
        on_finished()


# Names kept so existing imports keep working.
def show_window_with_animation(window, duration: int = 0, on_finished=None) -> None:
    show_prepared_window(window, duration=duration, on_finished=on_finished)


animate_window_show = show_window_with_animation
animate_window_hide = hide_window_with_animation
