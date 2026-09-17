"""
SVG and PNG icon loading, rendering, and caching with dynamic color tinting.
"""

import os
import re
from typing import Dict, Optional, Tuple

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from app.config.paths import ASSETS_DIR
from app.config.theme import DANGER, SUCCESS, TEXT_DIM, TEXT_MAIN

_ICON_DPR = 2.0
_PIXMAP_CACHE: Dict[Tuple[str, int, int, str], Optional[QPixmap]] = {}
_CACHE_LIMIT = 512


def _cache_get(key):
    value = _PIXMAP_CACHE.get(key)
    return QPixmap(value) if value is not None else None


def _cache_put(key, value):
    if len(_PIXMAP_CACHE) >= _CACHE_LIMIT:
        _PIXMAP_CACHE.pop(next(iter(_PIXMAP_CACHE)))
    _PIXMAP_CACHE[key] = QPixmap(value) if value is not None else None
    return QPixmap(value) if value is not None else None


def render_pixmap(name: str, size: Tuple[int, int], color: Optional[str] = None) -> Optional[QPixmap]:
    """Render an SVG or PNG asset from ASSETS_DIR with optional color tinting."""
    base_name = os.path.splitext(name)[0]
    w, h = size
    cache_key = (base_name, int(w), int(h), color or "")
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    svg_path = os.path.join(ASSETS_DIR, f"{base_name}.svg")
    png_path = os.path.join(ASSETS_DIR, f"{base_name}.png")

    if os.path.exists(svg_path):
        try:
            with open(svg_path, "r", encoding="utf-8") as f:
                svg = f.read()

            if color:
                # Tint stroke colors (except stroke="none")
                svg = re.sub(r'stroke="(?!none")[^"]*"', f'stroke="{color}"', svg)
                # Tint fills (except fill="none")
                svg = re.sub(r'fill="(?!none")[^"]*"', f'fill="{color}"', svg)

            renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
            if renderer.isValid():
                pm = QPixmap(int(w * _ICON_DPR), int(h * _ICON_DPR))
                pm.fill(Qt.transparent)
                painter = QPainter(pm)
                renderer.render(painter)
                painter.end()
                pm.setDevicePixelRatio(_ICON_DPR)
                return _cache_put(cache_key, pm)
        except (OSError, RuntimeError, ValueError):
            pass

    if os.path.exists(png_path):
        try:
            pm = QPixmap(png_path)
            if not pm.isNull():
                if color:
                    tinted = QPixmap(pm.size())
                    tinted.fill(Qt.transparent)
                    painter = QPainter(tinted)
                    painter.drawPixmap(0, 0, pm)
                    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
                    painter.fillRect(tinted.rect(), QColor(color))
                    painter.end()
                    pm = tinted
                pm = pm.scaled(int(w * _ICON_DPR), int(h * _ICON_DPR),
                               Qt.KeepAspectRatio, Qt.SmoothTransformation)
                pm.setDevicePixelRatio(_ICON_DPR)
                return _cache_put(cache_key, pm)
        except (OSError, RuntimeError, ValueError):
            pass
    _PIXMAP_CACHE[cache_key] = None
    return None


def render_padded_pixmap(
    name: str,
    icon_size: Tuple[int, int],
    canvas_size: Tuple[int, int],
    color: Optional[str] = None,
    pad_right: int = 6,
    pad_left: int = 0,
) -> Optional[QPixmap]:
    """Render an SVG asset with extra transparent padding for spacing in toolbars/inputs."""
    base_name = os.path.splitext(name)[0]
    iw, ih = icon_size
    cw, ch = canvas_size
    cache_key = (f"{base_name}:padded:{pad_left}:{pad_right}", int(cw), int(ch), color or "")
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    svg_path = os.path.join(ASSETS_DIR, f"{base_name}.svg")
    if not os.path.exists(svg_path):
        return render_pixmap(name, icon_size, color)

    try:
        with open(svg_path, "r", encoding="utf-8") as f:
            svg = f.read()

        if color:
            svg = re.sub(r'stroke="(?!none")[^"]*"', f'stroke="{color}"', svg)
            svg = re.sub(r'fill="(?!none")[^"]*"', f'fill="{color}"', svg)

        renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
        if not renderer.isValid():
            return None

        pm = QPixmap(int(cw * _ICON_DPR), int(ch * _ICON_DPR))
        pm.fill(Qt.transparent)

        from PySide6.QtCore import QRectF
        x = pad_left
        y = max(0, (ch - ih) // 2)

        painter = QPainter(pm)
        renderer.render(painter, QRectF(x * _ICON_DPR, y * _ICON_DPR, iw * _ICON_DPR, ih * _ICON_DPR))
        painter.end()
        pm.setDevicePixelRatio(_ICON_DPR)
        return _cache_put(cache_key, pm)
    except (OSError, RuntimeError, ValueError):
        return render_pixmap(name, icon_size, color)


def load_icon(name: str, size: Tuple[int, int] = (16, 16), color: Optional[str] = None) -> Optional[QIcon]:
    """Load a QIcon from an asset name, scaled and tinted."""
    pm = render_pixmap(name, size, color)
    return QIcon(pm) if pm is not None else None


class IconManager:
    """Central registry and cache for application icons."""
    def __init__(self):
        self._icons: Dict[str, Optional[QIcon]] = {}
        self.load_all()

    def load_all(self):
        self._icons = {
            "plus": load_icon("plus", (15, 15)),
            "copy": load_icon("copy", (14, 14), color="#8f97a8"),
            "check": load_icon("check", (14, 14), color="#8f97a8"),
            "pencil": load_icon("pencil", (14, 14)),
            "trash": load_icon("trash", (14, 14)),
            "trash_danger": load_icon("trash", (28, 28), color=DANGER),
            "ellipsis": load_icon("ellipsis-vertical", (14, 14), color="#727b8e"),
            "eye": load_icon("eye", (16, 16), color=TEXT_DIM),
            "eye_closed": load_icon("eye-closed", (16, 16), color=TEXT_DIM),
            "search": load_icon("search", (15, 15), color=TEXT_DIM),
            "back": load_icon("arrow-left", (15, 15)),
            "settings": load_icon("settings", (16, 16)),
            "prompt": load_icon("prompt", (16, 16)),
            "link": load_icon("link", (16, 16)),
            "globe": load_icon("globe", (14, 14)),
            "command": load_icon("command", (16, 16)),
            "sparkles": load_icon("sparkles-2", (14, 14)),
            "chevron-down": load_icon("chevron-down", (12, 12)),
            "chevron-up": load_icon("chevron-up", (12, 12)),
        }

    def get(self, name: str) -> Optional[QIcon]:
        return self._icons.get(name)

    def __getitem__(self, item: str) -> Optional[QIcon]:
        return self.get(item)
