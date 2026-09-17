from PySide6.QtCore import (
    QEvent,
    QObject,
    Qt,
    QTimer,
)
from PySide6.QtWidgets import QApplication


class _SearchInputFilter(QObject):
    """Handles keyboard events like Escape on the search input."""
    def __init__(self, controller):
        super().__init__(controller)
        self.controller = controller

    def eventFilter(self, watched, event):
        if watched == self.controller.list_view.search:
            if event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_Escape:
                    self.controller.close()
                    return True
        return super().eventFilter(watched, event)


class _SearchOutsideClickFilter(QObject):
    """
    Dismisses search input when the user clicks anywhere outside it,
    provided that no search text has been entered.
    """
    def __init__(self, controller):
        super().__init__(controller)
        self.controller = controller

    def eventFilter(self, watched, event):
        if event.type() == QEvent.MouseButtonPress:
            if self.controller.is_open:
                lv = self.controller.list_view
                search_widget = lv.search
                search_btn = getattr(lv, "search_btn", None)
                add_btn = getattr(lv, "add_btn", None)

                # Check if click is inside search widget itself, search button, or add button
                is_inside = False
                w = watched
                while w is not None:
                    if (
                        w is search_widget
                        or (search_btn is not None and w is search_btn)
                        or (add_btn is not None and w is add_btn)
                    ):
                        is_inside = True
                        break
                    try:
                        w = w.parent()
                    except Exception:
                        break

                if not is_inside:
                    # If empty, dismiss search when clicking outside
                    if not lv.search.text().strip():
                        QTimer.singleShot(0, self.controller.close)
        return super().eventFilter(watched, event)


class SearchController(QObject):
    """
    Manages the search bar lifecycle, dynamic sizing,
    outside-click detection, and instant show/hide without animations.
    """
    def __init__(self, list_view):
        super().__init__(list_view)
        self.list_view = list_view
        self._is_open = False
        self._switching = False

        # Setup event filter for search input
        self._input_filter = _SearchInputFilter(self)
        self.list_view.search.installEventFilter(self._input_filter)

        # Global outside click filter
        self._outside_filter = _SearchOutsideClickFilter(self)
        qapp = QApplication.instance()
        if qapp:
            qapp.installEventFilter(self._outside_filter)

    @property
    def is_open(self) -> bool:
        return self._is_open

    @property
    def is_switching(self) -> bool:
        return self._switching

    def calculate_target_width(self) -> int:
        """
        Calculate the search width from the actual header geometry.
        Explicitly reserves room for:
        - section title
        - count badge
        - search/close button
        - add button
        """
        available = self.list_view.header_widget.contentsRect().width()
        if available <= 0:
            available = self.list_view.width() - 32
        if available <= 0:
            available = 320

        title_width = (
            self.list_view.title_lbl.sizeHint().width()
            + self.list_view.count.sizeHint().width()
            + 8
        )
        search_btn_width = self.list_view.search_btn.sizeHint().width() if hasattr(self.list_view, "search_btn") else 28
        add_btn_width = self.list_view.add_btn.sizeHint().width() if hasattr(self.list_view, "add_btn") else 28
        spacing = 8 * 3
        safety = 8

        target = available - title_width - search_btn_width - add_btn_width - spacing - safety
        return max(120, min(target, 220))

    def open(self, duration: int = 0, on_finished=None):
        """Directly displays the search input with calculated target width and focuses it."""
        self._is_open = True
        target_width = self.calculate_target_width()

        self.list_view.search.setMinimumWidth(min(120, target_width))
        self.list_view.search.setMaximumWidth(target_width)
        self.list_view.search.show()
        if hasattr(self.list_view, "search_btn"):
            self.list_view.search_btn.setToolTip("Close search")
        if hasattr(self.list_view, "clear_action"):
            self.list_view.clear_action.setVisible(bool(self.list_view.search.text().strip()))
        self.list_view.search.setFocus()

        if callable(on_finished):
            on_finished()

    def close(
        self,
        duration: int = 0,
        on_finished=None,
        clear_text: bool = True,
        rebuild: bool = True,
    ):
        """Directly hides the search input and inner clear action."""
        if not self._is_open:
            if callable(on_finished):
                on_finished()
            return

        self._is_open = False
        self.list_view.search.hide()
        self.list_view.search.setMinimumWidth(0)
        self.list_view.search.setMaximumWidth(0)
        if hasattr(self.list_view, "clear_action"):
            self.list_view.clear_action.setVisible(False)
        if hasattr(self.list_view, "search_btn"):
            self.list_view.search_btn.setToolTip("Search")

        if clear_text:
            self.list_view.search.blockSignals(True)
            self.list_view.search.clear()
            self.list_view.search.blockSignals(False)

        if rebuild:
            self.list_view.rebuild()

        if callable(on_finished):
            on_finished()

    def toggle(self):
        """Toggles search between open and closed states."""
        if self._is_open:
            self.close()
        else:
            self.open()

    def switch_section(self, tab_id: str, apply_section_fn):
        """Directly updates section content while maintaining open state if search was active."""
        was_open = self._is_open
        apply_section_fn(tab_id)
        if was_open:
            self.open()

    def leave_list_view(self, on_finished=None):
        """Directly closes search when navigating out of list view."""
        if self._is_open:
            self.close(clear_text=False, rebuild=False)

        if callable(on_finished):
            on_finished()
