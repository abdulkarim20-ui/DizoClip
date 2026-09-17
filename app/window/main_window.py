import os
import sys

from PySide6.QtCore import (
    QEasingCurve,
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
    QStackedWidget,
)

from app.components.dialogs.confirm_delete import ConfirmDeleteDialog
from app.config.constants import (
    WINDOW_H_AI_MODEL_FORM,
    WINDOW_H_EMPTY,
    WINDOW_H_KEYS_3,
    WINDOW_H_PROMPT_FORM,
    WINDOW_H_SETTINGS,
    WINDOW_W,
)
from app.config.paths import ASSETS_DIR
from app.config.theme import BG_MAIN, TEXT_MAIN
from app.core.clipboard import copy_to_clipboard
from app.core.icons import IconManager
from app.core.data_manager import DataError, DataManager
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


class MainWindow(QMainWindow):
    WINDOW_W = WINDOW_W
    WINDOW_H_EMPTY = WINDOW_H_EMPTY
    WINDOW_H_SETTINGS = WINDOW_H_SETTINGS
    WINDOW_H_WELCOME = 328
    WINDOW_H_KEYS_3 = 405
    WINDOW_H_PROMPTS_3 = 423
    WINDOW_H_PROMPT_FORM = WINDOW_H_PROMPT_FORM
    WINDOW_H_AI_MODEL_FORM = WINDOW_H_AI_MODEL_FORM

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DizoClip")
        self.setFixedSize(self.WINDOW_W, self.WINDOW_H_KEYS_3)

        self._resize_anim = None

        self.data_manager = DataManager()
        try:
            datasets = self.data_manager.load_all()
        except DataError as exc:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(
                self,
                "DizoClip Data Recovery",
                f"DizoClip could not safely read your data.\n\n"
                f"{exc}\n\n"
                f"Your existing files were not replaced."
            )
            raise

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

        self.stack = QStackedWidget()
        self.stack.setAutoFillBackground(True)
        stack_pal = self.stack.palette()
        stack_pal.setColor(self.stack.backgroundRole(), QColor(BG_MAIN))
        self.stack.setPalette(stack_pal)
        self.stack.setStyleSheet(f"QStackedWidget {{ background-color: {BG_MAIN}; }}")

        self.list_view = ListView(self)
        self.form_view = FormView(self)
        self.prompt_form_view = PromptFormView(self)
        self.ai_model_form_view = AIModelFormView(self)
        self.link_form_view = LinkFormView(self)
        self.command_form_view = CommandFormView(self)
        self.settings_view = SettingsView(self)
        self.welcome_view = WelcomeView(self)

        self.stack.addWidget(self.list_view)
        self.stack.addWidget(self.form_view)
        self.stack.addWidget(self.prompt_form_view)
        self.stack.addWidget(self.ai_model_form_view)
        self.stack.addWidget(self.link_form_view)
        self.stack.addWidget(self.command_form_view)
        self.stack.addWidget(self.settings_view)
        self.stack.addWidget(self.welcome_view)
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

    def _setup_titlebar_color(self):
        """
        Prepare the native Windows titlebar and DWM appearance.

        This is intentionally called before the first show().
        """
        from app.config.theme import BG_MAIN, TEXT_MAIN

        prepare_window_for_native_transition(
            self,
            BG_MAIN,
            TEXT_MAIN,
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

    def closeEvent(self, event: QCloseEvent):
        """Handle window close with fade-out animation."""
        event.ignore()  # Don't close immediately

        # Save settings
        if hasattr(self, 'save_settings'):
            try:
                self.save_settings()
            except Exception:
                pass

        # Animate close then quit
        def on_close_finished():
            from PySide6.QtWidgets import QApplication
            QApplication.quit()

        from app.core.window_transition import hide_window_with_animation
        hide_window_with_animation(
            self,
            duration=200,
            on_finished=on_close_finished
        )

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

        # 2. Return to list view from form views
        if self.stack.currentWidget() in (
            self.form_view, self.prompt_form_view, self.ai_model_form_view,
            self.link_form_view, self.command_form_view,
            self.settings_view
        ):
            self.show_list_view()

    def save_keys(self):
        self.data_manager.save("keys", self.keys)

    def save_prompts(self):
        self.data_manager.save("prompts", self.prompts)

    def save_ai_models(self):
        self.data_manager.save("ai_models", self.ai_models)

    def save_links(self):
        self.data_manager.save("links", self.links)

    def save_commands(self):
        self.data_manager.save("commands", self.commands)

    def save_settings(self):
        self.data_manager.save("settings", self.settings)

    def copy_key(self, key, btn=None):
        val_to_copy = key.get("full_key", key["masked"])
        QGuiApplication.clipboard().setText(val_to_copy)
        if btn is None:
            return
        check = self.icons.get("check")
        if check is not None:
            btn.setText("")
            btn.setIcon(check)
        else:
            btn.setText("✓")
        QTimer.singleShot(1200, lambda: self._restore_copy_btn(btn))

    def copy_prompt(self, prompt, btn=None):
        val_to_copy = prompt.get("prompt") or prompt.get("content", "")
        QGuiApplication.clipboard().setText(val_to_copy)
        if btn is None:
            return
        check = self.icons.get("check")
        if check is not None:
            btn.setText("")
            btn.setIcon(check)
        else:
            btn.setText("✓")
        QTimer.singleShot(1200, lambda: self._restore_copy_btn(btn))

    def copy_ai_model(self, text_or_model, btn=None):
        if isinstance(text_or_model, dict):
            snippets = text_or_model.get("snippets", {})
            val_to_copy = next(iter(snippets.values())) if snippets else ""
        else:
            val_to_copy = str(text_or_model)
        QGuiApplication.clipboard().setText(val_to_copy)
        if btn is None:
            return
        check = self.icons.get("check")
        if check is not None:
            btn.setText("")
            btn.setIcon(check)
        else:
            btn.setText("✓")
        QTimer.singleShot(1200, lambda: self._restore_copy_btn(btn))

    def copy_link(self, link, btn=None):
        val = link.get("url", "")
        QGuiApplication.clipboard().setText(val)
        if btn is None:
            return
        check = self.icons.get("check")
        if check is not None:
            btn.setText("")
            btn.setIcon(check)
        else:
            btn.setText("✓")
        QTimer.singleShot(1200, lambda: self._restore_copy_btn(btn))

    def copy_command(self, cmd_item, btn=None):
        val = cmd_item.get("command", "")
        QGuiApplication.clipboard().setText(val)
        if btn is None:
            return
        check = self.icons.get("check")
        if check is not None:
            btn.setText("")
            btn.setIcon(check)
        else:
            btn.setText("✓")
        QTimer.singleShot(1200, lambda: self._restore_copy_btn(btn))

    def open_link(self, link):
        url = link.get("url", "").strip()
        if url:
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            QDesktopServices.openUrl(QUrl(url))

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

    def confirm_delete_key(self, key):
        if not self.settings.get("confirm_delete", True):
            if key in self.keys:
                self.keys.remove(key)
                self.save_keys()
                self.show_list_view()
            return
        dlg = ConfirmDeleteDialog(self, key.get("label", "Key"), self.icons.get("trash_danger"))
        center = self.frameGeometry().center()
        dlg.move(center.x() - dlg.width() // 2, center.y() - dlg.height() // 2)
        if dlg.exec() == QDialog.Accepted:
            if key in self.keys:
                self.keys.remove(key)
                self.save_keys()
                self.show_list_view()

    def confirm_delete_prompt(self, prompt):
        if not self.settings.get("confirm_delete", True):
            if prompt in self.prompts:
                self.prompts.remove(prompt)
                self.save_prompts()
                self.show_list_view()
            return
        label = prompt.get("name") or prompt.get("title", "Prompt")
        dlg = ConfirmDeleteDialog(self, label, self.icons.get("trash_danger"))
        center = self.frameGeometry().center()
        dlg.move(center.x() - dlg.width() // 2, center.y() - dlg.height() // 2)
        if dlg.exec() == QDialog.Accepted:
            if prompt in self.prompts:
                self.prompts.remove(prompt)
                self.save_prompts()
                self.show_list_view()

    def confirm_delete_ai_model(self, model):
        if not self.settings.get("confirm_delete", True):
            if model in self.ai_models:
                self.ai_models.remove(model)
                self.save_ai_models()
                self.show_list_view()
            return
        label = model.get("name", "AI Model")
        dlg = ConfirmDeleteDialog(self, label, self.icons.get("trash_danger"))
        center = self.frameGeometry().center()
        dlg.move(center.x() - dlg.width() // 2, center.y() - dlg.height() // 2)
        if dlg.exec() == QDialog.Accepted:
            if model in self.ai_models:
                self.ai_models.remove(model)
                self.save_ai_models()
                self.show_list_view()

    def confirm_delete_link(self, link):
        if not self.settings.get("confirm_delete", True):
            if link in self.links:
                self.links.remove(link)
                self.save_links()
                self.show_list_view()
            return
        label = link.get("title", "Link")
        dlg = ConfirmDeleteDialog(self, label, self.icons.get("trash_danger"))
        center = self.frameGeometry().center()
        dlg.move(center.x() - dlg.width() // 2, center.y() - dlg.height() // 2)
        if dlg.exec() == QDialog.Accepted:
            if link in self.links:
                self.links.remove(link)
                self.save_links()
                self.show_list_view()

    def confirm_delete_command(self, cmd_item):
        if not self.settings.get("confirm_delete", True):
            if cmd_item in self.commands:
                self.commands.remove(cmd_item)
                self.save_commands()
                self.show_list_view()
            return
        label = cmd_item.get("title", "Command")
        dlg = ConfirmDeleteDialog(self, label, self.icons.get("trash_danger"))
        center = self.frameGeometry().center()
        dlg.move(center.x() - dlg.width() // 2, center.y() - dlg.height() // 2)
        if dlg.exec() == QDialog.Accepted:
            if cmd_item in self.commands:
                self.commands.remove(cmd_item)
                self.save_commands()
                self.show_list_view()

    def apply_always_on_top(self, enable: bool):
        toggle_always_on_top(self, enable)
