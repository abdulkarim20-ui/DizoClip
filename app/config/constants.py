"""
Constants, dimensions, default settings, and seed datasets for DizoClip.
"""

# Fixed window dimensions:
# - WINDOW_W = 360 (Standard width across all modules)
# - WINDOW_H_KEYS_3 = 405 (Fixed height displaying 3 item cards or exactly 4 settings cards)
# - WINDOW_H_PROMPTS_3 = 423 (Fixed height for prompt cards)
# - WINDOW_H_SETTINGS = 405 (Fixed height for settings view displaying exactly 4 cards; extra cards use scrollbar)
WINDOW_W = 360
WINDOW_H_EMPTY = 360
WINDOW_H_SETTINGS = 430
WINDOW_H_KEYS_3 = 405
WINDOW_H_PROMPTS_3 = 423
WINDOW_H_PROMPT_FORM = 425
WINDOW_H_AI_MODEL_FORM = 455

CARD_W = 326
CLIPBOARD_CLEAR_SECONDS = 30
CARD_BORDER = "#252b38"
KEY_CARD_H = 76
PROMPT_CARD_H = 82
AI_MODEL_CARD_H = 82
LINK_CARD_H = 76
COMMAND_CARD_H = 82

BADGE_COLORS = [
    "#e8794a", "#4a7ce8", "#4ae87c", "#e84a4a",
    "#4ab8e8", "#a44ae8", "#4ae8c9", "#e84a9c"
]

DEFAULT_SETTINGS = {
    "always_on_top": False,
    "confirm_delete": True,
    "auto_clear_clipboard": True,
    "encrypt_all_data": True,
    "startup_module": "key-round",
    "section_order": ["key-round", "prompt", "ai_model", "link", "command"],
    "enabled_sections": ["key-round", "prompt", "ai_model", "link", "command"],
}

DEFAULT_SEED_KEYS = []
DEFAULT_SEED_PROMPTS = []
DEFAULT_SEED_LINKS = []
DEFAULT_SEED_COMMANDS = []
DEFAULT_SEED_AI_MODELS = []
