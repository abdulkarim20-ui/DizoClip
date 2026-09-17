"""
Integrated onboarding welcome view for fresh launch.
Embedded directly inside the primary window (no secondary window).
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.config.theme import (
    ACCENT,
    BG_MAIN,
    FONT_UI,
    TEXT_DIM,
    TEXT_MAIN,
)
from app.core.icons import render_pixmap


class WelcomeView(QWidget):
    """
    Onboarding view displayed directly inside the MainWindow stack
    on first launch, eliminating the need for a secondary window.
    """
    def __init__(self, win, parent=None):
        super().__init__(parent)
        self.win = win

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {BG_MAIN};
                font-family: {FONT_UI};
            }}
            QLabel {{
                background: transparent;
                border: none;
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
                background: {ACCENT};
                color: #ffffff;
                font-size: 12.5px;
                font-weight: 700;
                height: 36px;
                padding: 0 22px;
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
        root.setContentsMargins(20, 16, 20, 18)
        root.setSpacing(10)

        # Header Title & Subtitle
        title = QLabel("Welcome.")
        title.setObjectName("title")
        root.addWidget(title)

        subtitle = QLabel("A faster way to keep your developer essentials together.")
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        root.addSpacing(2)

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
            card_lay.setContentsMargins(14, 10, 14, 10)
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
            text_lay.setSpacing(2)

            t = QLabel(title_text)
            t.setObjectName("featureTitle")

            b = QLabel(body_text)
            b.setObjectName("featureText")
            b.setWordWrap(True)

            text_lay.addWidget(t)
            text_lay.addWidget(b)
            card_lay.addLayout(text_lay, 1)

            root.addWidget(card)

        root.addSpacing(4)

        # Bottom Action Row with right-aligned "Get Started" button
        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.addStretch(1)

        btn = QPushButton("Get Started")
        btn.setObjectName("getStarted")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self._on_get_started)
        btn.setDefault(True)
        actions.addWidget(btn)

        root.addLayout(actions)

    def _on_get_started(self):
        if hasattr(self.win, "on_welcome_get_started"):
            self.win.on_welcome_get_started()
