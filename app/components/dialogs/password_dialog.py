"""
PasswordPromptDialog: A compact, modern password input dialog for decrypting DizoClip archives.
Features:
- Unified DizoClip dark titlebar (apply_dark_title_bar)
- Comfortable expanded field width (330px dialog width)
- Embedded Lucide eye reveal toggle action (👁️) to show/hide password
- DizoClip midnight slate theme styling
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from app.config.theme import ACCENT, BG_INPUT, BG_MAIN, BORDER, TEXT_DIM, TEXT_MAIN
from app.core.icons import load_icon
from app.core.window_utils import apply_dark_title_bar


class PasswordPromptDialog(QDialog):
    WIDTH, HEIGHT = 330, 145

    def __init__(self, parent=None, title: str = "Import data", label: str = "Password for this file:"):
        super().__init__(parent)
        win_title = f"{title} - DizoClip" if "DizoClip" not in title else title
        self.setWindowTitle(win_title)
        self.setModal(True)
        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.setWindowFlags(
            Qt.Dialog
            | Qt.WindowTitleHint
            | Qt.WindowSystemMenuHint
            | Qt.WindowCloseButtonHint
            | Qt.MSWindowsFixedSizeDialogHint
        )

        if parent and hasattr(parent, "windowIcon") and not parent.windowIcon().isNull():
            self.setWindowIcon(parent.windowIcon())

        self.setStyleSheet(f"""
            QDialog {{ background-color: {BG_MAIN}; border: none; }}
            QLabel  {{ background: transparent; color: {TEXT_MAIN}; font-size: 13px; font-weight: 600; }}
            QLineEdit {{
                background: {BG_INPUT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 6px 32px 6px 10px;
                color: {TEXT_MAIN};
                font-size: 13px;
            }}
            QLineEdit:focus {{ border: 1px solid {ACCENT}; }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(10)

        lbl = QLabel(label)
        root.addWidget(lbl)

        self.pw_input = QLineEdit()
        self.pw_input.setEchoMode(QLineEdit.Password)
        self.pw_input.setPlaceholderText("Enter password")
        self.pw_input.setFixedHeight(34)

        self._reveal_pw = False
        self._eye_open = load_icon("eye", color=TEXT_DIM)
        self._eye_closed = load_icon("eye-closed", color=TEXT_DIM)

        self._toggle_action = QAction(self)
        if self._eye_open and not self._eye_open.isNull():
            self._toggle_action.setIcon(self._eye_open)
        self._toggle_action.setToolTip("Show / hide password")
        self._toggle_action.triggered.connect(self._toggle_pw_reveal)
        self.pw_input.addAction(self._toggle_action, QLineEdit.TrailingPosition)
        self.pw_input.returnPressed.connect(self.accept)
        root.addWidget(self.pw_input)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch(1)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedSize(76, 32)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: #1c202c;
                color: #9aa2b2;
                border: 1px solid {BORDER};
                border-radius: 8px;
                font-weight: 600;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: #242a3a;
                color: #ffffff;
            }}
        """)
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.cancel_btn)

        self.ok_btn = QPushButton("OK")
        self.ok_btn.setFixedSize(76, 32)
        self.ok_btn.setCursor(Qt.PointingHandCursor)
        self.ok_btn.setDefault(True)
        self.ok_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: #0b0d10;
                border-radius: 8px;
                font-weight: 700;
                font-size: 12px;
                border: none;
            }}
            QPushButton:hover {{
                background: #d5693c;
            }}
        """)
        self.ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(self.ok_btn)

        root.addLayout(btn_row)

    def _toggle_pw_reveal(self) -> None:
        self._reveal_pw = not self._reveal_pw
        if self._reveal_pw:
            self.pw_input.setEchoMode(QLineEdit.Normal)
            if self._eye_closed and not self._eye_closed.isNull():
                self._toggle_action.setIcon(self._eye_closed)
        else:
            self.pw_input.setEchoMode(QLineEdit.Password)
            if self._eye_open and not self._eye_open.isNull():
                self._toggle_action.setIcon(self._eye_open)

    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_title_bar(self, BG_MAIN, TEXT_MAIN)

    @classmethod
    def get_password(cls, parent=None, title: str = "Import data", label: str = "Password for this file:") -> str | None:
        dlg = cls(parent, title, label)
        if dlg.exec() == QDialog.Accepted:
            txt = dlg.pw_input.text()
            return txt if txt else None
        return None
