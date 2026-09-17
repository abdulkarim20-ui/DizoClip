from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.config.theme import CARD_BORDER
from app.core.icons import render_pixmap

SLIM_MENU_SCROLLBAR = """
    QScrollArea {
        background: transparent;
        border: none;
    }
    QScrollBar:vertical {
        border: none;
        background: transparent;
        width: 4px;
        margin: 0px 1px 0px 0px;
        border-radius: 2px;
    }
    QScrollBar::handle:vertical {
        background: #333d4e;
        min-height: 20px;
        border-radius: 2px;
    }
    QScrollBar::handle:vertical:hover {
        background: #505c73;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
        background: none;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
    }
"""


class ModuleOptionWidget(QPushButton):
    """Dropdown item with SVG icon, text label, and accent checkmark."""
    def __init__(self, key_id, label, icon_name, is_selected, win, on_select, parent=None):
        super().__init__(parent)
        self.key_id = key_id
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(34)

        if is_selected:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #202433;
                    border: none;
                    border-radius: 8px;
                    text-align: left;
                    padding-left: 10px;
                }
                QPushButton:hover {
                    background-color: #272d3f;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    border-radius: 8px;
                    text-align: left;
                    padding-left: 10px;
                }
                QPushButton:hover {
                    background-color: #1e222e;
                }
            """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 0, 10, 0)
        lay.setSpacing(8)

        icon_pm = render_pixmap(icon_name, (14, 14), color="#e2e8f0" if is_selected else "#7a8292")
        icon_lbl = QLabel()
        if icon_pm:
            icon_lbl.setPixmap(icon_pm)
        icon_lbl.setFixedSize(14, 14)
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(icon_lbl)

        txt_lbl = QLabel(label)
        txt_lbl.setStyleSheet(f"""
            color: {'#ffffff' if is_selected else '#8f97a8'};
            font-size: 12.5px;
            font-weight: {'700' if is_selected else '500'};
            background: transparent;
            border: none;
        """)
        lay.addWidget(txt_lbl)
        lay.addStretch(1)

        if is_selected:
            chk_pm = render_pixmap("check", (13, 13), color="#e2e8f0")
            chk_lbl = QLabel()
            if chk_pm:
                chk_lbl.setPixmap(chk_pm)
            chk_lbl.setFixedSize(13, 13)
            chk_lbl.setStyleSheet("background: transparent; border: none;")
            lay.addWidget(chk_lbl)

        self.clicked.connect(lambda: on_select(key_id))


class ModuleDropdownPopover(QFrame):
    def __init__(self, current_module, win, on_choose, on_close, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(166)
        self._on_close = on_close

        card = QFrame(self)
        card.setObjectName("ModuleCard")
        card.setStyleSheet(f"""
            QFrame#ModuleCard {{
                background-color: #161821;
                border: 1px solid {CARD_BORDER};
                border-radius: 12px;
            }}
        """)

        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)

        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.addWidget(card)

        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(2, 2, 2, 2)

        scroll = QScrollArea(card)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet(SLIM_MENU_SCROLLBAR)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        menu_lay = QVBoxLayout(content)
        menu_lay.setContentsMargins(4, 4, 4, 4)
        menu_lay.setSpacing(3)

        all_sections = ["key-round", "prompt", "ai_model", "link", "command"]
        enabled = set(win.settings.get("enabled_sections", all_sections))
        order = list(win.settings.get("section_order", all_sections))
        for item in all_sections:
            if item not in order:
                order.append(item)

        meta_map = {
            "key-round": ("API Keys", "key-round"),
            "prompt": ("Prompts", "prompt"),
            "ai_model": ("AI Models", "ai_model"),
            "sparkles-2": ("AI Models", "ai_model"),
            "link": ("Links", "link"),
            "command": ("Commands", "command"),
        }

        visible = [mid for mid in order if mid in enabled]
        if not visible:
            visible = ["key-round"]

        for mid in visible:
            label, ic = meta_map.get(mid, (mid, "key-round"))
            btn = ModuleOptionWidget(
                mid, label, ic,
                is_selected=(mid == current_module),
                win=win,
                on_select=lambda sid: (self.close(), on_choose(sid))
            )
            menu_lay.addWidget(btn)

        scroll.setWidget(content)

        # Cap height so exactly 4 options are fully visible; 5th requires scrolling
        count = len(visible)
        h_needed = count * 34 + max(0, count - 1) * 3 + 8
        scroll.setFixedHeight(min(153, h_needed))
        card_lay.addWidget(scroll)

    def hideEvent(self, event):
        cb = self._on_close
        self._on_close = None
        if cb:
            cb()
        super().hideEvent(event)


class VisibleModuleCheckItem(QPushButton):
    """Checklist item with SVG icon, text label, and accent checkmark toggle."""
    def __init__(self, key_id, label, icon_name, is_checked, on_toggle, parent=None):
        super().__init__(parent)
        self.key_id = key_id
        self.is_checked = is_checked
        self.on_toggle = on_toggle
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(34)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 0, 10, 0)
        lay.setSpacing(8)

        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(14, 14)
        self.icon_lbl.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(self.icon_lbl)

        self.txt_lbl = QLabel(label)
        self.txt_lbl.setStyleSheet("background: transparent; border: none; font-size: 12.5px;")
        lay.addWidget(self.txt_lbl)
        lay.addStretch(1)

        self.chk_lbl = QLabel()
        self.chk_lbl.setFixedSize(14, 14)
        self.chk_lbl.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(self.chk_lbl)

        self._update_appearance()
        self.clicked.connect(self._handle_click)

    def set_checked(self, checked: bool):
        self.is_checked = checked
        self._update_appearance()

    def _update_appearance(self):
        if self.is_checked:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #202433;
                    border: none;
                    border-radius: 8px;
                    text-align: left;
                    padding-left: 10px;
                }
                QPushButton:hover {
                    background-color: #272d3f;
                }
            """)
            self.txt_lbl.setStyleSheet("color: #ffffff; font-weight: 700; font-size: 12.5px;")
            icon_pm = render_pixmap(self.key_id, (14, 14), color="#e2e8f0")
            if icon_pm:
                self.icon_lbl.setPixmap(icon_pm)
            chk_pm = render_pixmap("check", (13, 13), color="#e2e8f0")
            if chk_pm:
                self.chk_lbl.setPixmap(chk_pm)
            else:
                self.chk_lbl.setText("✓")
                self.chk_lbl.setStyleSheet("color: #e2e8f0; font-weight: 700; font-size: 12px;")
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    border-radius: 8px;
                    text-align: left;
                    padding-left: 10px;
                }
                QPushButton:hover {
                    background-color: #1e222e;
                }
            """)
            self.txt_lbl.setStyleSheet("color: #7a8292; font-weight: 500; font-size: 12.5px;")
            icon_pm = render_pixmap(self.key_id, (14, 14), color="#7a8292")
            if icon_pm:
                self.icon_lbl.setPixmap(icon_pm)
            self.chk_lbl.clear()

    def _handle_click(self):
        new_state = not self.is_checked
        self.on_toggle(self.key_id, new_state, self)


class VisibleModulesDropdownPopover(QFrame):
    """Multi-select checklist dropdown for visible modules in Settings."""
    def __init__(self, win, on_modules_changed, on_close, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(166)
        self.win = win
        self.on_modules_changed = on_modules_changed
        self._on_close = on_close

        card = QFrame(self)
        card.setObjectName("ModuleCard")
        card.setStyleSheet(f"""
            QFrame#ModuleCard {{
                background-color: #161821;
                border: 1px solid {CARD_BORDER};
                border-radius: 12px;
            }}
        """)

        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)

        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.addWidget(card)

        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(2, 2, 2, 2)

        scroll = QScrollArea(card)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet(SLIM_MENU_SCROLLBAR)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        menu_lay = QVBoxLayout(content)
        menu_lay.setContentsMargins(4, 4, 4, 4)
        menu_lay.setSpacing(3)

        all_sections = ["key-round", "prompt", "ai_model", "link", "command"]
        order = list(win.settings.get("section_order", all_sections))
        for item in all_sections:
            if item not in order:
                order.append(item)

        meta_map = {
            "key-round": ("API Keys", "key-round"),
            "prompt": ("Prompts", "prompt"),
            "ai_model": ("AI Models", "ai_model"),
            "sparkles-2": ("AI Models", "ai_model"),
            "link": ("Links", "link"),
            "command": ("Commands", "command"),
        }

        self.items_map = {}
        for mid in order:
            label, ic = meta_map.get(mid, (mid, "key-round"))
            enabled_list = win.settings.get("enabled_sections", all_sections)
            is_chk = mid in enabled_list
            item_widget = VisibleModuleCheckItem(
                mid, label, ic,
                is_checked=is_chk,
                on_toggle=self._on_item_toggle
            )
            self.items_map[mid] = item_widget
            menu_lay.addWidget(item_widget)

        scroll.setWidget(content)

        # Cap height so exactly 4 options are fully visible; 5th requires scrolling
        count = len(order)
        h_needed = count * 34 + max(0, count - 1) * 3 + 8
        scroll.setFixedHeight(min(153, h_needed))
        card_lay.addWidget(scroll)

    def _on_item_toggle(self, mid, new_checked, widget):
        all_sections = ["key-round", "prompt", "ai_model", "link", "command"]
        enabled = list(self.win.settings.get("enabled_sections", all_sections))
        if not new_checked:
            if len(enabled) <= 1 and mid in enabled:
                # Cannot uncheck the last remaining enabled module!
                widget.set_checked(True)
                return
            if mid in enabled:
                enabled.remove(mid)
        else:
            if mid not in enabled:
                enabled.append(mid)

        self.win.settings["enabled_sections"] = enabled
        widget.set_checked(new_checked)
        self.on_modules_changed(enabled)

    def hideEvent(self, event):
        cb = self._on_close
        self._on_close = None
        if cb:
            cb()
        super().hideEvent(event)
