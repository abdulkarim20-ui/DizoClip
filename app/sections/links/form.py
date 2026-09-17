import time
import uuid

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.components.buttons.icon_button import icon_button
from app.components.inputs.color_picker import ColorSelectorBar
from app.config.constants import BADGE_COLORS
from app.config.theme import ACCENT, BG_CARD, BORDER, BTN_HOVER, TEXT_DIM, TEXT_MAIN, font_css


class LinkFormView(QWidget):
    """Add / Edit Link Form View."""
    def __init__(self, win):
        super().__init__()
        self.win = win
        self.editing = None
        self.selected_color = "#ff773d"
        self.color_buttons = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(6)

        # Top Bar
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 2)
        top.setSpacing(10)
        back = icon_button(win.icons.get("back"), "←", "Back to links",
                           size=28, icon_size=15, object_name="SquareBtn")
        back.clicked.connect(win.show_list_view)
        top.addWidget(back)

        self.title_lbl = QLabel("Add Link")
        self.title_lbl.setStyleSheet(font_css("title-lg", color=TEXT_MAIN))
        top.addWidget(self.title_lbl)
        top.addStretch(1)
        root.addLayout(top)

        root.addSpacing(4)
        name_lbl = QLabel("Title / Label")
        name_lbl.setStyleSheet(font_css("subtext", color=TEXT_DIM))
        root.addWidget(name_lbl)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("e.g. GitHub Repository")
        self.title_edit.setFixedHeight(34)
        root.addWidget(self.title_edit)

        # Consistent section gap before URL field
        root.addSpacing(9)
        url_lbl = QLabel("URL / Link Address")
        url_lbl.setStyleSheet(font_css("subtext", color=TEXT_DIM))
        root.addWidget(url_lbl)

        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://...")
        self.url_edit.setFixedHeight(34)
        root.addWidget(self.url_edit)

        # Consistent section gap before the color selector
        root.addSpacing(9)
        self.color_bar = ColorSelectorBar(
            initial_color=self.selected_color,
            on_color_changed=self._on_color_changed,
            win=self.win,
            parent=self
        )
        root.addWidget(self.color_bar)

        self.hint = QLabel()
        self.hint.setProperty("cls", "error")
        self.hint.hide()
        root.addWidget(self.hint)

        root.addStretch(1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.setContentsMargins(0, 6, 0, 0)

        cancel = QPushButton("Cancel")
        cancel.setStyleSheet(f"""
            QPushButton {{
                background: {BG_CARD};
                color: {TEXT_MAIN};
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                border: 1px solid {BORDER};
            }}
            QPushButton:hover {{ background: {BTN_HOVER}; }}
        """)
        cancel.setFixedHeight(36)
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.clicked.connect(win.show_list_view)
        btn_row.addWidget(cancel)

        save = QPushButton("Save")
        save.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: #0b0d10;
                font-weight: 700;
                font-size: 13px;
                border-radius: 8px;
                padding: 8px 16px;
                border: none;
            }}
            QPushButton:hover {{ background: #d5693c; }}
            QPushButton:pressed {{ background: #b85a30; }}
        """)
        save.setFixedHeight(36)
        save.setCursor(Qt.PointingHandCursor)
        save.clicked.connect(self._save)
        btn_row.addWidget(save)

        root.addLayout(btn_row)

    def edit(self, link_data=None):
        self.editing = link_data
        self.title_lbl.setText("Edit Link" if link_data else "Add Link")
        if link_data is not None:
            self.title_edit.setText(link_data.get("title", ""))
            self.url_edit.setText(link_data.get("url", ""))
            self.title_edit.setCursorPosition(0)
            self.url_edit.setCursorPosition(0)
            self._pick_color(link_data.get("color", BADGE_COLORS[0]))
        else:
            self.title_edit.clear()
            self.url_edit.clear()
            self._pick_color(BADGE_COLORS[0])
        self.hint.hide()
        self.title_edit.setFocus()

    def _pick_color(self, c):
        self.selected_color = c
        if hasattr(self, "color_bar"):
            self.color_bar.set_color(c)

    def _on_color_changed(self, c):
        self.selected_color = c

    def _save(self):
        title = self.title_edit.text().strip()
        url = self.url_edit.text().strip()
        if not title or not url:
            self.hint.setText("Please fill in both Title and URL.")
            self.hint.show()
            return

        now_ms = int(time.time() * 1000)
        if self.editing is not None:
            self.editing["title"] = title
            self.editing["url"] = url
            self.editing["color"] = self.selected_color
        else:
            new_id = f"link_{now_ms}_{uuid.uuid4().hex[:5]}"
            self.win.links.insert(0, {
                "id": new_id,
                "title": title,
                "url": url,
                "color": self.selected_color,
                "createdAt": now_ms
            })
        self.win.save_links()
        self.win.show_list_view()
