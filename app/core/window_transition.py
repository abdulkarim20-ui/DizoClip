"""
Window transition effects for smooth show/hide animations.
Provides native Windows-like fade and slide animations.
"""

from PySide6.QtCore import QPropertyAnimation, QEasingCurve, Qt, QTimer, QSize
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QGraphicsOpacityEffect


class WindowTransitionManager:
    """Manages window show/hide animations with fade and slide effects."""
    
    def __init__(self, window):
        self.window = window
        self.is_animating = False
        self.opacity_effect = None
        self.show_animation = None
        self.close_animation = None
    
    def setup_opacity_effect(self):
        """Setup opacity effect for fade animations."""
        if self.opacity_effect is None:
            self.opacity_effect = QGraphicsOpacityEffect()
            self.opacity_effect.setOpacity(0.0)
            self.window.setGraphicsEffect(self.opacity_effect)
    
    def animate_show(self, duration: int = 200, on_finished=None):
        """
        Show window with fade-in animation.
        
        Args:
            duration: Animation duration in milliseconds (default 200ms)
            on_finished: Callback when animation completes
        """
        if self.is_animating:
            return
        
        self.is_animating = True
        self.setup_opacity_effect()
        
        # Make sure window is visible before animating
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()
        
        # Create fade-in animation
        self.show_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.show_animation.setDuration(duration)
        self.show_animation.setStartValue(0.0)
        self.show_animation.setEndValue(1.0)
        self.show_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        def on_animation_finished():
            self.is_animating = False
            self.opacity_effect.setOpacity(1.0)
            if on_finished:
                on_finished()
        
        self.show_animation.finished.connect(on_animation_finished)
        self.show_animation.start()
    
    def animate_close(self, duration: int = 200, on_finished=None):
        """
        Close window with fade-out animation.
        
        Args:
            duration: Animation duration in milliseconds (default 200ms)
            on_finished: Callback when animation completes
        """
        if self.is_animating:
            return
        
        self.is_animating = True
        self.setup_opacity_effect()
        
        # Create fade-out animation
        self.close_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.close_animation.setDuration(duration)
        self.close_animation.setStartValue(1.0)
        self.close_animation.setEndValue(0.0)
        self.close_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        def on_animation_finished():
            self.is_animating = False
            self.window.hide()
            if on_finished:
                on_finished()
        
        self.close_animation.finished.connect(on_animation_finished)
        self.close_animation.start()
    
    def show_instant(self):
        """Show window instantly without animation."""
        self.setup_opacity_effect()
        self.opacity_effect.setOpacity(1.0)
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()
        self.is_animating = False


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


def show_prepared_window(window, duration: int = 200):
    """
    Show a prepared window with fade-in animation.
    
    This should be called after the window is fully prepared but before exec().
    
    Args:
        window: The main window widget
        duration: Animation duration in milliseconds (default 200ms)
    """
    # Ensure window is initially hidden and fully rendered
    if not hasattr(window, '_transition_manager'):
        window._transition_manager = WindowTransitionManager(window)
    
    # Defer animation to next event loop to ensure rendering is complete
    QTimer.singleShot(50, lambda: window._transition_manager.animate_show(duration=duration))


def show_window_with_animation(window, duration: int = 200, on_finished=None):
    """
    Show window with fade-in animation.
    
    Args:
        window: The window to show
        duration: Animation duration in milliseconds (default 200ms)
        on_finished: Callback when animation completes
    """
    if not hasattr(window, '_transition_manager'):
        window._transition_manager = WindowTransitionManager(window)
    
    QTimer.singleShot(0, lambda: window._transition_manager.animate_show(duration=duration, on_finished=on_finished))


def hide_window_with_animation(window, duration: int = 200, on_finished=None):
    """
    Hide window with fade-out animation.
    
    Args:
        window: The window to hide
        duration: Animation duration in milliseconds (default 200ms)
        on_finished: Callback when animation completes
    """
    if not hasattr(window, '_transition_manager'):
        window._transition_manager = WindowTransitionManager(window)
    
    window._transition_manager.animate_close(duration=duration, on_finished=on_finished)


# Alternative function name for compatibility
def animate_window_show(window, duration: int = 200, on_finished=None):
    """Alias for show_window_with_animation."""
    show_window_with_animation(window, duration=duration, on_finished=on_finished)


def animate_window_hide(window, duration: int = 200, on_finished=None):
    """Alias for hide_window_with_animation."""
    hide_window_with_animation(window, duration=duration, on_finished=on_finished)
