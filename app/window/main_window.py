import logging
import os
import sys
from pathlib import Path

from PySide6.QtCore import (
    QEasingCurve,
    QEvent,
    QPropertyAnimation,
    QSize,
    Qt,
    QTimer,
)
from PySide6.QtGui import QCloseEvent, QColor, QGuiApplication, QIcon, QKeySequence, QPainter, QShortcut
from PySide6.QtWidgets import (
    QDialog,
    QGraphicsOpacityEffect,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
)

from app.components.dialogs.confirm_delete import ConfirmDeleteDialog
from app.config.constants import (
    CLIPBOARD_CLEAR_SECONDS,
    WINDOW_H_AI_MODEL_FORM,
    WINDOW_H_EMPTY,
    WINDOW_H_KEYS_3,
    WINDOW_H_PROMPT_FORM,
    WINDOW_H_SETTINGS,
    WINDOW_W,
)
from app.config.paths import ASSETS_DIR
from app.config.theme import BG_MAIN, TEXT_MAIN
from app.core.clipboard import ClipboardGuard, copy_to_clipboard
from app.core.export_import import (
    EXPORT_DATASETS,
    ExportStats,
    ImportPlan,
    apply_plan,
    export_to_file,
    plan_import,
    read_bundle,
)
from app.core.icons import IconManager
from app.core.data_manager import DataError, DataManager
from app.core.masking import looks_masked
from app.core.memory_trim import trim_working_set
from app.core.window_utils import apply_dark_title_bar, toggle_always_on_top
from app.core.window_transition import prepare_window_for_native_transition
from app.sections.ai_models.form import AIModelFormView
from app.sections.commands.form import CommandFormView
from app.sections.keys.form import FormView
from app.sections.links.form import LinkFormView
from app.sections.prompts.form import PromptFormView
from app.views.list_view import ListView
from app.views.settings_view import SettingsView
from app.views.welcome_view import WelcomeView

log = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    WINDOW_W = WINDOW_W
    WINDOW_H_EMPTY = WINDOW_H_EMPTY
    WINDOW_H_SETTINGS = WINDOW_H_SETTINGS
    WINDOW_H_WELCOME = 328
    WINDOW_H_KEYS_3 = 405
    WINDOW_H_PROMPTS_3 = 423
    WINDOW_H_PROMPT_FORM = WINDOW_H_PROMPT_FORM
    WINDOW_H_AI_MODEL_FORM = WINDOW_H_AI_MODEL_FORM

    def __init__(self, data_manager=None, datasets=None):
        super().__init__()
        self.setWindowTitle("DizoClip")
        self.setFixedSize(self.WINDOW_W, self.WINDOW_H_KEYS_3)

        self._resize_anim = None

        # main.py normally loads data through load_with_recovery() and passes it in.
        self.data_manager = data_manager or DataManager()
        if datasets is None:
            datasets = self.data_manager.load_all()  # raises DataError if unreadable

        self.settings = datasets["settings"]
        self.keys = datasets["keys"]
        self.prompts = datasets["prompts"]
        self.ai_models = datasets["ai_models"]
        self.links = datasets["links"]
        self.commands = datasets["commands"]
        self.custom_colors = datasets["custom_colors"]

        init_flags = (
            Qt.Window
            | Qt.CustomizeWindowHint
            | Qt.WindowTitleHint
            | Qt.WindowSystemMenuHint
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowCloseButtonHint
        )
        if self.settings.get("always_on_top", False):
            init_flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(init_flags)

        ico_path = os.path.join(ASSETS_DIR, "app_logo.ico")
        png_path = os.path.join(ASSETS_DIR, "app_logo.png")
        if os.path.exists(ico_path):
            self.setWindowIcon(QIcon(ico_path))
        elif os.path.exists(png_path):
            self.setWindowIcon(QIcon(png_path))

        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setStyleSheet(f"QMainWindow {{ background-color: {BG_MAIN}; }}")
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), QColor(BG_MAIN))
        self.setPalette(pal)

        self.icons = IconManager()
        self.clipboard_guard = ClipboardGuard(self)

        self.stack = QStackedWidget()
        self.stack.setAutoFillBackground(True)
        stack_pal = self.stack.palette()
        stack_pal.setColor(self.stack.backgroundRole(), QColor(BG_MAIN))
        self.stack.setPalette(stack_pal)
        self.stack.setStyleSheet(f"QStackedWidget {{ background-color: {BG_MAIN}; }}")

        # Only the list view exists at start-up. Forms, Settings and Welcome are built the first
        # time they are opened (see the properties below): less to construct before the first
        # frame, and widgets that are never opened never cost any memory.
        self._form_view = None
        self._prompt_form_view = None
        self._ai_model_form_view = None
        self._link_form_view = None
        self._command_form_view = None
        self._settings_view = None
        self._welcome_view = None

        self.list_view = ListView(self)
        self.stack.addWidget(self.list_view)
        self.setCentralWidget(self.stack)

        self._setup_titlebar_color()

        all_available = ["key-round", "prompt", "ai_model", "link", "command"]
        initial_mod = self.settings.get("startup_module", "key-round")
        enabled = self.settings.get("enabled_sections", all_available)
        if initial_mod not in enabled:
            order = self.settings.get("section_order", all_available)
            valid = [k for k in order if k in enabled]
            initial_mod = valid[0] if valid else "key-round"

        if not self.settings.get("welcome_seen", False):
            self.show_welcome_view(animate=False)
        else:
            self.list_view.select_tab(initial_mod, animate=False)
            self.show_list_view(animate=False)

        QShortcut(QKeySequence("Escape"), self, activated=self._on_escape)

    # ------------------------------------------------------------ lazy views
    def _lazy_view(self, attr: str, factory):
        view = getattr(self, attr)
        if view is None:
            view = factory(self)
            setattr(self, attr, view)
            self.stack.addWidget(view)
        return view

    @property
    def form_view(self):
        return self._lazy_view("_form_view", FormView)

    @property
    def prompt_form_view(self):
        return self._lazy_view("_prompt_form_view", PromptFormView)

    @property
    def ai_model_form_view(self):
        return self._lazy_view("_ai_model_form_view", AIModelFormView)

    @property
    def link_form_view(self):
        return self._lazy_view("_link_form_view", LinkFormView)

    @property
    def command_form_view(self):
        return self._lazy_view("_command_form_view", CommandFormView)

    @property
    def settings_view(self):
        return self._lazy_view("_settings_view", SettingsView)

    @property
    def welcome_view(self):
        return self._lazy_view("_welcome_view", WelcomeView)

    def _setup_titlebar_color(self):
        """
        Prepare the native Windows titlebar and DWM appearance.

        This is intentionally called before the first show().
        """
        from app.config.theme import BG_MAIN, TEXT_MAIN, WINDOW_BORDER

        prepare_window_for_native_transition(
            self,
            BG_MAIN,
            TEXT_MAIN,
            WINDOW_BORDER,
        )

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(event.rect(), QColor(BG_MAIN))
        p.end()

    def showEvent(self, event):
        """
        First show is intentionally passive.

        Native Windows/DWM handles the desktop-window transition.
        We do not start a Qt opacity animation here.
        """
        super().showEvent(event)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.WindowStateChange and self.isMinimized():
            QTimer.singleShot(1000, lambda: trim_working_set() if self.isMinimized() else None)

    def closeEvent(self, event: QCloseEvent):
        """Save, hide, quit. Refuses to lose settings silently."""
        event.ignore()  # we close ourselves after the animation

        self.clipboard_guard.flush()  # never leave a copied key behind

        if not self.save_settings():
            reply = QMessageBox.question(
                self,
                "DizoClip",
                "Your settings could not be saved (see the message above).\n\nQuit anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

        # Hide first (Windows plays its native close transition), then quit straight away.
        from PySide6.QtWidgets import QApplication
        self.hide()
        QApplication.quit()

    def animate_to_height(self, target_h):
        current_size = self.size()
        target_size = QSize(self.WINDOW_W, target_h)

        if current_size == target_size:
            return

        self.setMinimumSize(self.WINDOW_W, min(current_size.height(), target_h))
        self.setMaximumSize(self.WINDOW_W, max(current_size.height(), target_h))

        if self._resize_anim is not None:
            self._resize_anim.stop()

        self._resize_anim = QPropertyAnimation(self, b"size")
        self._resize_anim.setDuration(160)
        self._resize_anim.setStartValue(current_size)
        self._resize_anim.setEndValue(target_size)
        self._resize_anim.setEasingCurve(QEasingCurve.OutCubic)

        def _on_finish():
            self.setFixedSize(self.WINDOW_W, target_h)
            self._resize_anim = None
            self.update()

        self._resize_anim.finished.connect(_on_finish)
        self._resize_anim.start()

    def update_size_for_count(self, count, is_prompt=False, animate=True):
        if count == 0:
            target_h = self.WINDOW_H_EMPTY
        elif count == 1:
            target_h = 243 if is_prompt else 237
        elif count == 2:
            target_h = 333 if is_prompt else 321
        else:
            target_h = self.WINDOW_H_PROMPTS_3 if is_prompt else self.WINDOW_H_KEYS_3

        if not animate:
            if self._resize_anim is not None:
                self._resize_anim.stop()
            self.setFixedSize(self.WINDOW_W, target_h)
            return

        self.animate_to_height(target_h)

    def fade_to_widget(self, widget):
        if self.stack.currentWidget() == widget:
            return

        if hasattr(self, "anim") and self.anim is not None:
            self.anim.stop()
            if hasattr(self, "effect") and self.effect is not None:
                self.stack.setGraphicsEffect(None)
                self.effect = None
                self.anim = None

        self.stack.setCurrentWidget(widget)

        self.effect = QGraphicsOpacityEffect(self.stack)
        self.stack.setGraphicsEffect(self.effect)

        self.anim = QPropertyAnimation(self.effect, b"opacity")
        self.anim.setDuration(120)
        self.anim.setStartValue(0.85)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

        def _cleanup():
            self.stack.setGraphicsEffect(None)
            self.effect = None
            self.anim = None

        self.anim.finished.connect(_cleanup)
        self.anim.start()

    def show_list_view(self, animate: bool = True):
        if animate:
            self.fade_to_widget(self.list_view)
        else:
            self.stack.setCurrentWidget(self.list_view)
        self.list_view.search.blockSignals(True)
        self.list_view.search.clear()
        self.list_view.search.blockSignals(False)
        self.list_view.rebuild(animate_resize=animate)

    def show_add_view(self):
        self.update_size_for_count(3, is_prompt=False)
        self.form_view.edit(None)
        self.fade_to_widget(self.form_view)

    def show_edit_view(self, key):
        self.update_size_for_count(3, is_prompt=False)
        self.form_view.edit(key)
        self.fade_to_widget(self.form_view)

    def show_add_prompt_view(self):
        self.animate_to_height(self.WINDOW_H_PROMPT_FORM)
        self.prompt_form_view.edit(None)
        self.fade_to_widget(self.prompt_form_view)

    def show_edit_prompt_view(self, prompt):
        self.animate_to_height(self.WINDOW_H_PROMPT_FORM)
        self.prompt_form_view.edit(prompt)
        self.fade_to_widget(self.prompt_form_view)

    def show_add_ai_model_view(self):
        self.animate_to_height(self.WINDOW_H_AI_MODEL_FORM)
        self.ai_model_form_view.edit(None)
        self.fade_to_widget(self.ai_model_form_view)

    def show_edit_ai_model_view(self, model):
        self.animate_to_height(self.WINDOW_H_AI_MODEL_FORM)
        self.ai_model_form_view.edit(model)
        self.fade_to_widget(self.ai_model_form_view)

    def show_add_link_view(self):
        self.update_size_for_count(3, is_prompt=False)
        self.link_form_view.edit(None)
        self.fade_to_widget(self.link_form_view)

    def show_edit_link_view(self, link):
        self.update_size_for_count(3, is_prompt=False)
        self.link_form_view.edit(link)
        self.fade_to_widget(self.link_form_view)

    def show_add_command_view(self):
        self.update_size_for_count(3, is_prompt=False)
        self.command_form_view.edit(None)
        self.fade_to_widget(self.command_form_view)

    def show_edit_command_view(self, cmd_item):
        self.update_size_for_count(3, is_prompt=False)
        self.command_form_view.edit(cmd_item)
        self.fade_to_widget(self.command_form_view)

    def show_settings_view(self):
        self.animate_to_height(self.WINDOW_H_SETTINGS)
        self.fade_to_widget(self.settings_view)

    def show_welcome_view(self, animate: bool = True):
        self.setFixedSize(self.WINDOW_W, self.WINDOW_H_WELCOME)
        if animate:
            self.fade_to_widget(self.welcome_view)
        else:
            self.stack.setCurrentWidget(self.welcome_view)

    def on_welcome_get_started(self):
        self.settings["welcome_seen"] = True
        self.save_settings()
        all_available = ["key-round", "prompt", "ai_model", "link", "command"]
        initial_mod = self.settings.get("startup_module", "key-round")
        enabled = self.settings.get("enabled_sections", all_available)
        if initial_mod not in enabled:
            order = self.settings.get("section_order", all_available)
            valid = [k for k in order if k in enabled]
            initial_mod = valid[0] if valid else "key-round"
        self.list_view.select_tab(initial_mod, animate=False)
        self.show_list_view(animate=True)

    def _on_escape(self):
        # 1. Close animated search if active
        if self.stack.currentWidget() == self.list_view and getattr(self.list_view, "_search_open", False):
            self.list_view.close_search()
            return

        # 2. Return to list view from form views / settings (anything except list + welcome)
        current = self.stack.currentWidget()
        if current is not self.list_view and current is not self._welcome_view:
            self.show_list_view()

    def reload_data(self) -> bool:
        """Re-read every dataset from disk (used after restoring a backup or importing)."""
        try:
            datasets = self.data_manager.load_all()
        except DataError as exc:
            QMessageBox.critical(self, "DizoClip", f"Could not reload your data:\n\n{exc}")
            return False
        self.settings = datasets["settings"]
        self.keys = datasets["keys"]
        self.prompts = datasets["prompts"]
        self.ai_models = datasets["ai_models"]
        self.links = datasets["links"]
        self.commands = datasets["commands"]
        self.custom_colors = datasets["custom_colors"]
        self.list_view.refresh_nav_tabs()
        if self._settings_view is not None:
            self._settings_view.refresh_nav_tabs()
        self.show_list_view()
        return True

    def _persist(self, name: str, data) -> bool:
        """Save one dataset. Never fails silently: log it and tell the user."""
        try:
            self.data_manager.save(name, data)
            return True
        except DataError as exc:
            log.exception("Saving %s failed", name)
            QMessageBox.critical(
                self,
                "DizoClip: could not save",
                f"Your latest changes to {name.replace('_', ' ')} were NOT saved.\n\n{exc}",
            )
            return False

    def save_keys(self):
        return self._persist("keys", self.keys)

    def save_prompts(self):
        return self._persist("prompts", self.prompts)

    def save_ai_models(self):
        return self._persist("ai_models", self.ai_models)

    def save_links(self):
        return self._persist("links", self.links)

    def save_commands(self):
        return self._persist("commands", self.commands)

    def save_settings(self):
        return self._persist("settings", self.settings)

    # ------------------------------------------------------------------ copy
    def _copy_text(self, text: str, btn=None, sensitive: bool = False) -> None:
        if sensitive and self.settings.get("auto_clear_clipboard", False):
            self.clipboard_guard.copy_sensitive(text, CLIPBOARD_CLEAR_SECONDS)
        else:
            QGuiApplication.clipboard().setText(text)
        if btn is not None:
            self._flash_copied(btn)

    def _flash_copied(self, btn) -> None:
        check = self.icons.get("check")
        if check is not None:
            btn.setText("")
            btn.setIcon(check)
        else:
            btn.setText("✓")
        QTimer.singleShot(1200, lambda: self._restore_copy_btn(btn))

    def _restore_copy_btn(self, btn):
        try:
            if btn is None:
                return
            copy_ic = self.icons.get("copy")
            if copy_ic is not None:
                btn.setIcon(copy_ic)
                btn.setText("")
            else:
                btn.setText("⧉")
        except RuntimeError:
            pass

    def _is_locked(self, item) -> bool:
        """Items encrypted for another Windows account cannot be copied here."""
        if isinstance(item, dict) and item.get("_decrypt_failed"):
            QMessageBox.warning(
                self,
                "DizoClip",
                "This item is encrypted for a different Windows account, so it can't be copied here.\n\n"
                "Open Edit and enter it again to replace it.",
            )
            return True
        return False

    def copy_key(self, key, btn=None):
        if self._is_locked(key):
            return
        secret = key.get("full_key", "")
        if not secret or looks_masked(secret):
            QMessageBox.warning(
                self,
                "DizoClip",
                "This key has no usable secret stored, so nothing was copied.\n\n"
                "Open Edit and enter the key again.",
            )
            return
        self._copy_text(secret, btn, sensitive=True)

    def copy_prompt(self, prompt, btn=None):
        if self._is_locked(prompt):
            return
        self._copy_text(prompt.get("prompt") or prompt.get("content", ""), btn)

    def copy_ai_model(self, text_or_model, btn=None):
        if self._is_locked(text_or_model):
            return
        if isinstance(text_or_model, dict):
            snippets = text_or_model.get("snippets", {})
            text = next(iter(snippets.values())) if snippets else ""
        else:
            text = str(text_or_model)
        self._copy_text(text, btn)

    def copy_link(self, link, btn=None):
        self._copy_text(link.get("url", ""), btn)

    def copy_command(self, cmd_item, btn=None):
        if self._is_locked(cmd_item):
            return
        self._copy_text(cmd_item.get("command", ""), btn)

    def open_link(self, link):
        url = link.get("url", "").strip()
        if url:
            from PySide6.QtCore import QUrl
            from PySide6.QtGui import QDesktopServices
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            QDesktopServices.openUrl(QUrl(url))

    # ---------------------------------------------------------------- delete
    def _confirm_delete(self, items: list, item, label: str, save) -> None:
        if self.settings.get("confirm_delete", True):
            dlg = ConfirmDeleteDialog(self, label, self.icons.get("trash_danger"))
            center = self.frameGeometry().center()
            dlg.move(center.x() - dlg.width() // 2, center.y() - dlg.height() // 2)
            if dlg.exec() != QDialog.Accepted:
                return
        if item in items:
            items.remove(item)
            save()
            self.show_list_view()

    def confirm_delete_key(self, key):
        self._confirm_delete(self.keys, key, key.get("label", "Key"), self.save_keys)

    def confirm_delete_prompt(self, prompt):
        label = prompt.get("name") or prompt.get("title", "Prompt")
        self._confirm_delete(self.prompts, prompt, label, self.save_prompts)

    def confirm_delete_ai_model(self, model):
        self._confirm_delete(self.ai_models, model, model.get("name", "AI Model"), self.save_ai_models)

    def confirm_delete_link(self, link):
        self._confirm_delete(self.links, link, link.get("title", "Link"), self.save_links)

    def confirm_delete_command(self, cmd_item):
        self._confirm_delete(self.commands, cmd_item, cmd_item.get("title", "Command"), self.save_commands)

    # ------------------------------------------------------------ export / import
    def _dataset_lists(self) -> dict:
        return {name: getattr(self, name) for name in EXPORT_DATASETS}

    def export_selected(self, path: str, selection: dict, *, passphrase: str | None = None) -> ExportStats:
        """Export only the chosen records, encrypted. Raises ExportError / OSError."""
        return export_to_file(path, selection, passphrase=passphrase)

    def export_data(self, path: str, passphrase: str) -> None:
        """Export everything, encrypted (the original one-call API)."""
        self.export_selected(path, self._dataset_lists(), passphrase=passphrase)

    def plan_import(self, payload: dict) -> ImportPlan:
        """Compare an export with the current data. Changes nothing."""
        return plan_import(self._dataset_lists(), payload)

    def import_selected(self, plan: ImportPlan, chosen=None) -> dict:
        """
        Add the chosen items (chosen=None means every NEW item). Returns {dataset: number_added}.
        Disk first, memory second: if saving fails nothing in memory changes, and the
        screen never shows items that are not stored.
        save() backs up each file first, so an import can always be undone from Settings > Restore.
        """
        new_lists, added = apply_plan(plan, self._dataset_lists(), chosen)
        if sum(added.values()):
            try:
                self.data_manager.save_all({n: new_lists[n] for n, c in added.items() if c})
            except DataError:
                log.exception("Import could not be saved")
                self.reload_data()  # make the screen match what is really on disk
                raise
            for name, count in added.items():
                if count:
                    getattr(self, name)[:] = new_lists[name]  # in place: other views keep their reference
            self.show_list_view()
        return added

    def import_data(self, path: str, passphrase: str | None = None) -> dict:
        """Merge an export file (either format) into the current data. Returns {dataset: number_added}."""
        payload = read_bundle(Path(path).read_bytes(), passphrase)  # raises ExportError
        return self.import_selected(self.plan_import(payload))

    def rewrite_all_datasets(self) -> None:
        """Re-save prompts, commands and AI models (used when the encryption setting changes)."""
        try:
            self.data_manager.save_all(
                {"prompts": self.prompts, "commands": self.commands, "ai_models": self.ai_models},
                force=True,
            )
        except DataError as exc:
            log.exception("Rewriting data after encryption change failed")
            QMessageBox.critical(self, "DizoClip", f"Could not update your data files:\n\n{exc}")

    def apply_always_on_top(self, enable: bool):
        toggle_always_on_top(self, enable)

