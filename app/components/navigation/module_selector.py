import time
from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from app.components.menus.module_menu import ModuleDropdownPopover
from app.config.theme import ACCENT, CARD_BORDER
from app.core.icons import render_pixmap


class AnimatedChevron(QWidget):
    """Smooth rotating chevron icon that transitions between 0 deg (down) and 180 deg (up)."""
    def __init__(self, size: int = 12, color: str = "#8f97a8", parent=None):
        super().__init__(parent)
        self._size = size
        self._color = color
        self._angle = 0.0
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self._anim = QPropertyAnimation(self, b"rotation")
        self._anim.setDuration(160)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

        self._pixmap = render_pixmap("chevron-down", (size, size), color=color)

    def get_rotation(self) -> float:
        return self._angle

    def set_rotation(self, angle: float):
        self._angle = angle
        self.update()

    rotation = Property(float, get_rotation, set_rotation)

    def set_open(self, is_open: bool, animate: bool = True):
        target = 180.0 if is_open else 0.0
        if not animate:
            self._anim.stop()
            self._angle = target
            self.update()
            return

        self._anim.stop()
        self._anim.setStartValue(self._angle)
        self._anim.setEndValue(target)
        self._anim.start()

    def paintEvent(self, event):
        if not self._pixmap or self._pixmap.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        cx = self.width() / 2.0
        cy = self.height() / 2.0
        painter.translate(cx, cy)
        painter.rotate(self._angle)
        painter.translate(-cx, -cy)
        painter.drawPixmap(0, 0, self._pixmap)
        painter.end()


class StartupModuleSelector(QFrame):
    """Button trigger displaying SVG icon, label, and dynamic chevron up/down."""
    def __init__(self, win, on_changed, parent=None):
        super().__init__(parent)
        self.win = win
        self.on_changed = on_changed
        self.current_id = win.settings.get("startup_module", "key-round")
        self._popover = None
        self._is_open = False
        self._close_time = 0.0

        self.setFixedHeight(26)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("SelectorTrigger")
        self._apply_style(is_active=False)

        self.lay = QHBoxLayout(self)
        self.lay.setContentsMargins(7, 2, 7, 2)
        self.lay.setSpacing(5)

        self.icon_lbl = QLabel()
        self.icon_lbl.setStyleSheet("background: transparent; border: none;")
        self.icon_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.lay.addWidget(self.icon_lbl)

        self.text_lbl = QLabel()
        self.text_lbl.setStyleSheet("color: #ffffff; font-size: 11.5px; font-weight: 600; background: transparent; border: none;")
        self.text_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.lay.addWidget(self.text_lbl)

        self.lay.addStretch(1)

        self.chevron_widget = AnimatedChevron(11, color="#8f97a8", parent=self)
        self.lay.addWidget(self.chevron_widget)

        self._refresh()

    def _apply_style(self, is_active=False):
        border_col = "#3b4354" if is_active else CARD_BORDER
        self.setStyleSheet(f"""
            QFrame#SelectorTrigger {{
                background-color: #161821;
                border: 1px solid {border_col};
                border-radius: 6px;
            }}
            QFrame#SelectorTrigger:hover {{
                border-color: #3b4354;
                background-color: #1a1e2a;
            }}
        """)


    def _refresh(self):
        all_sections = ["key-round", "prompt", "ai_model", "link", "command"]
        enabled = set(self.win.settings.get("enabled_sections", all_sections))
        saved_mod = self.win.settings.get("startup_module", "key-round")
        if saved_mod in enabled:
            self.current_id = saved_mod
        elif self.current_id not in enabled:
            order = self.win.settings.get("section_order", all_sections)
            valid = [k for k in order if k in enabled]
            self.current_id = valid[0] if valid else "key-round"
            self.win.settings["startup_module"] = self.current_id

        if self.current_id == "key-round":
            ic_name = "key-round"
            title = "API Keys"
        elif self.current_id == "prompt":
            ic_name = "prompt"
            title = "Prompts"
        elif self.current_id in ("ai_model", "sparkles-2"):
            ic_name = "ai_model"
            title = "AI Models"
        elif self.current_id == "link":
            ic_name = "link"
            title = "Links"
        else:
            ic_name = "command"
            title = "Commands"

        ic_pm = render_pixmap(ic_name, (14, 14), color="#ff8c5a")
        if ic_pm:
            self.icon_lbl.setPixmap(ic_pm)
        self.text_lbl.setText(title)

        fm = self.text_lbl.fontMetrics()
        txt_w = fm.horizontalAdvance(title)
        self.setFixedWidth(max(104, txt_w + 57))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            now = time.time()
            # If closed within 250ms by Qt popup dismissal, treat this click as collapsing
            if now - getattr(self, "_close_time", 0.0) < 0.25:
                self._is_open = False
                return

            if self._is_open:
                self._close_menu()
                return

            self._open_menu()
        super().mousePressEvent(event)

    def _toggle_menu(self):
        if self._is_open:
            self._close_menu()
        else:
            self._open_menu()

    def _close_menu(self):
        self._is_open = False
        self._close_time = time.time()
        if self._popover:
            p = self._popover
            self._popover = None
            p.close()
        self._on_popover_closed()

    def _open_menu(self):
        # Close other selector popover if open
        if hasattr(self.win, "settings_view"):
            sv = self.win.settings_view
            if hasattr(sv, "visible_modules_selector") and sv.visible_modules_selector is not None and sv.visible_modules_selector is not self:
                if getattr(sv.visible_modules_selector, "_is_open", False):
                    sv.visible_modules_selector._close_menu()

        self._is_open = True
        self._apply_style(is_active=True)
        self.chevron_widget.set_open(True)
        self._refresh()

        self._popover = ModuleDropdownPopover(
            current_module=self.current_id,
            win=self.win,
            on_choose=self._select_option,
            on_close=self._on_popover_closed,
            parent=self.win
        )
        self._popover.adjustSize()
        top_pos = self.mapToGlobal(self.rect().topLeft())
        pop_w = self._popover.width()
        pop_h = self._popover.height()
        x = top_pos.x() - (pop_w - self.width()) + 6
        y = top_pos.y() - pop_h - 4

        # Bounds check with window top
        win = self.window()
        if win is not None:
            win_top = win.mapToGlobal(win.rect().topLeft()).y()
            if y < win_top + 4:
                y = win_top + 4

        self._popover.move(x, y)
        self._popover.show()

    def _select_option(self, mod_id):
        self.current_id = mod_id
        self._is_open = False
        self._popover = None
        self._close_time = time.time()
        self._apply_style(is_active=False)
        self.chevron_widget.set_open(False)
        self._refresh()
        self.on_changed(mod_id)

    def _on_popover_closed(self):
        self._is_open = False
        self._close_time = time.time()
        self._popover = None
        self._apply_style(is_active=False)
        self.chevron_widget.set_open(False)
        self._refresh()


class VisibleModulesSelector(QFrame):
    """Button trigger displaying layers icon, selected module count, and dynamic chevron up/down."""
    def __init__(self, win, on_changed, parent=None):
        super().__init__(parent)
        self.win = win
        self.on_changed = on_changed
        self._popover = None
        self._is_open = False
        self._close_time = 0.0

        self.setFixedHeight(26)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("SelectorTrigger")
        self._apply_style(is_active=False)

        self.lay = QHBoxLayout(self)
        self.lay.setContentsMargins(7, 2, 7, 2)
        self.lay.setSpacing(5)

        self.icon_lbl = QLabel()
        self.icon_lbl.setStyleSheet("background: transparent; border: none;")
        self.icon_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.lay.addWidget(self.icon_lbl)

        self.text_lbl = QLabel()
        self.text_lbl.setStyleSheet("color: #ffffff; font-size: 11.5px; font-weight: 600; background: transparent; border: none;")
        self.text_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.lay.addWidget(self.text_lbl)

        self.lay.addStretch(1)

        self.chevron_widget = AnimatedChevron(11, color="#8f97a8", parent=self)
        self.lay.addWidget(self.chevron_widget)

        self._refresh()

    def _apply_style(self, is_active=False):
        border_col = "#3b4354" if is_active else CARD_BORDER
        self.setStyleSheet(f"""
            QFrame#SelectorTrigger {{
                background-color: #161821;
                border: 1px solid {border_col};
                border-radius: 6px;
            }}
            QFrame#SelectorTrigger:hover {{
                border-color: #3b4354;
                background-color: #1a1e2a;
            }}
        """)

    def _refresh(self):
        all_sections = ["key-round", "prompt", "ai_model", "link", "command"]
        enabled = self.win.settings.get("enabled_sections", all_sections)
        count = len(enabled)

        # SVG icon: eye in orange color
        ic_pm = render_pixmap("eye", (14, 14), color="#ff8c5a")
        if ic_pm:
            self.icon_lbl.setPixmap(ic_pm)

        if count >= len(all_sections):
            text_str = f"All ({len(all_sections)})"
        else:
            text_str = f"{count} Selected"
        self.text_lbl.setText(text_str)

        fm = self.text_lbl.fontMetrics()
        txt_w = fm.horizontalAdvance(text_str)
        self.setFixedWidth(max(104, txt_w + 57))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            now = time.time()
            if now - getattr(self, "_close_time", 0.0) < 0.25:
                self._is_open = False
                return

            if self._is_open:
                self._close_menu()
                return

            self._open_menu()
        super().mousePressEvent(event)

    def _toggle_menu(self):
        if self._is_open:
            self._close_menu()
        else:
            self._open_menu()

    def _close_menu(self):
        self._is_open = False
        self._close_time = time.time()
        if self._popover:
            p = self._popover
            self._popover = None
            p.close()
        self._on_popover_closed()

    def _open_menu(self):
        # Close other selector popover if open
        if hasattr(self.win, "settings_view"):
            sv = self.win.settings_view
            if hasattr(sv, "module_selector") and sv.module_selector is not None and sv.module_selector is not self:
                if getattr(sv.module_selector, "_is_open", False):
                    sv.module_selector._close_menu()

        from app.components.menus.module_menu import VisibleModulesDropdownPopover
        self._is_open = True
        self._apply_style(is_active=True)
        self.chevron_widget.set_open(True)
        self._refresh()

        self._popover = VisibleModulesDropdownPopover(
            win=self.win,
            on_modules_changed=self._on_modules_changed,
            on_close=self._on_popover_closed,
            parent=self.win
        )
        self._popover.adjustSize()
        top_pos = self.mapToGlobal(self.rect().topLeft())
        pop_w = self._popover.width()
        pop_h = self._popover.height()
        x = top_pos.x() - (pop_w - self.width()) + 6
        y = top_pos.y() - pop_h - 4

        # Bounds check with window top
        win = self.window()
        if win is not None:
            win_top = win.mapToGlobal(win.rect().topLeft()).y()
            if y < win_top + 4:
                y = win_top + 4

        self._popover.move(x, y)
        self._popover.show()

    def _on_modules_changed(self, enabled_list):
        self._refresh()
        self.on_changed(enabled_list)

    def _on_popover_closed(self):
        self._is_open = False
        self._close_time = time.time()
        self._popover = None
        self._apply_style(is_active=False)
        self.chevron_widget.set_open(False)
        self._refresh()
