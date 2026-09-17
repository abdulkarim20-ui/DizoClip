"""
Font discovery and application font loading for DizoClip.
"""
import os
from PySide6.QtGui import QFontDatabase
from app.config.paths import ASSETS_DIR


def load_app_fonts():
    """Register bundled fonts from assets/fonts into QFontDatabase."""
    fonts_dir = os.path.join(ASSETS_DIR, "fonts")
    if not os.path.exists(fonts_dir):
        return
    for fname in os.listdir(fonts_dir):
        if fname.lower().endswith((".ttf", ".otf")):
            QFontDatabase.addApplicationFont(os.path.join(fonts_dir, fname))
