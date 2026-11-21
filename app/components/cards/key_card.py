from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout

from app.components.buttons.icon_button import icon_button
from app.components.cards.base_card import BaseCard
from app.components.labels.elided_label import ElidedLabel
from app.components.menus.action_menu import ActionMenuPopup
from app.config.constants import BADGE_COLORS, KEY_CARD_H
from app.config.theme import FONT_MONO, font_css
from app.core.icons import render_pixmap
from app.core.masking import mask_secret


class KeyCard(BaseCard):
    """API Key card with masked key, copy action, and 3-dot dropdown."""
    CARD_HEIGHT = KEY_CARD_H

    def __init__(self, key, win, on_copy, on_edit, on_delete, on_toggle=None, parent=None):
        super().__init__(win, parent)
        self.key = key
        self.on_copy = on_copy
        self.on_edit = on_edit
        self.on_delete = on_delete

        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(14, 12, 14, 12)
        main_lay.setSpacing(6)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(4)

        color = key.get("color", BADGE_COLORS[0])
        title_text = key.get("label", "")
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

        # Action: Copy key button
        self.copy_btn = icon_button(win.icons.get("copy"), "⧉", "Copy key", size=24, icon_size=13)
        self.copy_btn.clicked.connect(lambda: on_copy(self.key, self.copy_btn))

        # 3-dot dropdown menu button
        self.menu_btn = icon_button(win.icons.get("ellipsis"), "⋮", "More actions", size=24, icon_size=14)
        self.menu_btn.setProperty("buttonRole", "menu")
        self.menu_btn.clicked.connect(self._open_dropdown)

        top_row.addStretch(1)
        top_row.addWidget(self.copy_btn, 0, Qt.AlignVCenter)
        top_row.addWidget(self.menu_btn, 0, Qt.AlignVCenter)
        main_lay.addLayout(top_row)

        bot_row = QHBoxLayout()
        bot_row.setContentsMargins(0, 0, 0, 0)
        bot_row.setSpacing(6)

        key_pm = render_pixmap("key-round", (12, 12), color=color)
        if key_pm is not None:
            key_ico_lbl = QLabel()
            key_ico_lbl.setPixmap(key_pm)
            key_ico_lbl.setFixedSize(12, 12)
            key_ico_lbl.setStyleSheet("background: transparent; border: none;")
            bot_row.addWidget(key_ico_lbl, 0, Qt.AlignVCenter)

        if key.get("_decrypt_failed"):
            masked_text = "Locked: encrypted for another Windows account"
        elif key.get("full_key"):
            masked_text = mask_secret(key["full_key"])
        else:
            masked_text = "No secret stored. Edit to re-enter it"
        self.masked_lbl = ElidedLabel(masked_text)
        self.masked_lbl.setStyleSheet(f"""
            color: #7a8292;
            font-family: {FONT_MONO};
            {font_css("code")}
        """)
        bot_row.addWidget(self.masked_lbl, 1, Qt.AlignVCenter)
        main_lay.addLayout(bot_row)

        self._refresh()

    def _open_dropdown(self):
        menu = ActionMenuPopup(
            self.win,
            on_edit=lambda: self.on_edit(self.key),
            on_delete=lambda: self.on_delete(self.key),
            parent=self.win
        )
        menu.show_under(self.menu_btn)

    def _refresh(self):
        self.copy_btn.setVisible(self._hovered)
