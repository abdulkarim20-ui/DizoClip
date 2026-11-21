"""
File logging for DizoClip: User_Data/Logs/dizoclip.log (rotating, 3 x 512 KB).

RULE: never log secret values (keys, prompt text, snippets). Log names and paths only.
"""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.runtime import user_data_dir


def setup_logging() -> Path:
    log_dir = user_data_dir() / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "dizoclip.log"

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if not any(isinstance(h, RotatingFileHandler) for h in root.handlers):
        handler = RotatingFileHandler(log_file, maxBytes=512_000, backupCount=3, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        root.addHandler(handler)

    def _hook(exc_type, exc, tb):
        logging.getLogger("dizoclip").critical("Uncaught exception", exc_info=(exc_type, exc, tb))
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = _hook
    return log_file
