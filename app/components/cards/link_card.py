from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from app.components.buttons.icon_button import icon_button
from app.components.cards.base_card import BaseCard
from app.components.labels.elided_label import ElidedLabel
from app.components.menus.action_menu import ActionMenuPopup
from app.config.constants import LINK_CARD_H
from app.config.theme import FONT_MONO, font_css
from app.core.icons import render_pixmap


class LinkSectionWidget(QWidget):
    """
    Interactive bottom link row (globe icon + URL).
    - Hovers with link color (#58a6ff) and underline with pointing hand cursor.
    - Clicking directly on this link opens the browser (card itself does not).
    """
    def __init__(self, url: str, badge_color: str, on_open_cb, parent=None):
        super().__init__(parent)
        self.url = url
        self.badge_color = badge_color
        self.on_open_cb = on_open_cb
        self._hovered = False
        self._card_hovered = False

        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(f"Open {url} in browser")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 2, 0, 2)
        lay.setSpacing(6)

        self.globe_lbl = QLabel()
        self.globe_lbl.setFixedSize(14, 14)
        self.globe_lbl.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(self.globe_lbl, 0, Qt.AlignVCenter)

        self.url_lbl = ElidedLabel(url)
        lay.addWidget(self.url_lbl, 1, Qt.AlignVCenter)

        self._update_appearance()

    def set_card_hovered(self, card_hovered: bool):
        self._card_hovered = card_hovered
        self._update_appearance()

    def _update_appearance(self):
        if self._hovered:
            col = "#58a6ff"
            self.url_lbl.setStyleSheet(f"""
                color: #58a6ff;
                font-family: {FONT_MONO};
                {font_css("code")}
                text-decoration: underline;
                background: transparent;
            """)
        elif self._card_hovered:
            col = "#58a6ff"
            self.url_lbl.setStyleSheet(f"""
                color: #58a6ff;
                font-family: {FONT_MONO};
                {font_css("code")}
                text-decoration: none;
                background: transparent;
            """)
        else:
            col = self.badge_color
            self.url_lbl.setStyleSheet(f"""
                color: #7a8292;
                font-family: {FONT_MONO};
                {font_css("code")}
                text-decoration: none;
                background: transparent;
            """)

        globe_pm = render_pixmap("globe", (14, 14), color=col)
        if not globe_pm:
            globe_pm = render_pixmap("link", (14, 14), color=col)
        if globe_pm:
            self.globe_lbl.setPixmap(globe_pm)

    def enterEvent(self, event):
        self._hovered = True
        self._update_appearance()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self._update_appearance()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.on_open_cb:
                self.on_open_cb()
        super().mousePressEvent(event)


class LinkCard(BaseCard):
    """Bookmark card with URL, browser launch on link click, copy action, and 3-dot dropdown."""
    CARD_HEIGHT = LINK_CARD_H

    def __init__(self, link, win, on_copy, on_edit, on_delete, on_open, parent=None):
        super().__init__(win, parent)
        self.link = link
        self.on_copy = on_copy
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_open = on_open

        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(14, 12, 14, 12)
        main_lay.setSpacing(6)

        # Top row: Label badge at top left, copy and 3-dot menu on right
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(4)

        color = link.get("color", "#ff773d")
        title_text = link.get("title", "Link")

        title = ElidedLabel(title_text)
        title.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        title.setStyleSheet(f"""
            background-color: {color};
            color: #000000;
            {font_css("caption")}
            padding: 2px 8px;
            border-radius: 4px;
        """)
        title.setToolTip(title_text)
        top_row.addWidget(title, 0, Qt.AlignVCenter)

        # Copy URL Button (visible on hover)
        self.copy_btn = icon_button(win.icons.get("copy"), "⧉", "Copy URL")
        self.copy_btn.clicked.connect(lambda: on_copy(self.link, self.copy_btn))

        # 3-dot More Actions button
        self.menu_btn = icon_button(win.icons.get("ellipsis"), "⋮", "More actions")
        self.menu_btn.setProperty("buttonRole", "menu")
        self.menu_btn.clicked.connect(self._open_dropdown)

        top_row.addStretch(1)
        top_row.addWidget(self.copy_btn, 0, Qt.AlignVCenter)
        top_row.addWidget(self.menu_btn, 0, Qt.AlignVCenter)
        main_lay.addLayout(top_row)

        # Bottom row: Interactive Link Section (Globe icon + URL)
        bot_row = QHBoxLayout()
        bot_row.setContentsMargins(0, 0, 0, 0)
        bot_row.setSpacing(6)

        url_text = link.get("url", "")
        self.link_section = LinkSectionWidget(
            url=url_text,
            badge_color=color,
            on_open_cb=lambda: self.on_open(self.link),
            parent=self,
        )
        bot_row.addWidget(self.link_section, 1, Qt.AlignVCenter)
        main_lay.addLayout(bot_row)

        self._refresh()

    def _open_dropdown(self):
        menu = ActionMenuPopup(
            self.win,
            on_edit=lambda: self.on_edit(self.link),
            on_delete=lambda: self.on_delete(self.link),
            parent=self.win
        )
        menu.show_under(self.menu_btn)

    def _refresh(self):
        self.copy_btn.setVisible(self._hovered)
        if hasattr(self, "link_section"):
            self.link_section.set_card_hovered(self._hovered)
