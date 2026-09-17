"""
Modular Color Contrast and Luminance Validator for DizoClip.
Ensures custom badge colors maintain high contrast against dark UI backgrounds
and black badge text (#0b0d10), adhering to accessibility and UI visibility standards.
"""

from typing import Tuple, Union
from PySide6.QtGui import QColor

# UI background colors that badge chips must not blend into
DARK_UI_BACKGROUNDS = [
    QColor("#0f111a"),  # Main window background
    QColor("#141722"),  # Card background
    QColor("#1a1d27"),  # Elevated background
    QColor("#12141c"),  # Input background
]

BADGE_TEXT_COLOR = QColor("#0b0d10")  # Dark badge label text


def _relative_luminance(color: QColor) -> float:
    """Calculates relative luminance (0.0 to 1.0) according to WCAG 2.1 specs."""
    def channel_val(c: int) -> float:
        c_norm = c / 255.0
        return c_norm / 12.92 if c_norm <= 0.03928 else ((c_norm + 0.055) / 1.055) ** 2.4

    r = channel_val(color.red())
    g = channel_val(color.green())
    b = channel_val(color.blue())
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(lum1: float, lum2: float) -> float:
    """Calculates contrast ratio between two relative luminances."""
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    return (lighter + 0.05) / (darker + 0.05)


def _color_distance(c1: QColor, c2: QColor) -> float:
    """Euclidean distance in RGB color space."""
    dr = c1.red() - c2.red()
    dg = c1.green() - c2.green()
    db = c1.blue() - c2.blue()
    return (dr * dr + dg * dg + db * db) ** 0.5


def validate_badge_color(color: Union[QColor, str]) -> Tuple[bool, str]:
    """
    Validates whether a selected color meets UI visibility and contrast standards:
    - Must not blend into dark UI background (#0f111a, #141722, #1a1d27).
    - Must have sufficient contrast against black badge text (#0b0d10).
    - Minimum brightness / luminance threshold.

    Returns:
        (is_valid: bool, warning_message: str)
    """
    if isinstance(color, str):
        col = QColor(color)
    else:
        col = color

    if not col.isValid():
        return False, "Invalid color value."

    # 1. Check brightness and value
    # Perceived brightness (0..255)
    perceived_brightness = (0.299 * col.red() + 0.587 * col.green() + 0.114 * col.blue())
    hsv_value = col.valueF()  # 0.0 to 1.0

    if perceived_brightness < 70 or hsv_value < 0.35:
        return False, "Color is too dark. Dark colors blend into the UI background and make label text unreadable."

    # 2. Check contrast ratio against black badge text (#0b0d10)
    badge_lum = _relative_luminance(col)
    text_lum = _relative_luminance(BADGE_TEXT_COLOR)
    contrast_with_text = _contrast_ratio(badge_lum, text_lum)

    if contrast_with_text < 2.8:
        return False, "Insufficient contrast. Badge text will not be visible on this dark shade. Pick a brighter color."

    # 3. Check similarity to UI dark backgrounds
    for ui_bg in DARK_UI_BACKGROUNDS:
        dist = _color_distance(col, ui_bg)
        if dist < 45.0:
            return False, "Color matches the UI background and will be invisible in cards. Choose a more distinct color."

    return True, ""
