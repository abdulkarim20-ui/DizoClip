"""
Storage engine handling JSON data persistence for custom colors and legacy compatibility.
Provides backward-compatible adapters delegating to DataManager and direct custom color storage.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

from app.config.paths import CUSTOM_COLORS_FILE, LEGACY_CUSTOM_COLORS_FILE


def load_custom_colors_from_disk() -> List[str]:
    """Load custom colors from disk."""
    if os.path.exists(CUSTOM_COLORS_FILE):
        try:
            with open(CUSTOM_COLORS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return [c for c in data if isinstance(c, str) and c.startswith("#")]
            elif isinstance(data, dict) and "colors" in data:
                return [c for c in data["colors"] if isinstance(c, str) and c.startswith("#")]
        except (json.JSONDecodeError, OSError):
            pass

    if os.path.exists(LEGACY_CUSTOM_COLORS_FILE):
        try:
            with open(LEGACY_CUSTOM_COLORS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                valid = [c for c in data if isinstance(c, str) and c.startswith("#")]
                save_custom_colors_to_disk(valid)
                return valid
            elif isinstance(data, dict) and "colors" in data:
                valid = [c for c in data["colors"] if isinstance(c, str) and c.startswith("#")]
                save_custom_colors_to_disk(valid)
                return valid
        except (json.JSONDecodeError, OSError):
            pass

    return []


def save_custom_colors_to_disk(colors: List[str]) -> None:
    """Save custom colors to disk atomically."""
    tmp_path = CUSTOM_COLORS_FILE + ".tmp"
    try:
        os.makedirs(os.path.dirname(CUSTOM_COLORS_FILE), exist_ok=True)
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(colors, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, CUSTOM_COLORS_FILE)
    except OSError:
        log.warning("Could not save custom colors", exc_info=True)
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def add_custom_color_to_disk(color_hex: str, max_count: int = 8) -> List[str]:
    """Add a new custom color to disk (prepended, deduplicated, capped to 8)."""
    current = load_custom_colors_from_disk()
    color_hex = color_hex.lower().strip()
    if color_hex in current:
        current.remove(color_hex)
    current.insert(0, color_hex)
    current = current[:max_count]
    save_custom_colors_to_disk(current)
    return current


# Legacy compatibility wrappers
def load_keys_from_disk() -> List[Dict[str, Any]]:
    from app.core.data_manager import DataManager
    return DataManager().load_all()["keys"]


def save_keys_to_disk(keys: List[Dict[str, Any]]) -> None:
    from app.core.data_manager import DataManager
    DataManager().save("keys", keys)


def load_prompts_from_disk() -> List[Dict[str, Any]]:
    from app.core.data_manager import DataManager
    return DataManager().load_all()["prompts"]


def save_prompts_to_disk(prompts: List[Dict[str, Any]]) -> None:
    from app.core.data_manager import DataManager
    DataManager().save("prompts", prompts)


def load_links_from_disk() -> List[Dict[str, Any]]:
    from app.core.data_manager import DataManager
    return DataManager().load_all()["links"]


def save_links_to_disk(links: List[Dict[str, Any]]) -> None:
    from app.core.data_manager import DataManager
    DataManager().save("links", links)


def load_commands_from_disk() -> List[Dict[str, Any]]:
    from app.core.data_manager import DataManager
    return DataManager().load_all()["commands"]


def save_commands_to_disk(commands: List[Dict[str, Any]]) -> None:
    from app.core.data_manager import DataManager
    DataManager().save("commands", commands)


def load_ai_models_from_disk() -> List[Dict[str, Any]]:
    from app.core.data_manager import DataManager
    return DataManager().load_all()["ai_models"]


def save_ai_models_to_disk(models: List[Dict[str, Any]]) -> None:
    from app.core.data_manager import DataManager
    DataManager().save("ai_models", models)


def load_settings_from_disk() -> Dict[str, Any]:
    from app.core.data_manager import DataManager
    return DataManager().load_all()["settings"]


def save_settings_to_disk(settings: Dict[str, Any]) -> None:
    from app.core.data_manager import DataManager
    DataManager().save("settings", settings)
