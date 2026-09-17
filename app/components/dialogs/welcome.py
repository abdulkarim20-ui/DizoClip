"""
First-launch DizoClip welcome dialog.

Matches the design mock:
- Title: "Welcome." with subtitle "A faster way to keep your developer essentials together."
- Feature Card 1: "Fast by design" with fast.svg icon
- Feature Card 2: "Local by default" with lock-keyhole.svg icon
- Accent "Get Started" button
- Native dark titlebar and window width matching main window
"""
from __future__ import annotations

import os

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from app.config.constants import WINDOW_W
from app.config.paths import ASSETS_DIR
from app.config.theme import (
    ACCENT,
    BG_CARD,
    BG_MAIN,
    BORDER,
    CARD_BORDER,
    FONT_UI,
    TEXT_DIM,
    TEXT_MAIN,
)
from app.core.icons import render_pixmap
from app.core.window_utils import apply_dark_title_bar, ensure_taskbar_icon


class WelcomeDialog(QDialog):
    def __init__(self, parent=None, mode: str = "installed"):
        super().__init__(parent)
        self.setWindowTitle("DizoClip")
        self.setModal(True)
        self.setFixedWidth(WINDOW_W)

        # Title bar: show title & close button, top-level window so taskbar icon is always visible
        self.setWindowFlags(
            Qt.Window
            | Qt.CustomizeWindowHint
            | Qt.WindowTitleHint
            | Qt.WindowSystemMenuHint
            | Qt.WindowCloseButtonHint
            | Qt.MSWindowsFixedSizeDialogHint
        )

        # Window icon for titlebar & taskbar
        ico_path = os.path.join(ASSETS_DIR, "app_logo.ico")
        png_path = os.path.join(ASSETS_DIR, "app_logo.png")
        if os.path.exists(ico_path):
            self.setWindowIcon(QIcon(ico_path))
        elif os.path.exists(png_path):
            self.setWindowIcon(QIcon(png_path))
        elif parent and not parent.windowIcon().isNull():
            self.setWindowIcon(parent.windowIcon())

        # Background & styles matching main window palette
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {BG_MAIN};
                border: none;
            }}
            QLabel {{
                background: transparent;
                border: none;
                font-family: {FONT_UI};
            }}
            QLabel#title {{
                color: #ffffff;
                font-size: 21px;
                font-weight: 800;
            }}
            QLabel#subtitle {{
                color: {TEXT_DIM};
                font-size: 12px;
                line-height: 1.4;
            }}
            QFrame#featureCard {{
                background: #151824;
                border: 1px solid #232838;
                border-radius: 12px;
            }}
            QLabel#featureTitle {{
                color: #ffffff;
                font-size: 13px;
                font-weight: 700;
            }}
            QLabel#featureText {{
                color: #8e97a8;
                font-size: 11.5px;
                line-height: 1.4;
            }}
            QPushButton#getStarted {{
                background: #d86539;
                color: #ffffff;
                font-size: 12.5px;
                font-weight: 700;
                height: 36px;
                padding: 0 20px;
                border: none;
                border-radius: 10px;
            }}
            QPushButton#getStarted:hover {{
                background: #e37244;
            }}
            QPushButton#getStarted:pressed {{
                background: #be5329;
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        # Header Title & Subtitle
        title = QLabel("Welcome.")
        title.setObjectName("title")
        root.addWidget(title)

        subtitle = QLabel("A faster way to keep your developer essentials together.")
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        root.addSpacing(4)

        # Feature Cards definition: (icon_name, icon_color, title, description)
        features = [
            (
                "fast",
                "#ff8c5a",
                "Fast by design",
                "Access your keys, prompts, models, links, and commands without breaking your flow.",
            ),
            (
                "lock-keyhole",
                "#8e97a8",
                "Local by default",
                "Your data stays on your computer, giving you control over your essentials.",
            ),
        ]

        for icon_name, icon_color, title_text, body_text in features:
            card = QFrame()
            card.setObjectName("featureCard")

            card_lay = QHBoxLayout(card)
            card_lay.setContentsMargins(14, 12, 14, 12)
            card_lay.setSpacing(12)
            card_lay.setAlignment(Qt.AlignTop)

            # Left Icon
            icon_lbl = QLabel()
            pm = render_pixmap(icon_name, (16, 16), color=icon_color)
            if pm is not None:
                icon_lbl.setPixmap(pm)
            icon_lbl.setFixedSize(18, 18)
            icon_lbl.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
            icon_lbl.setContentsMargins(0, 2, 0, 0)
            card_lay.addWidget(icon_lbl, 0, Qt.AlignTop)

            # Right content column (Title + Description)
            text_lay = QVBoxLayout()
            text_lay.setContentsMargins(0, 0, 0, 0)
            text_lay.setSpacing(3)

            t = QLabel(title_text)
            t.setObjectName("featureTitle")

            b = QLabel(body_text)
            b.setObjectName("featureText")
            b.setWordWrap(True)

            text_lay.addWidget(t)
            text_lay.addWidget(b)
            card_lay.addLayout(text_lay, 1)

            root.addWidget(card)

        root.addSpacing(6)

        # Bottom Action Row with right-aligned "Get Started" button
        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.addStretch(1)

        btn = QPushButton("Get Started")
        btn.setObjectName("getStarted")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self.accept)
        btn.setDefault(True)
        actions.addWidget(btn)

        root.addLayout(actions)

        # Smooth pop-in appearance animation
        self._opacity_fx = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_fx)
        self._anim = QPropertyAnimation(self._opacity_fx, b"opacity")
        self._anim.setDuration(150)
        self._anim.setStartValue(0.15)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

        # Apply dark title bar matching main window titlebar color
        self._setup_titlebar()

    def _setup_titlebar(self):
        apply_dark_title_bar(self, BG_MAIN, TEXT_MAIN)
        ensure_taskbar_icon(self)

    def showEvent(self, event):
        super().showEvent(event)
        self._anim.start()
