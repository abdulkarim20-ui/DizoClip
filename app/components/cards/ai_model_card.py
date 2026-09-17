import time
from typing import Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.components.buttons.icon_button import icon_button
from app.components.cards.base_card import BaseCard
from app.components.cards.prompt_card import PromptPreviewWidget
from app.components.labels.elided_label import ElidedLabel
from app.components.menus.action_menu import ActionMenuPopup
from app.config.constants import AI_MODEL_CARD_H, BADGE_COLORS
from app.config.theme import font_css
from app.core.icons import render_pixmap


class LanguageOptionItem(QPushButton):
    """Dropdown item for snippet language with label and accent checkmark."""
    def __init__(self, lang: str, is_selected: bool, on_select, parent=None):
        super().__init__(parent)
        self.lang = lang
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(28)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 0, 8, 0)
        lay.setSpacing(6)

        txt_lbl = QLabel(lang)
        txt_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        lay.addWidget(txt_lbl)

        lay.addStretch(1)

        if is_selected:
            chk_lbl = QLabel()
            chk_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            chk_pm = render_pixmap("check", (12, 12), color="#ffffff")
            if chk_pm:
                chk_lbl.setPixmap(chk_pm)
            lay.addWidget(chk_lbl)

            self.setStyleSheet("""
                QPushButton {
                    background-color: #222634;
                    border: none;
                    border-radius: 6px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #292f42;
                }
            """)
            txt_lbl.setStyleSheet(font_css("caption", color="#ffffff"))
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    border-radius: 6px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #1e222e;
                }
            """)
            txt_lbl.setStyleSheet(font_css("subtext", color="#94a3b8"))

        self.clicked.connect(lambda: on_select(lang))


class LanguageDropdownPopup(QFrame):
    """Popup menu displaying available snippet languages with selection checkmark."""
    def __init__(self, langs: List[str], current_lang: str, on_select, on_close, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(138)
        self._on_close = on_close

        card = QFrame(self)
        card.setObjectName("LangPopupCard")
        card.setStyleSheet("""
            QFrame#LangPopupCard {
                background-color: #161822;
                border: 1px solid #282e3f;
                border-radius: 8px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(18)
        shadow.setColor(QColor(0, 0, 0, 75))
        shadow.setOffset(0, 3)
        card.setGraphicsEffect(shadow)

        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.addWidget(card)

        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(3, 3, 3, 3)
        card_lay.setSpacing(2)

        scroll = QScrollArea(card)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 4px;
                border-radius: 2px;
            }
            QScrollBar::handle:vertical {
                background: #333d4e;
                min-height: 16px;
                border-radius: 2px;
            }
            QScrollBar::handle:vertical:hover { background: #505c73; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        items_lay = QVBoxLayout(content)
        items_lay.setContentsMargins(0, 0, 0, 0)
        items_lay.setSpacing(2)

        for lang in langs:
            item = LanguageOptionItem(
                lang=lang,
                is_selected=(lang == current_lang),
                on_select=lambda l: (self.close(), on_select(l)),
                parent=content
            )
            items_lay.addWidget(item)

        scroll.setWidget(content)

        count = len(langs)
        h_needed = count * 28 + max(0, count - 1) * 2
        scroll.setFixedHeight(min(148, h_needed))
        card_lay.addWidget(scroll)

    def hideEvent(self, event):
        cb = self._on_close
        self._on_close = None
        if cb:
            cb()
        super().hideEvent(event)


class LanguageDropdownTrigger(QFrame):
    """Compact trigger button matching model badge font size with SVG double chevron."""
    def __init__(self, current_lang: str, on_toggle, parent=None):
        super().__init__(parent)
        self.on_toggle = on_toggle
        self.current_lang = current_lang
        self.setFixedHeight(22)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("LangTrigger")
        self._apply_style(is_active=False)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 0, 6, 0)
        lay.setSpacing(4)

        self.text_lbl = QLabel(current_lang)
        self.text_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.text_lbl.setStyleSheet(font_css("caption", color="#ffffff", extra="background: transparent; border: none;"))
        lay.addWidget(self.text_lbl)

        self.chevron_lbl = QLabel()
        self.chevron_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.chevron_lbl.setStyleSheet("background: transparent; border: none;")
        ch_pm = render_pixmap("chevrons-up-down", (12, 12), color="#8f97a8")
        if ch_pm:
            self.chevron_lbl.setPixmap(ch_pm)
        lay.addWidget(self.chevron_lbl)

    def set_language(self, lang: str):
        self.current_lang = lang
        self.text_lbl.setText(lang)
        self.adjustSize()

    def _apply_style(self, is_active=False):
        border_col = "#ff8c5a" if is_active else "#2b3244"
        bg_col = "#202535" if is_active else "#1c202d"
        self.setStyleSheet(f"""
            QFrame#LangTrigger {{
                background-color: {bg_col};
                border: 1px solid {border_col};
                border-radius: 5px;
            }}
            QFrame#LangTrigger:hover {{
                border-color: #3d4760;
                background-color: #242a3c;
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.on_toggle:
                self.on_toggle()
        super().mousePressEvent(event)


class AIModelCard(BaseCard):
    """
    AI Model card matching Prompt card aesthetic:
    - Model name badge
    - Clutter-free snippet language dropdown trigger with SVG chevrons
    - Copy button for active snippet with animated checkmark
    - 3-dots actions menu
    - Code snippet preview
    """
    CARD_HEIGHT = AI_MODEL_CARD_H

    def __init__(self, model: Dict, win, on_copy, on_edit, on_delete, on_toggle=None, parent=None):
        super().__init__(win, parent)
        self.model = model
        self.win = win
        self.on_copy = on_copy
        self.on_edit = on_edit
        self.on_delete = on_delete

        snippets = model.get("snippets", {})
        self.available_langs = list(snippets.keys()) if snippets else ["Python"]
        self.selected_lang = self.available_langs[0]
        self._popover = None
        self._is_open = False
        self._close_time = 0.0

        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(14, 10, 14, 10)
        main_lay.setSpacing(5)

        # 1. Top row: Model Badge + Language Dropdown Trigger + Copy Button + 3-Dot Menu
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(6)

        color = model.get("color", BADGE_COLORS[0])
        model_name = model.get("name", "Unnamed Model")
        title = ElidedLabel(model_name)
        title.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        title.setStyleSheet(f"""
            background-color: {color};
            color: #0b0d10;
            {font_css("caption")}
            padding: 2px 7px;
            border-radius: 5px;
        """)
        title.setToolTip(model_name)
        top_row.addWidget(title, 0, Qt.AlignVCenter)

        # Dropdown trigger instead of multiple pill buttons
        self.lang_trigger = LanguageDropdownTrigger(
            current_lang=self.selected_lang,
            on_toggle=self._toggle_lang_dropdown,
            parent=self
        )
        top_row.addWidget(self.lang_trigger, 0, Qt.AlignVCenter)

        top_row.addStretch(1)

        # Copy button (copies current active snippet)
        self.copy_btn = icon_button(win.icons.get("copy"), "⧉", f"Copy {self.selected_lang} snippet")
        self.copy_btn.clicked.connect(self._handle_copy)

        self.menu_btn = icon_button(win.icons.get("ellipsis"), "⋮", "More actions")
        self.menu_btn.setProperty("buttonRole", "menu")
        self.menu_btn.clicked.connect(self._open_dropdown)

        top_row.addWidget(self.copy_btn, 0, Qt.AlignVCenter)
        top_row.addWidget(self.menu_btn, 0, Qt.AlignVCenter)
        main_lay.addLayout(top_row)

        # 2. Preview Area: Clean code snippet preview
        initial_code = snippets.get(self.selected_lang, "")
        self.preview = PromptPreviewWidget(initial_code, icon_pm=None)
        main_lay.addWidget(self.preview)

        self._refresh()

    def _toggle_lang_dropdown(self):
        now = time.time()
        if now - getattr(self, "_close_time", 0.0) < 0.25:
            self._is_open = False
            return

        if self._is_open:
            self._close_lang_dropdown()
            return

        self._open_lang_dropdown()

    def _close_lang_dropdown(self):
        self._is_open = False
        self._close_time = time.time()
        if self._popover:
            p = self._popover
            self._popover = None
            p.close()
        self._on_popover_closed()

    def _on_popover_closed(self):
        self._is_open = False
        self._close_time = time.time()
        self._popover = None
        self.lang_trigger._apply_style(is_active=False)

    def _open_lang_dropdown(self):
        self._is_open = True
        self.lang_trigger._apply_style(is_active=True)

        self._popover = LanguageDropdownPopup(
            langs=self.available_langs,
            current_lang=self.selected_lang,
            on_select=self._select_language,
            on_close=self._on_popover_closed,
            parent=self.win
        )
        self._popover.adjustSize()

        trigger_top_pos = self.lang_trigger.mapToGlobal(self.lang_trigger.rect().topLeft())
        pop_w = self._popover.width()
        pop_h = self._popover.height()

        x = trigger_top_pos.x()
        y = trigger_top_pos.y() + self.lang_trigger.height() + 4

        # Bounds check within window bounds
        win = self.window()
        if win is not None:
            win_rect = win.rect()
            win_bottom = win.mapToGlobal(win_rect.bottomLeft()).y()
            win_right = win.mapToGlobal(win_rect.topRight()).x()

            # If opening below would clip below window bottom, flip to open above
            if y + pop_h > win_bottom - 8:
                y = trigger_top_pos.y() - pop_h - 4

            if x + pop_w > win_right - 8:
                x = win_right - pop_w - 8

        self._popover.move(x, y)
        self._popover.show()

    def _select_language(self, lang: str):
        self.selected_lang = lang
        self._is_open = False
        self._close_time = time.time()
        self.lang_trigger.set_language(lang)
        self.lang_trigger._apply_style(is_active=False)

        snippets = self.model.get("snippets", {})
        code = snippets.get(lang, "")
        self.preview.setText(code)
        self.copy_btn.setToolTip(f"Copy {lang} snippet")

    def _handle_copy(self):
        snippets = self.model.get("snippets", {})
        val = snippets.get(self.selected_lang, "")
        self.on_copy(val, self.copy_btn)

    def _open_dropdown(self):
        menu = ActionMenuPopup(
            self.win,
            on_edit=lambda: self.on_edit(self.model),
            on_delete=lambda: self.on_delete(self.model),
            parent=self.win
        )
        menu.show_under(self.menu_btn)

    def _refresh(self):
        self.copy_btn.setVisible(self._hovered)

