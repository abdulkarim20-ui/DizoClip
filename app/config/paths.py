"""
Application base directory and asset path resolvers.
User data paths are delegated to app.core.runtime.user_data_dir() as the single source of truth.
"""
import os
import sys


def base_dir() -> str:
    """Return the application base directory (supports PyInstaller bundles)."""
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    # Go up two levels from app/config/ to project root
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


ASSETS_DIR = os.path.join(base_dir(), "assets")


def data_dir() -> str:
    """
    Return the user data directory.
    Delegates directly to app.core.runtime.user_data_dir() as the single authority.
    """
    from app.core.runtime import user_data_dir
    return str(user_data_dir())


# Standard DC_ prefixed storage files
KEYS_FILE = os.path.join(data_dir(), "DC_Keys.json")
PROMPTS_FILE = os.path.join(data_dir(), "DC_Prompts.json")
AI_MODELS_FILE = os.path.join(data_dir(), "DC_AI_Models.json")
LINKS_FILE = os.path.join(data_dir(), "DC_Links.json")
COMMANDS_FILE = os.path.join(data_dir(), "DC_Commands.json")
SETTINGS_FILE = os.path.join(data_dir(), "DC_Settings.json")
CUSTOM_COLORS_FILE = os.path.join(data_dir(), "DC_Custom_Colors.json")

# Legacy filenames for automatic migration
LEGACY_KEYS_FILE = os.path.join(data_dir(), "keys.json")
LEGACY_PROMPTS_FILE = os.path.join(data_dir(), "prompts.json")
LEGACY_AI_MODELS_FILE = os.path.join(data_dir(), "ai_models.json")
LEGACY_LINKS_FILE = os.path.join(data_dir(), "links.json")
LEGACY_COMMANDS_FILE = os.path.join(data_dir(), "commands.json")
LEGACY_SETTINGS_FILE = os.path.join(data_dir(), "settings.json")
LEGACY_CUSTOM_COLORS_FILE = os.path.join(data_dir(), "custom_colors.json")

