"""
First-launch onboarding coordinator.
"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget

from app.components.dialogs.welcome import WelcomeDialog
from app.core.runtime import runtime_mode


def show_first_launch_if_needed(parent: QWidget, settings: dict, save_settings) -> bool:
    """
    Show onboarding exactly once per user-data directory.

    Returns True when the welcome dialog was shown.
    """
    if settings.get("welcome_seen", False):
        return False

    # Pass parent=None so WelcomeDialog is an unowned top-level window with its own taskbar button and icon
    dialog = WelcomeDialog(None, runtime_mode().value)
    dialog.exec()

    settings["welcome_seen"] = True
    save_settings()
    return True
