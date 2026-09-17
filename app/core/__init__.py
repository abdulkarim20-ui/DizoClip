"""Core services exposed through lazy imports to keep package startup lightweight."""

_EXPORTS = {
    "copy_to_clipboard": ("app.core.clipboard", "copy_to_clipboard"),
    "show_copy_feedback": ("app.core.clipboard", "show_copy_feedback"),
    "IconManager": ("app.core.icons", "IconManager"),
    "load_icon": ("app.core.icons", "load_icon"),
    "render_pixmap": ("app.core.icons", "render_pixmap"),
    "apply_dark_title_bar": ("app.core.window_utils", "apply_dark_title_bar"),
    "setup_app_user_model_id": ("app.core.window_utils", "setup_app_user_model_id"),
    "toggle_always_on_top": ("app.core.window_utils", "toggle_always_on_top"),
    "DataManager": ("app.core.data_manager", "DataManager"),
    "DataError": ("app.core.data_manager", "DataError"),
    "RuntimeMode": ("app.core.runtime", "RuntimeMode"),
    "BackupManager": ("app.core.backup_manager", "BackupManager"),
    "load_custom_colors_from_disk": ("app.core.storage", "load_custom_colors_from_disk"),
    "save_custom_colors_to_disk": ("app.core.storage", "save_custom_colors_to_disk"),
    "add_custom_color_to_disk": ("app.core.storage", "add_custom_color_to_disk"),
    "load_commands_from_disk": ("app.core.storage", "load_commands_from_disk"),
    "load_keys_from_disk": ("app.core.storage", "load_keys_from_disk"),
    "load_links_from_disk": ("app.core.storage", "load_links_from_disk"),
    "load_prompts_from_disk": ("app.core.storage", "load_prompts_from_disk"),
    "load_settings_from_disk": ("app.core.storage", "load_settings_from_disk"),
    "save_commands_to_disk": ("app.core.storage", "save_commands_to_disk"),
    "save_keys_to_disk": ("app.core.storage", "save_keys_to_disk"),
    "save_links_to_disk": ("app.core.storage", "save_links_to_disk"),
    "save_prompts_to_disk": ("app.core.storage", "save_prompts_to_disk"),
    "save_settings_to_disk": ("app.core.storage", "save_settings_to_disk"),
}


__all__ = list(_EXPORTS)


def __getattr__(name):
    try:
        module_name, attr_name = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(name) from exc
    from importlib import import_module
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
