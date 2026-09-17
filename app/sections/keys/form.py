from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
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


class FormView(QWidget):
    """Add / Edit API Key Form View with embedded eye action inside the input."""
    def __init__(self, win):
        super().__init__()
        self.win = win
        self.editing_key = None
        self.selected_color = BADGE_COLORS[0]
        self._reveal = False
        self.color_buttons = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(6)

        # Top Bar
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 4)
        top.setSpacing(10)
        back = icon_button(win.icons.get("back"), "←", "Back to list",
                           size=28, icon_size=15, object_name="SquareBtn")
        back.clicked.connect(win.show_list_view)
        top.addWidget(back)

        self.title_lbl = QLabel("Add API Key")
        self.title_lbl.setStyleSheet(font_css("title-lg", color=TEXT_MAIN))
        top.addWidget(self.title_lbl)
        top.addStretch(1)
        root.addLayout(top)

        root.addSpacing(4)
        lbl_text = QLabel("Label")
        lbl_text.setStyleSheet(font_css("subtext", color=TEXT_DIM))
        root.addWidget(lbl_text)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. OpenAI Api Key")
        self.name_edit.setFixedHeight(34)
        root.addWidget(self.name_edit)

        # Consistent section gap before API Key field
        root.addSpacing(9)
        key_text = QLabel("API Key")
        key_text.setStyleSheet(font_css("subtext", color=TEXT_DIM))
        root.addWidget(key_text)

        # Embedded trailing eye action inside full-width QLineEdit
        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("Paste your secret key here...")
        self.key_edit.setFixedHeight(34)
        self.key_edit.setEchoMode(QLineEdit.Password)
        self.key_edit.setStyleSheet("font-size: 15px; letter-spacing: 1.5px; padding: 8px 10px 4px 10px;")

        self.eye_action = QAction(self)
        self.eye_action.setToolTip("Reveal key")
        eye_ic = self.win.icons.get("eye")
        if eye_ic:
            self.eye_action.setIcon(eye_ic)
        self.eye_action.triggered.connect(lambda: self._set_reveal(not self._reveal))
        self.key_edit.addAction(self.eye_action, QLineEdit.TrailingPosition)
        root.addWidget(self.key_edit)

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

    def edit(self, key_data=None):
        self.editing_key = key_data
        self._set_reveal(False)
        self.title_lbl.setText("Edit API Key" if key_data else "Add API Key")
        if key_data is not None:
            self.name_edit.setText(key_data.get("label", ""))
            initial_val = key_data.get("full_key", key_data.get("masked", ""))
            self.key_edit.setText(initial_val)
            self.key_edit.setCursorPosition(0)
            self.name_edit.setCursorPosition(0)
            self._pick_color(key_data.get("color", BADGE_COLORS[0]))
        else:
            self.name_edit.clear()
            self.key_edit.clear()
            self._pick_color(BADGE_COLORS[0])
        self.hint.hide()
        self.name_edit.setFocus()

    def _pick_color(self, c):
        self.selected_color = c
        if hasattr(self, "color_bar"):
            self.color_bar.set_color(c)

    def _on_color_changed(self, c):
        self.selected_color = c

    def _set_reveal(self, flag):
        self._reveal = flag
        self.key_edit.setEchoMode(QLineEdit.Normal if flag else QLineEdit.Password)
        if flag:
            self.key_edit.setStyleSheet("font-size: 13px; letter-spacing: normal; padding: 6px 10px;")
        else:
            self.key_edit.setStyleSheet("font-size: 15px; letter-spacing: 1.5px; padding: 8px 10px 4px 10px;")
        self.key_edit.setCursorPosition(0)
        ic = self.win.icons.get("eye_closed" if flag else "eye")
        if ic is not None:
            self.eye_action.setIcon(ic)
        self.eye_action.setToolTip("Hide key" if flag else "Reveal key")

    def _mask_key(self, raw):
        if len(raw) <= 6:
            return "*" * len(raw) if raw else "********"
        prefix = raw[:3]
        suffix = raw[-3:]
        return f"{prefix}-{'*' * 20}{suffix}"

    def _save(self):
        name = self.name_edit.text().strip()
        val = self.key_edit.text().strip()
        if not name or not val:
            self.hint.setText("Please fill in both fields.")
            self.hint.show()
            return
        if self.editing_key is not None:
            self.editing_key["label"] = name
            self.editing_key["full_key"] = val
            self.editing_key["masked"] = self._mask_key(val)
            self.editing_key["color"] = self.selected_color
        else:
            self.win.keys.insert(0, {
                "label": name,
                "masked": self._mask_key(val),
                "full_key": val,
                "color": self.selected_color
            })
        self.win.save_keys()
        self.win.show_list_view()
