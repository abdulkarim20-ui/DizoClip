from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from app.components.buttons.icon_button import icon_button
from app.components.cards.base_card import BaseCard
from app.components.labels.elided_label import ElidedLabel
from app.components.menus.action_menu import ActionMenuPopup
from app.config.constants import COMMAND_CARD_H
from app.config.theme import FONT_MONO, font_css


class CommandPreviewWidget(QWidget):
    """
    Two-line monospace command preview with '>_' prompt prefix on line 1 and full-width flowing text on line 2.
    """
    def __init__(self, text: str, prefix_color: str = "#ff773d", parent=None):
        super().__init__(parent)
        self._raw_text = text
        self._prefix_color = prefix_color
        self.setFixedHeight(32)

        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(2)

        self.row1 = QHBoxLayout()
        self.row1.setContentsMargins(0, 0, 0, 0)
        self.row1.setSpacing(6)

        self.prompt_sym = QLabel(">_")
        self.prompt_sym.setStyleSheet(f"""
            color: {prefix_color};
            font-family: {FONT_MONO};
            {font_css("code")}
            background: transparent;
            border: none;
        """)
        self.row1.addWidget(self.prompt_sym, 0, Qt.AlignVCenter)

        self.line1_lbl = QLabel()
        self.line1_lbl.setStyleSheet(f"""
            color: #7a8292;
            font-family: {FONT_MONO};
            {font_css("code")}
            background: transparent;
            border: none;
        """)
        self.row1.addWidget(self.line1_lbl, 1, Qt.AlignVCenter)
        self.lay.addLayout(self.row1)

        self.line2_lbl = QLabel()
        self.line2_lbl.setStyleSheet(f"""
            color: #7a8292;
            font-family: {FONT_MONO};
            {font_css("code")}
            background: transparent;
            border: none;
        """)
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

        fm = self.line1_lbl.fontMetrics()
        sym_w = fm.horizontalAdvance(">_") + 6
        w1 = max(10, w - sym_w)
        w2 = max(10, w)

        lines = [l.strip() for l in raw.split("\n") if l.strip()]

        if len(lines) >= 2:
            # Explicit multi-line snippet: line 1 shows 1st line, line 2 shows 2nd line
            self.line1_lbl.setText(fm.elidedText(lines[0], Qt.ElideRight, w1))
            self.line2_lbl.setText(fm.elidedText(lines[1], Qt.ElideRight, w2))
            self.line2_lbl.setVisible(True)
        elif len(lines) == 1:
            # Single line: if it fits on line 1, display it; otherwise wrap words across 2 lines
            single_line = lines[0]
            if fm.horizontalAdvance(single_line) <= w1:
                self.line1_lbl.setText(single_line)
                self.line2_lbl.setText("")
                self.line2_lbl.setVisible(False)
            else:
                words = single_line.split(" ")
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


class CommandCard(BaseCard):
    """Terminal command card with >_ prompt on line 1, 2-line monospace snippet preview, copy action, and 3-dot dropdown."""
    CARD_HEIGHT = COMMAND_CARD_H

    def __init__(self, cmd_item, win, on_copy, on_edit, on_delete, parent=None):
        super().__init__(win, parent)
        self.cmd_item = cmd_item
        self.on_copy = on_copy
        self.on_edit = on_edit
        self.on_delete = on_delete

        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(14, 12, 14, 12)
        main_lay.setSpacing(6)

        # Top row: Solid colored badge + Copy button + 3-dot menu
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(4)

        color = cmd_item.get("color", "#ff773d")
        title_text = cmd_item.get("title", "Command")

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

        # Copy button
        self.copy_btn = icon_button(win.icons.get("copy"), "⧉", "Copy command")
        self.copy_btn.clicked.connect(lambda: on_copy(self.cmd_item, self.copy_btn))

        # 3-dot More Actions button with semantic role
        self.menu_btn = icon_button(win.icons.get("ellipsis"), "⋮", "More actions")
        self.menu_btn.setProperty("buttonRole", "menu")
        self.menu_btn.clicked.connect(self._open_dropdown)

        top_row.addStretch(1)
        top_row.addWidget(self.copy_btn, 0, Qt.AlignVCenter)
        top_row.addWidget(self.menu_btn, 0, Qt.AlignVCenter)
        main_lay.addLayout(top_row)

        # Bottom content area: 2-line monospace command preview
        cmd_text = cmd_item.get("command", "")
        self.preview = CommandPreviewWidget(cmd_text, prefix_color=color)
        main_lay.addWidget(self.preview)

        self._refresh()

    def _open_dropdown(self):
        menu = ActionMenuPopup(
            self.win,
            on_edit=lambda: self.on_edit(self.cmd_item),
            on_delete=lambda: self.on_delete(self.cmd_item),
            parent=self.win
        )
        menu.show_under(self.menu_btn)

    def _refresh(self):
        self.copy_btn.setVisible(self._hovered)
