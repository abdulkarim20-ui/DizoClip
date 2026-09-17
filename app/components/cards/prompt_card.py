from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.components.buttons.icon_button import icon_button
from app.components.cards.base_card import BaseCard
from app.components.labels.elided_label import ElidedLabel
from app.components.menus.action_menu import ActionMenuPopup
from app.config.constants import BADGE_COLORS, PROMPT_CARD_H
from app.config.theme import font_css
from app.core.icons import render_pixmap


class PromptPreviewWidget(QWidget):
    """
    Two-line prompt preview with an icon on line 1 and full-width flowing text on line 2.
    """
    def __init__(self, text: str, icon_pm: Optional[QPixmap] = None, parent=None):
        super().__init__(parent)
        self._raw_text = text
        self._icon_pm = icon_pm
        self.setFixedHeight(32)

        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(2)

        self.row1 = QHBoxLayout()
        self.row1.setContentsMargins(0, 0, 0, 0)
        self.row1.setSpacing(6)

        if self._icon_pm is not None:
            self.icon_lbl = QLabel()
            self.icon_lbl.setPixmap(self._icon_pm)
            self.icon_lbl.setFixedSize(13, 13)
            self.icon_lbl.setStyleSheet("background: transparent; border: none;")
            self.row1.addWidget(self.icon_lbl, 0, Qt.AlignVCenter)

        self.line1_lbl = QLabel()
        self.line1_lbl.setStyleSheet(font_css("subtext", color="#7a8292", extra="background: transparent; border: none;"))
        self.row1.addWidget(self.line1_lbl, 1, Qt.AlignVCenter)
        self.lay.addLayout(self.row1)

        self.line2_lbl = QLabel()
        self.line2_lbl.setStyleSheet(font_css("subtext", color="#7a8292", extra="background: transparent; border: none;"))
        self.lay.addWidget(self.line2_lbl)

    def setText(self, text: str):
        self._raw_text = text
        self._update_lines()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_lines()

    def _update_lines(self):
        w = self.width()
        if w <= 20:
            return

        raw = (self._raw_text or "").strip()
        if not raw:
            self.line1_lbl.setText("")
            self.line2_lbl.setText("")
            self.line2_lbl.setVisible(False)
            return

        fm = self.fontMetrics()
        icon_w = (13 + 6) if self._icon_pm is not None else 0
        w1 = max(10, w - icon_w)
        w2 = max(10, w)

        lines = [l.strip() for l in raw.split("\n") if l.strip()]
        if len(lines) >= 2:
            self.line1_lbl.setText(fm.elidedText(lines[0], Qt.ElideRight, w1))
            self.line2_lbl.setText(fm.elidedText(lines[1], Qt.ElideRight, w2))
            self.line2_lbl.setVisible(True)
            return

        clean = " ".join(raw.split())
        words = clean.split(" ")
        line1 = ""
        rem_idx = len(words)
        for i, word in enumerate(words):
            candidate = (line1 + " " + word).strip()
            if fm.horizontalAdvance(candidate) <= w1:
                line1 = candidate
            else:
                rem_idx = i
                break

        if not line1:
            line1 = fm.elidedText(words[0], Qt.ElideRight, w1)
            rem_idx = 1

        self.line1_lbl.setText(line1)

        if rem_idx < len(words):
            rem_text = " ".join(words[rem_idx:]).strip()
            line2 = fm.elidedText(rem_text, Qt.ElideRight, w2)
            self.line2_lbl.setText(line2)
            self.line2_lbl.setVisible(True)
        else:
            self.line2_lbl.setText("")
            self.line2_lbl.setVisible(False)


class PromptCard(BaseCard):
    """Prompt snippet card with astroid icon on line 1 and full-width flow on line 2."""
    CARD_HEIGHT = PROMPT_CARD_H

    def __init__(self, prompt, win, on_copy, on_edit, on_delete, on_toggle=None, parent=None):
        super().__init__(win, parent)
        self.prompt = prompt
        self.on_copy = on_copy
        self.on_edit = on_edit
        self.on_delete = on_delete

        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(14, 12, 14, 12)
        main_lay.setSpacing(6)

        # Top row: Label badge at top left, copy and 3-dot menu on right
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(4)

        color = prompt.get("color", BADGE_COLORS[0])
        title_text = prompt.get("name") or prompt.get("title", "")
        title = ElidedLabel(title_text)
        title.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        title.setStyleSheet(f"""
            background-color: {color};
            color: #0b0d10;
            {font_css("caption")}
            padding: 2px 8px;
            border-radius: 5px;
        """)
        title.setToolTip(title_text)
        top_row.addWidget(title, 0, Qt.AlignVCenter)

        # Action Buttons
        self.copy_btn = icon_button(win.icons.get("copy"), "⧉", "Copy prompt")
        self.copy_btn.clicked.connect(lambda: on_copy(self.prompt, self.copy_btn))

        self.menu_btn = icon_button(win.icons.get("ellipsis"), "⋮", "More actions")
        self.menu_btn.setProperty("buttonRole", "menu")
        self.menu_btn.clicked.connect(self._open_dropdown)

        top_row.addStretch(1)
        top_row.addWidget(self.copy_btn, 0, Qt.AlignVCenter)
        top_row.addWidget(self.menu_btn, 0, Qt.AlignVCenter)
        main_lay.addLayout(top_row)

        # Bottom content area: Astroid Icon anchored to line 1 with full-width line 2 flow
        astroid_pm = render_pixmap("astroid", (13, 13), color=color)

        raw_prompt = prompt.get("prompt") or prompt.get("content", "")
        self.preview = PromptPreviewWidget(raw_prompt, icon_pm=astroid_pm)
        main_lay.addWidget(self.preview)

        self._refresh()

    def _open_dropdown(self):
        menu = ActionMenuPopup(
            self.win,
            on_edit=lambda: self.on_edit(self.prompt),
            on_delete=lambda: self.on_delete(self.prompt),
            parent=self.win
        )
        menu.show_under(self.menu_btn)

    def _refresh(self):
        self.copy_btn.setVisible(self._hovered)
