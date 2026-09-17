from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from app.config.theme import (
    BG_CARD,
    BG_INPUT,
    BG_MAIN,
    BORDER,
    BTN_HOVER,
    CARD_BORDER,
    TEXT_DIM,
    TEXT_MAIN,
)
from app.core.icons import render_pixmap
from app.core.window_utils import apply_dark_title_bar


class ConfirmDeleteDialog(QDialog):
    """
    Clean, modern delete confirmation dialog.
    Flat design with no awkward inner card curves or borders, seamless with the native dark titlebar.
    """
    def __init__(self, parent, label_text, trash_icon=None):
        super().__init__(parent)
        self.setWindowTitle("DizoClip")
        self.setModal(True)
        self.setFixedSize(306, 204)

        # Title bar: show title, hide help button & maximize
        self.setWindowFlags(
            Qt.Dialog
            | Qt.WindowTitleHint
            | Qt.WindowSystemMenuHint
            | Qt.WindowCloseButtonHint
            | Qt.MSWindowsFixedSizeDialogHint
        )

        if parent and not parent.windowIcon().isNull():
            self.setWindowIcon(parent.windowIcon())

        # Solid flat background matching titlebar exactly (no curve, no inner border)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {BG_MAIN};
                border: none;
            }}
        """)

        # Clean dialog layout
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 20)
        root.setSpacing(6)
        root.setAlignment(Qt.AlignCenter)

        # Soft red rounded badge containing clean SVG trash icon
        badge = QFrame()
        badge.setFixedSize(46, 46)
        badge.setStyleSheet("""
            QFrame {
                background: #1f1113;
                border: 1px solid rgba(232, 74, 74, 0.22);
                border-radius: 12px;
            }
        """)
        badge_lay = QVBoxLayout(badge)
        badge_lay.setContentsMargins(0, 0, 0, 0)
        badge_lay.setAlignment(Qt.AlignCenter)

        icon_lbl = QLabel()
        pm_trash = render_pixmap("trash", (22, 22), color="#ff5454")
        if pm_trash is not None:
            icon_lbl.setPixmap(pm_trash)
        elif trash_icon is not None:
            icon_lbl.setPixmap(trash_icon.pixmap(22, 22))
        else:
            icon_lbl.setText("🗑")
            icon_lbl.setStyleSheet("font-size: 20px; color: #ff5454;")
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        badge_lay.addWidget(icon_lbl)
        root.addWidget(badge, 0, Qt.AlignCenter)

        root.addSpacing(4)

        # Title: Delete '<Item>'?
        t = QLabel(f"Delete '{label_text}'?")
        t.setStyleSheet("""
            color: #ffffff;
            font-size: 14px;
            font-weight: 700;
            background: transparent;
            border: none;
        """)
        t.setAlignment(Qt.AlignCenter)
        t.setWordWrap(True)
        root.addWidget(t)

        # Subtitle: This item will be removed permanently.
        s = QLabel("This item will be removed permanently.")
        s.setStyleSheet(f"""
            color: {TEXT_DIM};
            font-size: 11.5px;
            background: transparent;
            border: none;
        """)
        s.setAlignment(Qt.AlignCenter)
        root.addWidget(s)

        root.addSpacing(12)

        # Action Buttons Row
        row = QHBoxLayout()
        row.setSpacing(10)

        cancel = QPushButton("Cancel")
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.setFixedHeight(34)
        cancel.setAutoDefault(False)
        cancel.setDefault(False)
        cancel.setFocusPolicy(Qt.NoFocus)
        cancel.setStyleSheet(f"""
            QPushButton {{
                background: {BG_CARD};
                color: {TEXT_MAIN};
                font-size: 12.5px;
                font-weight: 600;
                border: 1px solid {CARD_BORDER};
                border-radius: 8px;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background: {BTN_HOVER};
                border-color: {BORDER};
                color: #ffffff;
            }}
            QPushButton:pressed {{
                background: {BG_INPUT};
            }}
        """)
        cancel.clicked.connect(self.reject)

        delete = QPushButton("Delete")
        delete.setCursor(Qt.PointingHandCursor)
        delete.setFixedHeight(34)
        delete.setAutoDefault(False)
        delete.setDefault(False)
        delete.setFocusPolicy(Qt.NoFocus)
        delete.setStyleSheet("""
            QPushButton {{
                background: #eb3f3f;
                color: #ffffff;
                font-size: 12.5px;
                font-weight: 700;
                border: none;
                border-radius: 8px;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background: #d63131;
            }}
            QPushButton:pressed {{
                background: #b52424;
            }}
        """)
        delete.clicked.connect(self.accept)

        row.addWidget(cancel, 1)
        row.addWidget(delete, 1)
        root.addLayout(row)

        # Crisp pop-in opacity & appearance animation
        self._opacity_fx = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_fx)
        self._anim = QPropertyAnimation(self._opacity_fx, b"opacity")
        self._anim.setDuration(150)
        self._anim.setStartValue(0.15)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

        # Apply dark title bar with background color BG_MAIN and border color matching
        self._setup_titlebar()

    def _setup_titlebar(self):
        apply_dark_title_bar(self, BG_MAIN, TEXT_MAIN)
        QTimer.singleShot(30, lambda: apply_dark_title_bar(self, BG_MAIN, TEXT_MAIN))
        QTimer.singleShot(100, lambda: apply_dark_title_bar(self, BG_MAIN, TEXT_MAIN))

    def showEvent(self, event):
        super().showEvent(event)
        self._anim.start()
        self._setup_titlebar()
