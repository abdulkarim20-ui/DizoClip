from app.components.cards.ai_model_card import AIModelCard
from app.components.cards.command_card import CommandCard
from app.components.cards.key_card import KeyCard
from app.components.cards.link_card import LinkCard
from app.components.cards.prompt_card import PromptCard
from app.sections.ai_models.form import AIModelFormView
from app.sections.commands.form import CommandFormView
from app.sections.keys.form import FormView
from app.sections.links.form import LinkFormView
from app.sections.prompts.form import PromptFormView

SECTION_REGISTRY = {
    "key-round": {
        "title": "API Keys",
        "search_placeholder": "Search keys",
        "card_class": KeyCard,
        "form_class": FormView,
        "is_prompt": False,
        "empty_title": "No keys added yet",
        "empty_subtitle": "Store your API keys safely and\ncopy them with a single click.",
        "add_btn_text": "Add key",
    },
    "prompt": {
        "title": "Prompts",
        "search_placeholder": "Search prompts",
        "card_class": PromptCard,
        "form_class": PromptFormView,
        "is_prompt": True,
        "empty_title": "No prompts added yet",
        "empty_subtitle": "Save your favorite prompts and snippets\nfor instant copy and reuse.",
        "add_btn_text": "Add prompt",
    },
    "ai_model": {
        "title": "AI Models",
        "search_placeholder": "Search models",
        "card_class": AIModelCard,
        "form_class": AIModelFormView,
        "is_prompt": True,
        "empty_title": "No models added yet",
        "empty_subtitle": "Save your AI models and code snippets\nfor instant integration and reuse.",
        "add_btn_text": "Add model",
    },
    "sparkles-2": {
        "title": "AI Models",
        "search_placeholder": "Search models",
        "card_class": AIModelCard,
        "form_class": AIModelFormView,
        "is_prompt": True,
        "empty_title": "No models added yet",
        "empty_subtitle": "Save your AI models and code snippets\nfor instant integration and reuse.",
        "add_btn_text": "Add model",
    },
    "link": {
        "title": "Links",
        "search_placeholder": "Search links",
        "card_class": LinkCard,
        "form_class": LinkFormView,
        "is_prompt": False,
        "empty_title": "No links added yet",
        "empty_subtitle": "Save your most used URLs and bookmarks\nfor quick launch and copy.",
        "add_btn_text": "Add link",
    },
    "command": {
        "title": "Commands",
        "search_placeholder": "Search commands",
        "card_class": CommandCard,
        "form_class": CommandFormView,
        "is_prompt": False,
        "empty_title": "No commands added yet",
        "empty_subtitle": "Save commonly used CLI commands\nand terminal one-liners.",
        "add_btn_text": "Add command",
    },
}
