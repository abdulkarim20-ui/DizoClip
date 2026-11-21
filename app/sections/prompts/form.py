import time
import uuid

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.components.buttons.icon_button import icon_button
from app.components.inputs.color_picker import ColorSelectorBar
from app.config.constants import BADGE_COLORS
from app.config.theme import ACCENT, BG_CARD, BORDER, BTN_HOVER, TEXT_DIM, TEXT_MAIN, font_css


class PromptFormView(QWidget):
    """Add / Edit Prompt Form View."""
    def __init__(self, win):
        super().__init__()
        self.win = win
        self.editing = None
        self.selected_color = BADGE_COLORS[0]
        self.color_buttons = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(6)

        # Top Bar
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 2)
        top.setSpacing(10)
        back = icon_button(win.icons.get("back"), "←", "Back to list",
                           size=28, icon_size=15, object_name="SquareBtn")
        back.clicked.connect(win.show_list_view)
        top.addWidget(back)

        self.title_lbl = QLabel("Add Prompt")
        self.title_lbl.setStyleSheet(font_css("title-lg", color=TEXT_MAIN))
        top.addWidget(self.title_lbl)
        top.addStretch(1)
        root.addLayout(top)

        root.addSpacing(4)
        name_lbl = QLabel("Title / Name")
        name_lbl.setStyleSheet(font_css("subtext", color=TEXT_DIM))
        root.addWidget(name_lbl)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Find & Fix Bugs")
        self.name_edit.setFixedHeight(34)
        root.addWidget(self.name_edit)

        # Consistent section gap before the prompt content
        root.addSpacing(9)
        prompt_lbl = QLabel("Prompt Content")
        prompt_lbl.setStyleSheet(font_css("subtext", color=TEXT_DIM))
        root.addWidget(prompt_lbl)

        self.prompt_edit = QPlainTextEdit()
        self.prompt_edit.setPlaceholderText("Write or paste your full prompt here...")
        self.prompt_edit.setFixedHeight(154)
        root.addWidget(self.prompt_edit)

        # Consistent section gap before the color selector.
        # Keeps the color palette visually separated from the prompt editor.
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

    def edit(self, prompt_data=None):
        self.editing = prompt_data
        self.title_lbl.setText("Edit Prompt" if prompt_data else "Add Prompt")
        if prompt_data is not None:
            self.name_edit.setText(prompt_data.get("name") or prompt_data.get("title", ""))
            self.prompt_edit.setPlainText(prompt_data.get("prompt") or prompt_data.get("content", ""))
            self._pick_color(prompt_data.get("color", BADGE_COLORS[0]))
        else:
            self.name_edit.clear()
            self.prompt_edit.clear()
            self._pick_color(BADGE_COLORS[0])
        self.hint.hide()
        self.name_edit.setFocus()

    def _pick_color(self, c):
        self.selected_color = c
        if hasattr(self, "color_bar"):
            self.color_bar.set_color(c)

    def _on_color_changed(self, c):
        self.selected_color = c

    def _save(self):
        title = self.name_edit.text().strip()
        body = self.prompt_edit.toPlainText().strip()
        if not title or not body:
            self.hint.setText("Please fill in both Name and Prompt.")
            self.hint.show()
            return

        now_ms = int(time.time() * 1000)
        if self.editing is not None:
            self.editing["name"] = title
            self.editing["prompt"] = body
            self.editing["color"] = self.selected_color
            self.editing["updatedAt"] = now_ms
            self.editing.pop("_decrypt_failed", None)
        else:
            new_id = f"prompt_{now_ms}_{uuid.uuid4().hex[:5]}"
            self.win.prompts.insert(0, {
                "id": new_id,
                "name": title,
                "prompt": body,
                "color": self.selected_color,
                "createdAt": now_ms,
                "updatedAt": now_ms
            })
        self.win.save_prompts()
        self.win.show_list_view()
