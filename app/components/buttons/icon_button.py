from typing import Optional

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QToolButton

from app.components.labels.animated_tooltip import attach_tooltip, set_tooltip

ICON_BUTTON_SIZE = 24
ICON_SIZE = 14


def icon_button(
    icon: Optional[QIcon],
    fallback: str = "",
    tooltip: str = "",
    size: int = ICON_BUTTON_SIZE,
    icon_size: int = ICON_SIZE,
    object_name: str = "",
) -> QToolButton:
    """
    Create a reusable icon-only button with animated custom tooltip.

    Guarantees:
    - fixed clickable area
    - no stylesheet padding
    - centered icon
    - consistent icon dimensions
    - no layout shrinking
    - matching UI animated tooltip
    """
    btn = QToolButton()

    # Fixed clickable area
    btn.setFixedSize(size, size)
    btn.setMinimumSize(size, size)
    btn.setMaximumSize(size, size)

    # Explicit icon geometry
    btn.setIconSize(QSize(icon_size, icon_size))

    # Prevent Qt from treating this like a text/tool button
    btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
    btn.setAutoRaise(True)

    btn.setCursor(Qt.PointingHandCursor)
    btn.setFocusPolicy(Qt.NoFocus)

    if object_name:
        btn.setObjectName(object_name)
    else:
        btn.setProperty("cls", "icon")

    # Reusable stylesheet with support for standard icon button and menu role
    btn.setStyleSheet(f"""
        QToolButton {{
            background: transparent;
            border: none;
            padding: 0px;
            margin: 0px;
            min-width: {size}px;
            max-width: {size}px;
            min-height: {size}px;
            max-height: {size}px;
            qproperty-iconSize: {icon_size}px {icon_size}px;
        }}

        QToolButton:hover {{
            background: #242938;
            border-radius: 6px;
        }}

        QToolButton:pressed {{
            background: #2d3345;
            border-radius: 6px;
        }}

        QToolButton[buttonRole="menu"] {{
            color: #727b8e;
            background: transparent;
        }}

        QToolButton[buttonRole="menu"]:hover {{
            color: #e2e8f0;
            background: #242938;
        }}

        QToolButton[buttonRole="menu"]:pressed {{
            background: #2d3345;
        }}
    """)

    if icon is not None and not icon.isNull():
        btn.setIcon(icon)
    else:
        btn.setText(fallback)

    # Intercept setToolTip to use custom animated tooltip automatically
    btn.setToolTip = lambda text: set_tooltip(btn, text, placement="auto")

    if tooltip:
        set_tooltip(btn, tooltip, placement="auto")

    return btn


def set_button_tooltip(btn: QToolButton, text: str) -> None:
    """Update tooltip text for an icon button dynamically using custom animated tooltip."""
    set_tooltip(btn, text, placement="auto")
