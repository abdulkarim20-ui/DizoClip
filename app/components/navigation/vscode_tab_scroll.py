from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QFrame, QScrollArea, QWidget


class VSCodeTabScrollArea(QScrollArea):
    """
    Horizontal scroll area modeled after the VS Code tab bar:
    - Automatically enables smooth horizontal scrolling when tabs overflow container width.
    - Captures vertical mouse wheel events and translates them into horizontal scrolling.
    - Minimalist 3px scrollbar that blends cleanly with dark theme.
    - Helper method to auto-scroll active/new tabs into view.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:horizontal {
                height: 3px;
                background: rgba(0, 0, 0, 0.25);
                margin: 0px;
                border: none;
                border-radius: 1px;
            }
            QScrollBar::handle:horizontal {
                background: #333d52;
                border-radius: 1px;
                min-width: 24px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #ff773d;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
                height: 0px;
                border: none;
                background: transparent;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: transparent;
            }
        """)

        # Install wheel event filter on viewport
        if self.viewport():
            self.viewport().installEventFilter(self)

    def setWidget(self, widget: QWidget):
        super().setWidget(widget)
        if widget:
            widget.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            self.wheelEvent(event)
            return True
        elif event.type() == QEvent.ChildAdded:
            # Install filter on dynamically added tab buttons
            child = getattr(event, "child", lambda: None)()
            if child and isinstance(child, QWidget):
                child.installEventFilter(self)
        return super().eventFilter(obj, event)

    def wheelEvent(self, event):
        # Convert vertical wheel motion into horizontal scrolling
        delta = event.angleDelta().y()
        if delta == 0:
            delta = event.angleDelta().x()
        if delta != 0:
            hbar = self.horizontalScrollBar()
            # Standard mouse notch is 120 -> scroll ~45px per notch
            step = int(- (delta / 120.0) * 45)
            hbar.setValue(hbar.value() + step)
            event.accept()
            return
        super().wheelEvent(event)

    def ensure_tab_visible(self, widget: QWidget):
        """Scrolls the horizontal view so that the given tab widget is visible."""
        if widget:
            self.ensureWidgetVisible(widget, 10, 0)
