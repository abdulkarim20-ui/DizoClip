from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from app.config.theme import BG_MAIN, BORDER, CARD_BORDER, TEXT_DIM, TEXT_MAIN
from app.core.icons import render_pixmap


class ActionMenuItem(QPushButton):
    """
    Dropdown menu item with pixel-perfect SVG alignment and dynamic hover states.
    Uses explicit layout with QLabel widgets to guarantee vertical/horizontal alignment.
    """
    def __init__(
        self,
        text: str,
        icon_name: str,
        is_danger: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.is_danger = is_danger
        self.icon_name = icon_name
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFixedHeight(32)

        # Base layout
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 0, 10, 0)
        lay.setSpacing(9)
        lay.setAlignment(Qt.AlignVCenter)

        # Icon
        self._pm_normal = render_pixmap(
            icon_name,
            (14, 14),
            color="#e05a5a" if is_danger else "#8f97a8",
        )
        self._pm_hover = render_pixmap(
            icon_name,
            (14, 14),
            color="#ff5454" if is_danger else "#ffffff",
        )

        self.icon_lbl = QLabel()
        if self._pm_normal:
            self.icon_lbl.setPixmap(self._pm_normal)
        self.icon_lbl.setFixedSize(14, 14)
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(self.icon_lbl, 0, Qt.AlignVCenter)

        # Text label
        self.text_lbl = QLabel(text)
        self.text_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.text_lbl.setStyleSheet(f"""
            color: {'#e05a5a' if is_danger else TEXT_MAIN};
            font-size: 12px;
            font-weight: 500;
            background: transparent;
            border: none;
        """)
        lay.addWidget(self.text_lbl, 1, Qt.AlignVCenter)

        self._update_style(False)

    def enterEvent(self, event):
        self._update_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._update_style(False)
        super().leaveEvent(event)

    def _update_style(self, hovered: bool):
        if self.is_danger:
            if hovered:
                self.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(232, 74, 74, 0.16);
                        border: none;
                        border-radius: 7px;
                    }
                """)
                self.text_lbl.setStyleSheet("""
                    color: #ff5454;
                    font-size: 12px;
                    font-weight: 600;
                    background: transparent;
                    border: none;
                """)
                if self._pm_hover:
                    self.icon_lbl.setPixmap(self._pm_hover)
            else:
                self.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        border: none;
                        border-radius: 7px;
                    }
                """)
                self.text_lbl.setStyleSheet("""
                    color: #e05a5a;
                    font-size: 12px;
                    font-weight: 500;
                    background: transparent;
                    border: none;
                """)
                if self._pm_normal:
                    self.icon_lbl.setPixmap(self._pm_normal)
        else:
            if hovered:
                self.setStyleSheet("""
                    QPushButton {
                        background-color: #242938;
                        border: none;
                        border-radius: 7px;
                    }
                """)
                self.text_lbl.setStyleSheet("""
                    color: #ffffff;
                    font-size: 12px;
                    font-weight: 500;
                    background: transparent;
                    border: none;
                """)
                if self._pm_hover:
                    self.icon_lbl.setPixmap(self._pm_hover)
            else:
                self.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        border: none;
                        border-radius: 7px;
                    }
                """)
                self.text_lbl.setStyleSheet(f"""
                    color: {TEXT_MAIN};
                    font-size: 12px;
                    font-weight: 500;
                    background: transparent;
                    border: none;
                """)
                if self._pm_normal:
                    self.icon_lbl.setPixmap(self._pm_normal)


class ActionMenuPopup(QFrame):
    """Floating dropdown menu matching Design 8 (rounded-xl, p-1, borderSubtle, shadow)."""
    def __init__(self, win, on_edit, on_delete, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(144)

        # Container card matching main UI background & dropdown specs
        card = QFrame(self)
        card.setObjectName("ActionMenuCard")
        card.setStyleSheet(f"""
            QFrame#ActionMenuCard {{
                background-color: {BG_MAIN};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)

        # Drop shadow styling matching modern subtle elevation
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)

        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)  # breathing room for shadow
        root.addWidget(card)

        menu_lay = QVBoxLayout(card)
        menu_lay.setContentsMargins(4, 4, 4, 4)  # p-1
        menu_lay.setSpacing(2)

        # 1. Edit Item
        edit_btn = ActionMenuItem("Edit Item", "pencil", is_danger=False, parent=self)
        edit_btn.clicked.connect(lambda: (self.close(), on_edit()))
        menu_lay.addWidget(edit_btn)

        # 2. Delete Item (unhighlighted by default, highlights red on hover)
        del_btn = ActionMenuItem("Delete Item", "trash", is_danger=True, parent=self)
        del_btn.clicked.connect(lambda: (self.close(), on_delete()))
        menu_lay.addWidget(del_btn)

    def show_under(self, anchor_btn):
        anchor_rect = anchor_btn.rect()
        pos = anchor_btn.mapToGlobal(anchor_rect.bottomLeft())
        # Position slightly to the left so it aligns neatly under the 3-dots button
        self.move(pos.x() - self.width() + anchor_btn.width() + 6, pos.y() + 2)
        self.show()
