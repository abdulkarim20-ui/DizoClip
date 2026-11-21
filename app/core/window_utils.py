"""
Native OS window utilities (Windows dark mode title bar & Always-on-Top).
"""

import sys
from PySide6.QtGui import QColor

from app.config.theme import BG_MAIN, TEXT_MAIN, WINDOW_BORDER


def setup_app_user_model_id(app_id: str = "AbdulKarim.DizoClip.1.0") -> None:
    """Set Windows taskbar grouping ID so the custom logo appears on the taskbar."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception:
            pass


def apply_dark_title_bar(
    window,
    bg_hex: str = BG_MAIN,
    text_hex: str = TEXT_MAIN,
    border_hex: str = WINDOW_BORDER,
) -> None:
    """Set the native Windows 10/11 title bar and caption text colors directly."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        hwnd = int(window.winId())
        if not hwnd:
            return

        # Guard: only apply once per window to prevent DWM thrashing and flicker
        if getattr(window, "_dark_titlebar_applied", False):
            return

        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        DWMWA_BORDER_COLOR = 34
        DWMWA_CAPTION_COLOR = 35
        DWMWA_TEXT_COLOR = 36

        # Force immersive dark mode (1 = TRUE)
        dark_mode = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(dark_mode), ctypes.sizeof(dark_mode)
        )

        # Apply rounded corners (DWMWCP_ROUND = 2) for modern Windows 11 look
        corner_pref = ctypes.c_int(2)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, ctypes.byref(corner_pref), ctypes.sizeof(corner_pref)
        )

        # Apply custom background color to the titlebar caption (BGR conversion)
        qc = QColor(bg_hex)
        caption_color = ctypes.c_int((qc.blue() << 16) | (qc.green() << 8) | qc.red())
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_CAPTION_COLOR, ctypes.byref(caption_color), ctypes.sizeof(caption_color)
        )

        # Apply custom text color to the titlebar caption
        qt = QColor(text_hex)
        text_color = ctypes.c_int((qt.blue() << 16) | (qt.green() << 8) | qt.red())
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_TEXT_COLOR, ctypes.byref(text_color), ctypes.sizeof(text_color)
        )

        # Apply slim window border color
        qb = QColor(border_hex)
        border_color = ctypes.c_int((qb.blue() << 16) | (qb.green() << 8) | qb.red())
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_BORDER_COLOR, ctypes.byref(border_color), ctypes.sizeof(border_color)
        )

        # Clear WS_POPUP from the window style so Windows 11 DWM recognizes it as a standard
        # WS_OVERLAPPED desktop window and plays the smooth native open/close scale & fade animation
        try:
            GWL_STYLE = -16
            WS_POPUP = 0x80000000
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
            if style & WS_POPUP:
                new_style = style & ~WS_POPUP
                if new_style >= 0x80000000:
                    new_style -= 0x100000000
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, ctypes.c_long(new_style))
                # Frame changed notification to update non-client area without moving/resizing
                SWP_NOMOVE = 0x0002
                SWP_NOSIZE = 0x0001
                SWP_NOZORDER = 0x0004
                SWP_FRAMECHANGED = 0x0020
                SWP_NOACTIVATE = 0x0010
                ctypes.windll.user32.SetWindowPos(
                    hwnd, 0, 0, 0, 0, 0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED | SWP_NOACTIVATE
                )
        except Exception:
            pass

        window._dark_titlebar_applied = True
    except Exception:
        pass


def toggle_always_on_top(window, enable: bool) -> None:
    """Toggle Always-on-Top without recreating the native Win32 window handle."""
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            hwnd = wintypes.HWND(int(window.winId()))
            HWND_TOPMOST = ctypes.c_void_p(-1)
            HWND_NOTOPMOST = ctypes.c_void_p(-2)
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOACTIVATE = 0x0010
            flags = SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE

            target = HWND_TOPMOST if enable else HWND_NOTOPMOST
            ctypes.windll.user32.SetWindowPos(hwnd, target, 0, 0, 0, 0, flags)
            return
        except Exception:
            pass

    from PySide6.QtCore import Qt
    qw = window.windowHandle()
    if qw:
        qw.setFlag(Qt.WindowStaysOnTopHint, enable)
    else:
        window.setWindowFlag(Qt.WindowStaysOnTopHint, enable)
        window.show()


def ensure_taskbar_icon(window) -> None:
    """Ensure the native Windows window has the taskbar style and icon."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        import os
        from app.config.paths import ASSETS_DIR

        hwnd = int(window.winId())
        if not hwnd:
            return

        GWL_EXSTYLE = -20
        WS_EX_APPWINDOW = 0x00040000
        WS_EX_TOOLWINDOW = 0x00000080
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style = (style & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

        ico_path = os.path.join(ASSETS_DIR, "app_logo.ico")
        if os.path.exists(ico_path):
            IMAGE_ICON = 1
            LR_LOADFROMFILE = 0x00000010
            WM_SETICON = 0x0080
            ICON_SMALL = 0
            ICON_BIG = 1

            h_big = ctypes.windll.user32.LoadImageW(None, ico_path, IMAGE_ICON, 32, 32, LR_LOADFROMFILE)
            h_small = ctypes.windll.user32.LoadImageW(None, ico_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
            if h_big:
                ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, h_big)
            if h_small:
                ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, h_small)
    except Exception:
        pass

