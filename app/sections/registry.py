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


def _has(text, *values):
    # Non-text values (hand-edited or damaged data) are ignored instead of crashing the search.
    return any(text in v.lower() for v in values if isinstance(v, str))


def _snippet_values(model):
    snippets = model.get("snippets")
    return snippets.values() if isinstance(snippets, dict) else ()


_MATCHERS = {
    "key-round": lambda k, t: _has(t, k.get("label")),
    "prompt": lambda p, t: _has(t, p.get("name") or p.get("title"), p.get("prompt") or p.get("content")),
    "ai_model": lambda m, t: _has(t, m.get("name"), m.get("provider"), *_snippet_values(m)),
    "link": lambda l, t: _has(t, l.get("title"), l.get("url")),
    "command": lambda c, t: _has(t, c.get("title"), c.get("command")),
}

_WIRING = {
    "key-round": dict(items_attr="keys", save_attr="save_keys", copy_attr="copy_key",
                      edit_attr="show_edit_view", delete_attr="confirm_delete_key"),
    "prompt": dict(items_attr="prompts", save_attr="save_prompts", copy_attr="copy_prompt",
                   edit_attr="show_edit_prompt_view", delete_attr="confirm_delete_prompt"),
    "ai_model": dict(items_attr="ai_models", save_attr="save_ai_models", copy_attr="copy_ai_model",
                     edit_attr="show_edit_ai_model_view", delete_attr="confirm_delete_ai_model"),
    "link": dict(items_attr="links", save_attr="save_links", copy_attr="copy_link",
                 edit_attr="show_edit_link_view", delete_attr="confirm_delete_link",
                 card_kwargs=lambda win: {"on_open": win.open_link}),
    "command": dict(items_attr="commands", save_attr="save_commands", copy_attr="copy_command",
                    edit_attr="show_edit_command_view", delete_attr="confirm_delete_command"),
}

for _id, _match in _MATCHERS.items():
    SECTION_REGISTRY[_id]["match"] = _match
    SECTION_REGISTRY[_id].update(_WIRING[_id])
SECTION_REGISTRY["sparkles-2"] = SECTION_REGISTRY["ai_model"]  # legacy alias
