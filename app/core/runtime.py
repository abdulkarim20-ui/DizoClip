r"""
DizoClip runtime mode detection.

Portable mode:
    A file named ``portable.flag`` exists beside the executable.

Installed mode:
    Frozen Windows executable without portable.flag -> %APPDATA%\DizoClip\User_Data

Development mode:
    Running from source -> <project>/User_Data

This module never writes user data by itself.
"""
from __future__ import annotations

import os
import sys
from enum import Enum
from pathlib import Path


class RuntimeMode(str, Enum):
    DEVELOPMENT = "development"
    PORTABLE = "portable"
    INSTALLED = "installed"


APP_NAME = "DizoClip"
PORTABLE_FLAG = "portable.flag"
DATA_DIR_ENV = "DIZOCLIP_DATA_DIR"


def app_dir() -> Path:
    """Directory containing the source tree or frozen executable."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def is_portable() -> bool:
    """Portable is enabled either by portable.flag beside the executable or if executable name contains 'portable'."""
    return (app_dir() / PORTABLE_FLAG).is_file() or "portable" in Path(sys.executable).stem.lower()


def runtime_mode() -> RuntimeMode:
    if not getattr(sys, "frozen", False):
        return RuntimeMode.DEVELOPMENT
    return RuntimeMode.PORTABLE if is_portable() else RuntimeMode.INSTALLED


def user_data_dir() -> Path:
    """
    Return the durable per-user data directory.

    DIZOCLIP_DATA_DIR overrides everything (used by tests and benchmarks so they
    can never touch real user data).
    """
    override = os.environ.get(DATA_DIR_ENV)
    if override:
        path = Path(override).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    mode = runtime_mode()

    if mode in (RuntimeMode.DEVELOPMENT, RuntimeMode.PORTABLE):
        path = app_dir() / "User_Data"
    else:
        appdata = os.environ.get("APPDATA")
        if not appdata:
            appdata = str(Path.home() / "AppData" / "Roaming")
        path = Path(appdata) / APP_NAME / "User_Data"

    path.mkdir(parents=True, exist_ok=True)
    return path


def runtime_info() -> dict[str, str]:
    mode = runtime_mode()
    return {
        "mode": mode.value,
        "app_dir": str(app_dir()),
        "user_data_dir": str(user_data_dir()),
    }
